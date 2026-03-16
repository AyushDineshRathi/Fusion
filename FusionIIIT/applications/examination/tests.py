from django.contrib.auth.models import User
from django.test import TestCase

from applications.academic_information.models import Student
from applications.globals.models import DepartmentInfo, ExtraInfo, Faculty
from applications.programme_curriculum.models import Batch, Course, CourseInstructor, Curriculum, Discipline, Programme, Semester

from .models import StudentFinalGrade
from .services import submit_grades_service, verify_grades_service


class ExaminationServiceTests(TestCase):
    def setUp(self):
        department = DepartmentInfo.objects.create(name="CSE-Test")
        faculty_user = User.objects.create_user(username="faculty1", password="pass")
        student_user = User.objects.create_user(username="20BCS001", password="pass")
        self.faculty_extra = ExtraInfo.objects.create(
            id="EMP001",
            user=faculty_user,
            user_type="faculty",
            department=department,
        )
        self.student_extra = ExtraInfo.objects.create(
            id="20BCS001",
            user=student_user,
            user_type="student",
            department=department,
        )
        self.faculty = Faculty.objects.create(id=self.faculty_extra)
        programme = Programme.objects.create(category="UG", name="BTech Test")
        discipline = Discipline.objects.create(name="Computer Science Test", acronym="CST")
        discipline.programmes.add(programme)
        curriculum = Curriculum.objects.create(programme=programme, name="Curriculum Test", no_of_semester=8)
        self.batch = Batch.objects.create(name="B.Tech", discipline=discipline, year=2020, curriculum=curriculum)
        self.student = Student.objects.create(
            id=self.student_extra,
            programme="B.Tech",
            batch=2020,
            batch_id=self.batch,
            category="GEN",
            curr_semester_no=5,
        )
        self.semester = Semester.objects.create(curriculum=curriculum, semester_no=5)
        self.course = Course.objects.create(
            code="CSE501",
            name="Software Architecture",
            credit=4,
            lecture_hours=3,
            tutorial_hours=1,
            pratical_hours=0,
            discussion_hours=0,
            project_hours=0,
            syllabus="Test syllabus",
            ref_books="Test references",
        )
        CourseInstructor.objects.create(course_id=self.course, instructor_id=self.faculty, year=2025, semester_type="Odd Semester")

    def test_submit_grades_service_creates_unverified_grade(self):
        submit_grades_service(
            self.faculty_extra.user,
            self.course.id,
            self.semester.id,
            "2025-26",
            [{"student_id": self.student.id_id, "letter_grade": "A", "components": []}],
        )
        grade = StudentFinalGrade.objects.get(student=self.student, course=self.course)
        self.assertEqual(grade.letter_grade, "A")
        self.assertFalse(grade.is_verified)

    def test_verify_grades_service_marks_grade_verified(self):
        submit_grades_service(
            self.faculty_extra.user,
            self.course.id,
            self.semester.id,
            "2025-26",
            [{"student_id": self.student.id_id, "letter_grade": "B+", "components": []}],
        )
        verify_grades_service(self.faculty_extra.user, self.course.id, self.semester.id, "2025-26")
        grade = StudentFinalGrade.objects.get(student=self.student, course=self.course)
        self.assertTrue(grade.is_verified)
