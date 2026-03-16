from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("academic_information", "0001_initial"),
        ("academic_procedures", "0014_assignment_coursereplacementrequest_stipendrequest"),
        ("globals", "0005_moduleaccess_database"),
        ("programme_curriculum", "0009_auto_20250503_1355"),
        ("examination", "0002_resultannouncement"),
    ]

    operations = [
        migrations.DeleteModel(name="ResultAnnouncement"),
        migrations.DeleteModel(name="authentication"),
        migrations.DeleteModel(name="grade"),
        migrations.DeleteModel(name="hidden_grades"),
        migrations.CreateModel(
            name="ExamCourseRegistration",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("academic_year", models.CharField(max_length=9)),
                ("status", models.CharField(choices=[("registered", "Registered"), ("dropped", "Dropped"), ("withdrawn", "Withdrawn")], default="registered", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_registrations", to="programme_curriculum.Course")),
                ("semester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_course_registrations", to="programme_curriculum.Semester")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_course_registrations", to="academic_information.Student")),
            ],
            options={"ordering": ("student__id__id",), "unique_together": {("student", "course", "semester", "academic_year")}},
        ),
        migrations.CreateModel(
            name="ExaminationAnnouncement",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150)),
                ("message", models.TextField()),
                ("audience", models.CharField(default="all", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="exam_announcements", to="globals.ExtraInfo")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="GradeComponent",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("component_name", models.CharField(max_length=100)),
                ("max_marks", models.DecimalField(decimal_places=2, max_digits=6)),
                ("weightage", models.DecimalField(decimal_places=2, max_digits=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grade_components", to="programme_curriculum.Course")),
            ],
            options={"ordering": ("course", "component_name"), "unique_together": {("course", "component_name")}},
        ),
        migrations.CreateModel(
            name="ResultPublication",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("academic_year", models.CharField(max_length=9)),
                ("is_published", models.BooleanField(default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="result_publications", to="programme_curriculum.Batch")),
                ("published_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="published_results", to="globals.ExtraInfo")),
                ("semester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="result_publications", to="programme_curriculum.Semester")),
            ],
            options={"ordering": ("-published_at", "batch__year"), "unique_together": {("batch", "semester", "academic_year")}},
        ),
    ]
