from collections import defaultdict

from django.db.models import Count

from .models import (
    ExaminationAnnouncement,
    GradeChangeLog,
    ReevaluationRequest,
    ResultPublication,
    StudentFinalGrade,
)
from .utils import group_results_for_transcript


def get_student_results_selector(student, semester_id=None, academic_year=None, published_only=True):
    queryset = StudentFinalGrade.objects.select_related("course", "semester", "student__id__user").filter(student=student)
    if semester_id:
        queryset = queryset.filter(semester_id=semester_id)
    if academic_year:
        queryset = queryset.filter(academic_year=academic_year)
    rows = []
    for grade in queryset.order_by("semester__semester_no", "course__code"):
        publication = ResultPublication.objects.filter(
            batch=grade.student.batch_id,
            semester=grade.semester,
            academic_year=grade.academic_year,
            is_published=True,
        ).first()
        if published_only and not publication:
            continue
        rows.append(
            {
                "semester_id": grade.semester_id,
                "semester_no": grade.semester.semester_no,
                "academic_year": grade.academic_year,
                "course_id": grade.course_id,
                "course_code": grade.course.code,
                "course_name": grade.course.name,
                "credits": grade.course.credit,
                "letter_grade": grade.letter_grade,
                "grade_points": grade.grade_points,
                "is_verified": grade.is_verified,
            }
        )
    transcript = group_results_for_transcript(rows)
    return {"results": rows, "spi": transcript["spi"], "cpi": transcript["cpi"]}


def get_course_grade_summary_selector(course_id, semester_id, academic_year):
    grades = (
        StudentFinalGrade.objects.select_related("student__id__user", "course", "semester")
        .filter(course_id=course_id, semester_id=semester_id, academic_year=academic_year)
        .order_by("student__id__id")
    )
    return {
        "students": [
            {
                "student_id": grade.student_id_id,
                "roll_no": grade.student.id_id,
                "student_name": grade.student.id.user.get_full_name().strip() or grade.student.id.user.username,
                "letter_grade": grade.letter_grade,
                "grade_points": grade.grade_points,
                "is_verified": grade.is_verified,
            }
            for grade in grades
        ],
        "grade_breakdown": list(
            grades.values("letter_grade").annotate(total=Count("id")).order_by("letter_grade")
        ),
    }


def get_student_semesters_selector(student):
    semester_map = defaultdict(set)
    for grade in StudentFinalGrade.objects.filter(student=student).select_related("semester").order_by("semester__semester_no"):
        semester_map[grade.semester.semester_no].add(grade.academic_year)
    return [
        {"semester_no": semester_no, "academic_years": sorted(list(years))}
        for semester_no, years in sorted(semester_map.items())
    ]


def get_result_publication_status_selector(batch_id, semester_id, academic_year):
    publication = ResultPublication.objects.filter(
        batch_id=batch_id,
        semester_id=semester_id,
        academic_year=academic_year,
    ).select_related("published_by__user").first()
    if not publication:
        return {
            "batch_id": batch_id,
            "semester_id": semester_id,
            "academic_year": academic_year,
            "is_published": False,
            "published_at": None,
            "published_by": None,
        }
    return {
        "batch_id": batch_id,
        "semester_id": semester_id,
        "academic_year": academic_year,
        "is_published": publication.is_published,
        "published_at": publication.published_at,
        "published_by": publication.published_by.user.username if publication.published_by else None,
    }


def get_transcript_selector(student):
    result_payload = get_student_results_selector(student, published_only=True)
    grouped = defaultdict(list)
    for row in result_payload["results"]:
        grouped["Semester {}".format(row["semester_no"])].append(row)
    return {
        "student_id": student.id_id,
        "student_name": student.id.user.get_full_name().strip() or student.id.user.username,
        "semesters": dict(grouped),
        "spi": result_payload["spi"],
        "cpi": result_payload["cpi"],
    }


def get_grade_audit_logs_selector(course_id=None, student_id=None):
    queryset = GradeChangeLog.objects.select_related("student__id__user", "course", "changed_by__user")
    if course_id:
        queryset = queryset.filter(course_id=course_id)
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    return list(
        queryset.values(
            "student__id__id",
            "course__code",
            "old_grade",
            "new_grade",
            "reason",
            "timestamp",
            "changed_by__user__username",
        )
    )


def get_dashboard_snapshot_selector(user):
    student = getattr(getattr(user, "extrainfo", None), "student", None)
    snapshot = {
        "announcements": list(ExaminationAnnouncement.objects.values("id", "title", "message", "audience", "created_at")[:5]),
        "pending_reevaluations": ReevaluationRequest.objects.filter(status__in=["requested", "in_review"]).count(),
    }
    if student:
        snapshot["student_result_summary"] = get_student_results_selector(student, published_only=True)
        snapshot["available_semesters"] = get_student_semesters_selector(student)
    return snapshot
