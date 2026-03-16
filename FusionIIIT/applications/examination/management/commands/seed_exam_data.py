import json
import os
import random
from decimal import Decimal
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from applications.globals.models import ExtraInfo, DepartmentInfo, Designation, Faculty, HoldsDesignation, ModuleAccess
from applications.academic_information.models import Student
from applications.programme_curriculum.models import Course, Semester, Batch, Curriculum, Discipline, Programme, CourseInstructor
from applications.examination.models import (
    ExamCourseRegistration, GradeComponent, StudentComponentMark,
    StudentFinalGrade, ResultPublication, SeatingPlan
)
from applications.academic_procedures.models import course_registration

class Command(BaseCommand):
    help = 'Seeds database with examination module test data (B.Tech 2023)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seeding...")
        
        # 1. Setup departments, disciplines, and basics
        dept, _ = DepartmentInfo.objects.get_or_create(name="Computer Science and Engineering")
        disc, _ = Discipline.objects.get_or_create(name="Computer Science and Engineering", acronym="CSE")
        
        programme, _ = Programme.objects.get_or_create(name="B.Tech", defaults={"category": "UG"})
        disc.programmes.add(programme)
        
        # 1.5 Setup Designations and ModuleAccess
        des_student, _ = Designation.objects.get_or_create(name="student", defaults={"full_name": "Student", "type": "academic"})
        des_faculty, _ = Designation.objects.get_or_create(name="Assistant Professor", defaults={"full_name": "Faculty", "type": "academic"})
        des_admin, _ = Designation.objects.get_or_create(name="acadadmin", defaults={"full_name": "Academic Admin", "type": "administrative"})
        des_dean, _ = Designation.objects.get_or_create(name="Dean Academic", defaults={"full_name": "Dean Academic", "type": "administrative"})
        
        ModuleAccess.objects.get_or_create(designation="student", defaults={"examinations": True, "course_registration": True, "phc": True, "complaint_management": True})
        ModuleAccess.objects.get_or_create(designation="Assistant Professor", defaults={"examinations": True, "course_management": True, "department": True})
        ModuleAccess.objects.get_or_create(designation="acadadmin", defaults={"examinations": True, "program_and_curriculum": True, "other_academics": True})
        ModuleAccess.objects.get_or_create(designation="Dean Academic", defaults={"examinations": True, "program_and_curriculum": True})
        
        # 2. Curriculums and batches
        curriculum, _ = Curriculum.objects.get_or_create(
            name="B.Tech CSE 2023",
            programme=programme,
            defaults={"version": 1.0, "no_of_semester": 8}
        )
        
        batch, _ = Batch.objects.get_or_create(
            name="B.Tech",
            discipline=disc,
            year=2023,
            defaults={"curriculum": curriculum}
        )
        
        semester, _ = Semester.objects.get_or_create(
            curriculum=curriculum,
            semester_no=1,
            defaults={"instigate_semester": True}
        )

        academic_year = "2023-24"
        
        # 3. Load Student Data
        seed_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(seed_dir, "seed_data", "btech_2023_students.json")
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Dataset not found at {json_path}. Run Phase 2 script first."))
            return
            
        with open(json_path, 'r') as f:
            student_data = json.load(f)
            
        students_created = 0
        student_objs = []
        for s in student_data:
            roll_no = s["roll_no"].lower()
            name = s["name"]
            
            user, created = User.objects.get_or_create(username=roll_no, defaults={
                "email": f"{roll_no}@iiitdmj.ac.in",
                "first_name": name.split()[0],
                "last_name": " ".join(name.split()[1:])
            })
            if created:
                user.set_password('student123')
                user.save()
            
            extrainfo, _ = ExtraInfo.objects.get_or_create(
                user=user,
                defaults={"user_type": "student", "department": dept, "id": roll_no}
            )
            HoldsDesignation.objects.get_or_create(user=user, working=user, designation=des_student)
            
            student, created = Student.objects.get_or_create(
                id=extrainfo,
                defaults={"programme": "B.Tech", "batch": 2023, "batch_id": batch, "curr_semester_no": 1}
            )
            
            if created:
                students_created += 1
                
            student_objs.append(student)
            
        self.stdout.write(self.style.SUCCESS(f"Students created/verified: {students_created} / {len(student_data)}"))
        
        # 4. Faculty
        faculty_names = ["Dr Rajesh Sharma", "Dr Anita Verma", "Dr Vivek Mishra", "Dr Pooja Gupta", "Dr Sandeep Kulkarni"]
        faculty_objs = []
        for i, fname in enumerate(faculty_names):
            username = f"faculty{i+1}"
            user, created = User.objects.get_or_create(username=username, defaults={
                "email": f"{username}@iiitdmj.ac.in",
                "first_name": fname.split(' ', 1)[0],
                "last_name": fname.split(' ', 1)[1] if len(fname.split(' ')) > 1 else ""
            })
            if created:
                user.set_password('faculty123')
                user.save()
            extrainfo, _ = ExtraInfo.objects.get_or_create(
                user=user, defaults={"user_type": "faculty", "department": dept, "id": username}
            )
            HoldsDesignation.objects.get_or_create(user=user, working=user, designation=des_faculty)
            faculty, _ = Faculty.objects.get_or_create(id=extrainfo)
            faculty_objs.append(faculty)
            
        self.stdout.write(self.style.SUCCESS(f"Faculty created: {len(faculty_objs)}"))
        
        # 4.5 Admin & Dean
        admin_user, _ = User.objects.get_or_create(username="acadadmin", defaults={"first_name": "Academic", "last_name": "Admin", "email": "acadadmin@iiitdmj.ac.in"})
        admin_user.set_password("admin123")
        admin_user.save()
        extrainfo, _ = ExtraInfo.objects.get_or_create(user=admin_user, defaults={"user_type": "staff", "department": dept, "id": "acadadmin"})
        HoldsDesignation.objects.get_or_create(user=admin_user, working=admin_user, designation=des_admin)
        
        dean_user, _ = User.objects.get_or_create(username="dean_academic", defaults={"first_name": "Dean", "last_name": "Academic", "email": "dean@iiitdmj.ac.in"})
        dean_user.set_password("dean123")
        dean_user.save()
        extrainfo, _ = ExtraInfo.objects.get_or_create(user=dean_user, defaults={"user_type": "faculty", "department": dept, "id": "dean_academic"})
        HoldsDesignation.objects.get_or_create(user=dean_user, working=dean_user, designation=des_dean)
        
        # 5. Courses
        course_data = [
            ("CS101", "Programming Fundamentals"),
            ("CS102", "Data Structures"),
            ("CS103", "Discrete Mathematics"),
            ("EC101", "Basic Electronics"),
            ("ME101", "Engineering Mechanics"),
            ("SM101", "Mathematics I")
        ]
        
        courses = []
        for code, name in course_data:
            course, _ = Course.objects.get_or_create(
                code=code,
                defaults={"name": name, "credit": 4, "version": 1.0}
            )
            courses.append(course)
            
        self.stdout.write(self.style.SUCCESS(f"Courses created: {len(courses)}"))
        
        # 5.5 Assign instructors
        for idx, course in enumerate(courses):
            faculty = faculty_objs[idx % len(faculty_objs)]
            CourseInstructor.objects.get_or_create(
                course_id=course,
                instructor_id=faculty,
                year=2023,
                semester_type="Odd Semester"
            )
        self.stdout.write(self.style.SUCCESS("Instructors assigned to courses"))
        
        # 6. Registrations
        target_courses = [c for c in courses if c.code in ('CS101', 'SM101', 'EC101')]
        
        reg_count = 0
        for student in student_objs:
            for course in target_courses:
                # Legacy registration
                course_registration.objects.get_or_create(
                    student_id=student,
                    semester_id=semester,
                    course_id=course,
                    defaults={"registration_type": "Regular"}
                )
                
                # New Examination Registration
                ExamCourseRegistration.objects.get_or_create(
                    student=student,
                    course=course,
                    semester=semester,
                    academic_year=academic_year,
                    defaults={"status": "registered"}
                )
                reg_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Registrations created: {reg_count}"))
        
        # 7. Grades
        grades_pool = [("O", 10), ("A+", 10), ("A", 9), ("B+", 8), ("B", 7), ("C+", 6), ("C", 5), ("D+", 4), ("D", 4)]
        
        for course in target_courses:
            comp_m, _ = GradeComponent.objects.get_or_create(course=course, component_name="Midterm", defaults={"max_marks": 30, "weightage": 30})
            comp_e, _ = GradeComponent.objects.get_or_create(course=course, component_name="Endterm", defaults={"max_marks": 50, "weightage": 50})
            comp_a, _ = GradeComponent.objects.get_or_create(course=course, component_name="Assignment", defaults={"max_marks": 20, "weightage": 20})
            
            for student in student_objs:
                mid_marks = random.randint(10, 30)
                end_marks = random.randint(15, 50)
                ass_marks = random.randint(10, 20)
                
                StudentComponentMark.objects.update_or_create(student=student, course=course, component=comp_m, defaults={"marks_obtained": mid_marks})
                StudentComponentMark.objects.update_or_create(student=student, course=course, component=comp_e, defaults={"marks_obtained": end_marks})
                StudentComponentMark.objects.update_or_create(student=student, course=course, component=comp_a, defaults={"marks_obtained": ass_marks})
                
                letter_grade, points = random.choice(grades_pool)
                StudentFinalGrade.objects.update_or_create(
                    student=student, course=course, semester=semester, academic_year=academic_year,
                    defaults={"letter_grade": letter_grade, "grade_points": points, "is_verified": True}
                )
                
        self.stdout.write(self.style.SUCCESS(f"Grades generated for all registered students"))
        
        # 8. Results Published
        publisher_extra = ExtraInfo.objects.filter(user_type="acadadmin").first() or faculty_objs[0].id
        
        ResultPublication.objects.update_or_create(
            batch=batch, semester=semester, academic_year=academic_year,
            defaults={"is_published": True, "published_by": publisher_extra, "published_at": timezone.now()}
        )
        self.stdout.write(self.style.SUCCESS("Results published"))
        
        # 9. Seating Plan (Sample for CS101)
        halls = [("LH101", 60), ("LH102", 60), ("LH103", 60)]
        course_to_seat = target_courses[0]
        curr_seat = 1
        curr_hall_idx = 0
        allocated = 0
        
        SeatingPlan.objects.filter(course=course_to_seat, exam_name="Mid Semester").delete()
        
        while allocated < len(student_objs) and curr_hall_idx < len(halls):
            hall_name, cap = halls[curr_hall_idx]
            rem_in_hall = cap
            take = min(rem_in_hall, len(student_objs) - allocated)
            
            SeatingPlan.objects.create(
                exam_name="Mid Semester",
                course=course_to_seat,
                semester=semester,
                academic_year=academic_year,
                exam_date=date.today(),
                hall_name=hall_name,
                hall_capacity=cap,
                seat_start=allocated + 1,
                seat_end=allocated + take,
                generated_by=publisher_extra
            )
            allocated += take
            curr_hall_idx += 1
            
        self.stdout.write(self.style.SUCCESS(f"Seating plans created across {curr_hall_idx} halls"))
        
        print("\n" + "="*50)
        print("SEEDING COMPLETE. SUMMARY:")
        print(f"Students created: {len(student_objs)}")
        print(f"Faculty created: {len(faculty_objs)}")
        print(f"Courses created: {len(courses)}")
        print(f"Registrations created: {reg_count}")
        print("Grades generated & Results published")
        print("Seating plans created")
        print("\nSample Login Credentials:")
        if student_objs:
            s = student_objs[0].id.user.username
            print(f"Student  -> u: {s} | p: student123")
        print("Faculty  -> u: faculty1 | p: faculty123")
        print("="*50)
