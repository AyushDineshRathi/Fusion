from rest_framework import serializers

from .models import ExaminationAnnouncement, ReevaluationRequest, SeatingPlan


class GradeComponentInputSerializer(serializers.Serializer):
    component_name = serializers.CharField(max_length=100)
    max_marks = serializers.DecimalField(max_digits=6, decimal_places=2)
    weightage = serializers.DecimalField(max_digits=5, decimal_places=2)
    marks_obtained = serializers.DecimalField(max_digits=6, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True)


class GradeSubmissionItemSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    letter_grade = serializers.CharField(max_length=2)
    reason = serializers.CharField(required=False, allow_blank=True)
    components = GradeComponentInputSerializer(many=True, required=False)


class GradeSubmissionSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)
    grades = GradeSubmissionItemSerializer(many=True)


class VerifyGradesSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)


class PublishResultsSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)


class UpdateGradeSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    course_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)
    new_grade = serializers.CharField(max_length=2)
    reason = serializers.CharField()


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.user.username", read_only=True)

    class Meta:
        model = ExaminationAnnouncement
        fields = ("id", "title", "message", "audience", "created_by", "created_at")


class ReevaluationRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source="student.id_id", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = ReevaluationRequest
        fields = (
            "id",
            "student_id",
            "course",
            "course_code",
            "semester",
            "academic_year",
            "reason",
            "status",
            "resolution_note",
            "created_at",
            "updated_at",
        )


class ReevaluationCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)
    reason = serializers.CharField()


class ReevaluationResolveSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    status_value = serializers.ChoiceField(choices=["in_review", "resolved", "rejected"])
    resolution_note = serializers.CharField(required=False, allow_blank=True)


class SeatingHallSerializer(serializers.Serializer):
    hall_name = serializers.CharField()
    capacity = serializers.IntegerField(min_value=1)


class SeatingPlanCreateSerializer(serializers.Serializer):
    exam_name = serializers.CharField()
    course_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    academic_year = serializers.CharField(max_length=9)
    exam_date = serializers.DateField()
    halls = SeatingHallSerializer(many=True)


class SeatingPlanSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = SeatingPlan
        fields = (
            "id",
            "exam_name",
            "course",
            "course_code",
            "semester",
            "academic_year",
            "exam_date",
            "hall_name",
            "hall_capacity",
            "seat_start",
            "seat_end",
            "generated_at",
        )
