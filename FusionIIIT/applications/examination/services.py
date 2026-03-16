from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from notifications.signals import notify

from applications.academic_information.models import Student
from applications.academic_procedures.models import course_registration
from applications.programme_curriculum.models import Course, CourseInstructor, Semester

from .models import (
    ExamCourseRegistration,
    ExaminationAnnouncement,
    GradeChangeLog,
    GradeComponent,
    ReevaluationRequest,
    ResultPublication,
    SeatingPlan,
    StudentComponentMark,
    StudentFinalGrade,
)
from .utils import build_csv_preview, distribute_seats, get_grade_points, normalise_grade, parse_grades_csv


def _extra_info_from_user(user):
    return getattr(user, "extrainfo", None)


def _validate_faculty_course_access(user, course):
    if user.is_superuser:
        return
    extra_info = _extra_info_from_user(user)
    if not extra_info:
        raise ValueError("User profile is not configured.")
    if not CourseInstructor.objects.filter(course_id=course, instructor_id__id=extra_info).exists():
        raise ValueError("Faculty member is not assigned to this course.")


def sync_course_registrations_service(course_id, semester_id, academic_year):
    synced = []
    registrations = course_registration.objects.select_related("student_id", "course_id", "semester_id").filter(
        course_id_id=course_id,
        semester_id_id=semester_id,
    )
    for registration in registrations:
        exam_registration, _ = ExamCourseRegistration.objects.update_or_create(
            student=registration.student_id,
            course=registration.course_id,
            semester=registration.semester_id,
            academic_year=academic_year,
            defaults={"status": "registered"},
        )
        synced.append(exam_registration)
    return synced


@transaction.atomic
def submit_grades_service(actor, course_id, semester_id, academic_year, grades):
    course = Course.objects.get(id=course_id)
    semester = Semester.objects.get(id=semester_id)
    _validate_faculty_course_access(actor, course)
    sync_course_registrations_service(course_id, semester_id, academic_year)
    actor_extra = _extra_info_from_user(actor)
    created_or_updated = []
    for item in grades:
        student = Student.objects.select_related("id__user").get(id=item["student_id"])
        ExamCourseRegistration.objects.get_or_create(
            student=student,
            course=course,
            semester=semester,
            academic_year=academic_year,
            defaults={"status": "registered"},
        )
        letter_grade = normalise_grade(item["letter_grade"])
        defaults = {
            "letter_grade": letter_grade,
            "grade_points": get_grade_points(letter_grade),
            "is_verified": False,
            "verified_by": None,
            "verified_at": None,
            "submitted_by": actor_extra,
        }
        final_grade, created = StudentFinalGrade.objects.get_or_create(
            student=student,
            course=course,
            semester=semester,
            academic_year=academic_year,
            defaults=defaults,
        )
        old_grade = ""
        if not created:
            old_grade = final_grade.letter_grade
            for key, value in defaults.items():
                setattr(final_grade, key, value)
            final_grade.save()
        if old_grade != letter_grade:
            GradeChangeLog.objects.create(
                student=student,
                course=course,
                old_grade=old_grade,
                new_grade=letter_grade,
                changed_by=actor_extra,
                reason=item.get("reason") or "Faculty submission",
            )
        for component in item.get("components", []):
            component_obj, _ = GradeComponent.objects.update_or_create(
                course=course,
                component_name=component["component_name"],
                defaults={
                    "max_marks": Decimal(str(component["max_marks"])),
                    "weightage": Decimal(str(component["weightage"])),
                },
            )
            StudentComponentMark.objects.update_or_create(
                student=student,
                course=course,
                component=component_obj,
                defaults={
                    "marks_obtained": Decimal(str(component["marks_obtained"])),
                    "remarks": component.get("remarks", ""),
                    "updated_by": actor_extra,
                },
            )
        created_or_updated.append({"student_id": student.id_id, "grade": letter_grade})
    return created_or_updated


def preview_grades_csv_service(file_obj):
    return build_csv_preview(parse_grades_csv(file_obj))


def upload_grades_csv_service(actor, course_id, semester_id, academic_year, file_obj):
    preview = preview_grades_csv_service(file_obj)
    if preview["errors"]:
        raise ValueError("; ".join(preview["errors"]))
    payload = [
        {
            "student_id": row["roll_no"],
            "letter_grade": row["letter_grade"],
            "reason": row["remarks"] or "Uploaded via CSV",
            "components": [],
        }
        for row in preview["rows"]
    ]
    return submit_grades_service(actor, int(course_id), int(semester_id), academic_year, payload)


@transaction.atomic
def verify_grades_service(actor, course_id, semester_id, academic_year):
    actor_extra = _extra_info_from_user(actor)
    count = StudentFinalGrade.objects.filter(
        course_id=course_id,
        semester_id=semester_id,
        academic_year=academic_year,
    ).update(is_verified=True, verified_by=actor_extra, verified_at=timezone.now())
    return {"verified_records": count}


@transaction.atomic
def publish_results_service(actor, batch_id, semester_id, academic_year):
    actor_extra = _extra_info_from_user(actor)
    publication, _ = ResultPublication.objects.update_or_create(
        batch_id=batch_id,
        semester_id=semester_id,
        academic_year=academic_year,
        defaults={"is_published": True, "published_at": timezone.now(), "published_by": actor_extra},
    )
    registrations = ExamCourseRegistration.objects.select_related("student__id__user").filter(
        semester_id=semester_id,
        academic_year=academic_year,
        student__batch_id_id=batch_id,
    )
    for registration in registrations:
        notify.send(actor, recipient=registration.student.id.user, verb="Results published for semester {}".format(publication.semester.semester_no))
    return publication


@transaction.atomic
def update_grade_service(actor, student_id, course_id, semester_id, academic_year, new_grade, reason):
    actor_extra = _extra_info_from_user(actor)
    final_grade = StudentFinalGrade.objects.select_related("student", "course").get(
        student_id=student_id,
        course_id=course_id,
        semester_id=semester_id,
        academic_year=academic_year,
    )
    old_grade = final_grade.letter_grade
    normalized = normalise_grade(new_grade)
    final_grade.letter_grade = normalized
    final_grade.grade_points = get_grade_points(normalized)
    final_grade.is_verified = False
    final_grade.verified_by = None
    final_grade.verified_at = None
    final_grade.save()
    GradeChangeLog.objects.create(
        student=final_grade.student,
        course=final_grade.course,
        old_grade=old_grade,
        new_grade=normalized,
        changed_by=actor_extra,
        reason=reason,
    )
    return final_grade


def create_announcement_service(actor, title, message, audience):
    return ExaminationAnnouncement.objects.create(
        title=title,
        message=message,
        audience=audience,
        created_by=_extra_info_from_user(actor),
    )


def request_reevaluation_service(actor, course_id, semester_id, academic_year, reason):
    student = Student.objects.get(id=actor.extrainfo)
    request_obj, created = ReevaluationRequest.objects.update_or_create(
        student=student,
        course_id=course_id,
        semester_id=semester_id,
        academic_year=academic_year,
        defaults={"reason": reason, "status": "requested", "resolution_note": "", "reviewed_by": None},
    )
    return {"request_id": request_obj.id, "created": created}


def resolve_reevaluation_service(actor, request_id, status_value, resolution_note):
    request_obj = ReevaluationRequest.objects.get(id=request_id)
    request_obj.status = status_value
    request_obj.resolution_note = resolution_note
    request_obj.reviewed_by = _extra_info_from_user(actor)
    request_obj.save()
    return request_obj


@transaction.atomic
def generate_seating_plan_service(actor, course_id, semester_id, academic_year, exam_name, exam_date, halls):
    course = Course.objects.get(id=course_id)
    semester = Semester.objects.get(id=semester_id)
    students = list(
        ExamCourseRegistration.objects.select_related("student__id__user")
        .filter(course=course, semester=semester, academic_year=academic_year, status="registered")
        .order_by("student__id__id")
        .values("student__id__id", "student__id__user__first_name", "student__id__user__last_name")
    )
    allocations = distribute_seats(students, halls)
    SeatingPlan.objects.filter(course=course, semester=semester, academic_year=academic_year, exam_name=exam_name).delete()
    plan_rows = []
    for allocation in allocations:
        plan_rows.append(
            SeatingPlan.objects.create(
                exam_name=exam_name,
                course=course,
                semester=semester,
                academic_year=academic_year,
                exam_date=exam_date,
                hall_name=allocation["hall_name"],
                hall_capacity=allocation["hall_capacity"],
                seat_start=allocation["seat_start"],
                seat_end=allocation["seat_end"],
                generated_by=_extra_info_from_user(actor),
            )
        )
    return plan_rows


def send_grade_deadline_reminders_service(actor, course_ids, deadline_label):
    reminders = []
    queryset = CourseInstructor.objects.select_related("course_id", "instructor_id__id__user").filter(course_id_id__in=course_ids)
    for assignment in queryset:
        recipient = assignment.instructor_id.id.user
        notify.send(actor, recipient=recipient, verb="Reminder: submit grades for {} before {}".format(assignment.course_id.code, deadline_label))
        reminders.append({"course_code": assignment.course_id.code, "recipient": recipient.username})
    return reminders
