from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("examination", "0003_rebuild_examination_module")]

    operations = [
        migrations.CreateModel(
            name="SeatingPlan",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("exam_name", models.CharField(max_length=150)),
                ("academic_year", models.CharField(max_length=9)),
                ("exam_date", models.DateField()),
                ("hall_name", models.CharField(max_length=100)),
                ("hall_capacity", models.PositiveIntegerField()),
                ("seat_start", models.PositiveIntegerField()),
                ("seat_end", models.PositiveIntegerField()),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seating_plans", to="programme_curriculum.Course")),
                ("generated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="generated_seating_plans", to="globals.ExtraInfo")),
                ("semester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seating_plans", to="programme_curriculum.Semester")),
            ],
            options={"ordering": ("exam_date", "hall_name", "seat_start")},
        ),
        migrations.CreateModel(
            name="StudentFinalGrade",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("academic_year", models.CharField(max_length=9)),
                ("letter_grade", models.CharField(choices=[("O", "O"), ("A+", "A+"), ("A", "A"), ("B+", "B+"), ("B", "B"), ("C+", "C+"), ("C", "C"), ("D+", "D+"), ("D", "D"), ("F", "F")], max_length=2)),
                ("grade_points", models.PositiveIntegerField()),
                ("is_verified", models.BooleanField(default=False)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="final_grades", to="programme_curriculum.Course")),
                ("semester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="final_grades", to="programme_curriculum.Semester")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="final_grades", to="academic_information.Student")),
                ("submitted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="submitted_exam_grades", to="globals.ExtraInfo")),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verified_exam_grades", to="globals.ExtraInfo")),
            ],
            options={"ordering": ("student__id__id", "course__code"), "unique_together": {("student", "course", "semester", "academic_year")}},
        ),
        migrations.CreateModel(
            name="ReevaluationRequest",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("academic_year", models.CharField(max_length=9)),
                ("reason", models.TextField()),
                ("status", models.CharField(choices=[("requested", "Requested"), ("in_review", "In Review"), ("resolved", "Resolved"), ("rejected", "Rejected")], default="requested", max_length=20)),
                ("resolution_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reevaluation_requests", to="programme_curriculum.Course")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_reevaluations", to="globals.ExtraInfo")),
                ("semester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reevaluation_requests", to="programme_curriculum.Semester")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reevaluation_requests", to="academic_information.Student")),
            ],
            options={"ordering": ("-created_at",), "unique_together": {("student", "course", "semester", "academic_year")}},
        ),
    ]
