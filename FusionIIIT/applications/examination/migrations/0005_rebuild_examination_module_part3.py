from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("examination", "0004_rebuild_examination_module_part2")]

    operations = [
        migrations.CreateModel(
            name="GradeChangeLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("old_grade", models.CharField(blank=True, max_length=2)),
                ("new_grade", models.CharField(choices=[("O", "O"), ("A+", "A+"), ("A", "A"), ("B+", "B+"), ("B", "B"), ("C+", "C+"), ("C", "C"), ("D+", "D+"), ("D", "D"), ("F", "F")], max_length=2)),
                ("reason", models.TextField()),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="grade_change_logs", to="globals.ExtraInfo")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grade_change_logs", to="programme_curriculum.Course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="grade_change_logs", to="academic_information.Student")),
            ],
            options={"ordering": ("-timestamp",)},
        ),
        migrations.CreateModel(
            name="StudentComponentMark",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("marks_obtained", models.DecimalField(decimal_places=2, max_digits=6)),
                ("remarks", models.CharField(blank=True, max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("component", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_marks", to="examination.GradeComponent")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_component_marks", to="programme_curriculum.Course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="component_marks", to="academic_information.Student")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_component_marks", to="globals.ExtraInfo")),
            ],
            options={"ordering": ("student__id__id", "component__component_name"), "unique_together": {("student", "course", "component")}},
        ),
    ]
