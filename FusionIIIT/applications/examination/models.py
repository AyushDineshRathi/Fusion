from django.db import models
from django.utils import timezone

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.programme_curriculum.models import Batch, Course, Semester


LETTER_GRADE_CHOICES = (
    ("O", "O"),
    ("A+", "A+"),
    ("A", "A"),
    ("B+", "B+"),
    ("B", "B"),
    ("C+", "C+"),
    ("C", "C"),
    ("D+", "D+"),
    ("D", "D"),
    ("F", "F"),
)


class ExamCourseRegistration(models.Model):
    STATUS_CHOICES = (
        ("registered", "Registered"),
        ("dropped", "Dropped"),
        ("withdrawn", "Withdrawn"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exam_course_registrations")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exam_registrations")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="exam_course_registrations")
    academic_year = models.CharField(max_length=9)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="registered")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "course", "semester", "academic_year")
        ordering = ("student__id__id",)

    def __str__(self):
        return "{} - {} - {}".format(self.student_id, self.course.code, self.academic_year)


class GradeComponent(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="grade_components")
    component_name = models.CharField(max_length=100)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2)
    weightage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "component_name")
        ordering = ("course", "component_name")

    def __str__(self):
        return "{} - {}".format(self.course.code, self.component_name)


class StudentComponentMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="component_marks")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="student_component_marks")
    component = models.ForeignKey(GradeComponent, on_delete=models.CASCADE, related_name="student_marks")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_component_marks",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "course", "component")
        ordering = ("student__id__id", "component__component_name")

    def __str__(self):
        return "{} - {} - {}".format(self.student_id, self.course.code, self.component.component_name)


class StudentFinalGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="final_grades")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="final_grades")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="final_grades")
    academic_year = models.CharField(max_length=9)
    letter_grade = models.CharField(max_length=2, choices=LETTER_GRADE_CHOICES)
    grade_points = models.PositiveIntegerField()
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_exam_grades",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_exam_grades",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "course", "semester", "academic_year")
        ordering = ("student__id__id", "course__code")

    def __str__(self):
        return "{} - {} - {}".format(self.student_id, self.course.code, self.letter_grade)


class ResultPublication(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="result_publications")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="result_publications")
    academic_year = models.CharField(max_length=9)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_results",
    )

    class Meta:
        unique_together = ("batch", "semester", "academic_year")
        ordering = ("-published_at", "batch__year")

    def __str__(self):
        return "{} - sem {} - {}".format(self.batch, self.semester.semester_no, self.academic_year)


class GradeChangeLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grade_change_logs")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="grade_change_logs")
    old_grade = models.CharField(max_length=2, blank=True)
    new_grade = models.CharField(max_length=2, choices=LETTER_GRADE_CHOICES)
    changed_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grade_change_logs",
    )
    reason = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return "{} - {} - {} -> {}".format(self.student_id, self.course.code, self.old_grade, self.new_grade)


class ReevaluationRequest(models.Model):
    STATUS_CHOICES = (
        ("requested", "Requested"),
        ("in_review", "In Review"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="reevaluation_requests")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reevaluation_requests")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="reevaluation_requests")
    academic_year = models.CharField(max_length=9)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    resolution_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reevaluations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "course", "semester", "academic_year")
        ordering = ("-created_at",)


class ExaminationAnnouncement(models.Model):
    title = models.CharField(max_length=150)
    message = models.TextField()
    audience = models.CharField(max_length=50, default="all")
    created_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exam_announcements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class SeatingPlan(models.Model):
    exam_name = models.CharField(max_length=150)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="seating_plans")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="seating_plans")
    academic_year = models.CharField(max_length=9)
    exam_date = models.DateField()
    hall_name = models.CharField(max_length=100)
    hall_capacity = models.PositiveIntegerField()
    seat_start = models.PositiveIntegerField()
    seat_end = models.PositiveIntegerField()
    generated_by = models.ForeignKey(
        ExtraInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_seating_plans",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("exam_date", "hall_name", "seat_start")
