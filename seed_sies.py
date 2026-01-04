"""
SIES College Seed Data
Populates database with SIES College of Management Studies data
- MMS Program (120 students, Semester 1)
- MCA Program (120 students, Semester 1)
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')
django.setup()

import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from saara.authapp.models import AllowedEmailDomain, User
from saara.erp.models import (
    Institution, Department, Student, Teacher, Admin, Course, 
    CourseFaculty, StudentCourse, FeeStructure
)


def clear_all_data():
    """Clear existing data"""
    print("🗑️  Clearing existing data...")
    from saara.erp.models import StudentCourse
    StudentCourse.objects.all().delete()
    CourseFaculty.objects.all().delete()
    Course.objects.all().delete()
    FeeStructure.objects.all().delete()
    Student.objects.all().delete()
    Teacher.objects.all().delete()
    Admin.objects.all().delete()
    Department.objects.all().delete()
    Institution.objects.all().delete()
    User.objects.all().delete()
    AllowedEmailDomain.objects.all().delete()
    print("✅ Data cleared!")


def seed_domain():
    """Seed SIES email domain"""
    print("\n📧 Seeding email domain...")
    domain = AllowedEmailDomain.objects.create(
        domain="siescoms.sies.edu.in",
        institution_name="SIES College of Management Studies",
        allow_subdomains=False
    )
    print(f"   ✓ Created domain: {domain.domain}")
    return domain


def seed_institution():
    """Seed SIES institution"""
    print("\n🏛️  Seeding institution...")
    inst = Institution.objects.create(
        name="SIES College of Management Studies",
        short_name="SIESCOMS",
        city="Mumbai",
        state="Maharashtra",
        contact_email="info@siescoms.sies.edu.in",
        contact_phone="+91-22-2657-5752",
        website="https://www.siescoms.edu"
    )
    print(f"   ✓ Created: {inst.name}")
    return inst


def seed_departments(institution):
    """Seed MMS and MCA departments"""
    print("\n🏢 Seeding departments...")
    
    mms = Department.objects.create(
        institution=institution,
        department_name="Management Studies",
        dept_code="MMS",
        program_type="pg",
        hod_id="HOD-MMS-001"
    )
    print(f"   ✓ Created: {mms.department_name} (MMS)")
    
    mca = Department.objects.create(
        institution=institution,
        department_name="Computer Applications",
        dept_code="MCA",
        program_type="pg",
        hod_id="HOD-MCA-001"
    )
    print(f"   ✓ Created: {mca.department_name} (MCA)")
    
    return mms, mca


def seed_users():
    """Seed admin, faculty, and student users"""
    print("\n👤 Seeding users...")
    
    # Admin users (3)
    admin_users = []
    for i in range(1, 4):
        user = User.objects.create(
            email=f"admin{i}@siescoms.sies.edu.in",
            password_hash=make_password("admin123"),
            role="admin",
            is_active=True
        )
        admin_users.append(user)
    print(f"   ✓ Created {len(admin_users)} admin users")
    
    # Faculty users (20)
    faculty_users = []
    for i in range(1, 21):
        user = User.objects.create(
            email=f"faculty{i}@siescoms.sies.edu.in",
            password_hash=make_password("faculty123"),
            role="faculty",
            is_active=True
        )
        faculty_users.append(user)
    print(f"   ✓ Created {len(faculty_users)} faculty users")
    
    # Student users (240 total: 120 MMS + 120 MCA)
    student_users = []
    for i in range(1, 241):
        user = User.objects.create(
            email=f"student{i}@siescoms.sies.edu.in",
            password_hash=make_password("student123"),
            role="student",
            is_active=True
        )
        student_users.append(user)
    print(f"   ✓ Created {len(student_users)} student users")
    
    return admin_users, faculty_users, student_users


def seed_admins(admin_users):
    """Seed admin profiles"""
    print("\n👔 Seeding admins...")
    
    admin_names = ["Dr. Rajesh Kumar", "Ms. Priya Sharma", "Mr. Amit Verma"]
    admins = []
    
    for user, name in zip(admin_users, admin_names):
        admin = Admin.objects.create(user=user, name=name)
        admins.append(admin)
    
    print(f"   ✓ Created {len(admins)} admins")
    return admins


def seed_teachers(faculty_users, mms_dept, mca_dept):
    """Seed teacher profiles"""
    print("\n👨‍🏫 Seeding teachers...")
    
    first_names = ["Rajesh", "Meera", "Suresh", "Kavita", "Lakshmi", "Rahul", "Deepa", "Venkat", 
                   "Anita", "Sanjay", "Priya", "Amit", "Neha", "Vikram", "Pooja", "Arun", 
                   "Swati", "Kiran", "Ravi", "Anjali"]
    last_names = ["Sharma", "Patel", "Desai", "Mehta", "Iyer", "Gupta", "Verma", "Nair", 
                  "Joshi", "Singh"]
    
    teachers = []
    for i, user in enumerate(faculty_users):
        # First 10 for MMS, next 10 for MCA
        dept = mms_dept if i < 10 else mca_dept
        
        teacher = Teacher.objects.create(
            teacher_id=f"TCH{i+1:03d}",
            user=user,
            first_name=first_names[i],
            last_name=random.choice(last_names),
            department=dept,
            designation=random.choice(["Professor", "Associate Professor", "Assistant Professor"])
        )
        teachers.append(teacher)
    
    print(f"   ✓ Created {len(teachers)} teachers")
    return teachers


def seed_students(student_users, mms_dept, mca_dept):
    """Seed 240 students: 120 MMS + 120 MCA, all in Semester 1"""
    print("\n👨‍🎓 Seeding students...")
    
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
                   "Ishaan", "Shaurya", "Ananya", "Diya", "Saanvi", "Aanya", "Aadhya", "Pari",
                   "Navya", "Anika", "Prisha", "Riya"]
    middle_names = ["Kumar", "Raj", "Priya", "Devi", "Lal", "Chand"]
    last_names = ["Sharma", "Patel", "Desai", "Mehta", "Shah", "Joshi", "Kumar", "Singh",
                  "Gupta", "Verma", "Iyer", "Nair", "Rao", "Reddy"]
    
    students = []
    for i, user in enumerate(student_users):
        # First 120 = MMS, Next 120 = MCA
        if i < 120:
            dept = mms_dept
            program = "MMS"
        else:
            dept = mca_dept
            program = "MCA"
        
        student = Student.objects.create(
            user=user,
            first_name=random.choice(first_names),
            middle_name=random.choice(middle_names),
            last_name=random.choice(last_names),
            department=dept,
            program=program,
            year_of_study=1,
            semester=1
        )
        students.append(student)
    
    print(f"   ✓ Created {len(students)} students (120 MMS + 120 MCA)")
    return students


def seed_mms_courses(mms_dept):
    """Seed MMS Semester 1 courses"""
    print("\n📚 Seeding MMS Semester I courses...")
    
    # Core courses
    core_courses = [
        {"code": "MMS101", "name": "Perspective Management", "credits": 4},
        {"code": "MMS102", "name": "Financial Accounting", "credits": 4},
        {"code": "MMS103", "name": "Business Statistics", "credits": 4},
        {"code": "MMS104", "name": "Operations Management", "credits": 4},
        {"code": "MMS105", "name": "Managerial Economics", "credits": 4},
    ]
    
    # Electives (students choose 3 out of these)
    elective_courses = [
        {"code": "MMS1E1", "name": "Effective and Management Communication"},
        {"code": "MMS1E2", "name": "Business Ethics"},
        {"code": "MMS1E3", "name": "Management Information System"},
        {"code": "MMS1E4", "name": "Organizational Behaviour"},
        {"code": "MMS1E5", "name": "Introduction to Creativity and Innovation Management"},
    ]
    
    courses = []
    
    # Create core courses
    for course_data in core_courses:
        course = Course.objects.create(
            course_id=course_data["code"],
            course_name=course_data["name"],
            credits=course_data["credits"],
            semester=1,
            department=mms_dept
        )
        courses.append(course)
    
    # Create elective courses
    for elective_data in elective_courses:
        course = Course.objects.create(
            course_id=elective_data["code"],
            course_name=elective_data["name"],
            credits=4,
            semester=1,
            department=mms_dept
        )
        courses.append(course)
    
    print(f"   ✓ Created {len(courses)} MMS courses (5 core + {len(elective_courses)} electives)")
    return courses


def seed_mca_courses(mca_dept):
    """Seed MCA Semester 1 courses"""
    print("\n📚 Seeding MCA Semester I courses...")
    
    # Mandatory courses
    mandatory_courses = [
        {"code": "MCA11", "name": "Mathematical Foundation for Computer Science", "credits": 4},
        {"code": "MCA12", "name": "Advanced Java", "credits": 3},
        {"code": "MCA13", "name": "Advanced Database Management System", "credits": 3},
        {"code": "MCA14", "name": "Software Project Management", "credits": 3},
    ]
    
    # Elective-1 options
    elective_courses = [
        {"code": "MCA1E1", "name": "Accounting & Managerial Economics"},
        {"code": "MCA1E2", "name": "Optimization Techniques"},
        {"code": "MCA1E3", "name": "Digital Marketing and Business Analytics"},
        {"code": "MCA1E4", "name": "E-Commerce"}
    ]
    
    # Lab courses
    lab_courses = [
        {"code": "MCAL11", "name": "Advanced Data Structures Lab"},
        {"code": "MCAL12", "name": "Advanced Java Lab"},
        {"code": "MCAL13", "name": "Advanced DBMS Lab"},
        {"code": "MCAL14", "name": "Web Technologies Lab"}
    ]
    
    courses = []
    
    # Create mandatory courses
    for course_data in mandatory_courses:
        course = Course.objects.create(
            course_id=course_data["code"],
            course_name=course_data["name"],
            credits=course_data["credits"],
            semester=1,
            department=mca_dept
        )
        courses.append(course)
    
    # Create electives
    for elective_data in elective_courses:
        course = Course.objects.create(
            course_id=elective_data["code"],
            course_name=elective_data["name"],
            credits=3,
            semester=1,
            department=mca_dept
        )
        courses.append(course)
    
    # Create lab courses
    for lab_data in lab_courses:
        course = Course.objects.create(
            course_id=lab_data["code"],
            course_name=lab_data["name"],
            credits=1,
            semester=1,
            department=mca_dept
        )
        courses.append(course)
    
    # Mini Project
    project = Course.objects.create(
        course_id="MCAP1",
        course_name="Mini Project – IA",
        credits=2,
        semester=1,
        department=mca_dept
    )
    courses.append(project)
    
    print(f"   ✓ Created {len(courses)} MCA courses (4 mandatory + 4 electives + 4 labs + 1 project)")
    return courses


def seed_course_faculty(mms_courses, mca_courses, teachers):
    """Assign teachers to courses"""
    print("\n👥 Seeding course-faculty assignments...")
    
    mms_teachers = teachers[:10]
    mca_teachers = teachers[10:20]
    
    assignments = []
    
    # Assign MMS courses
    for course in mms_courses:
        teacher = random.choice(mms_teachers)
        cf = CourseFaculty.objects.create(course=course, teacher=teacher)
        assignments.append(cf)
    
    # Assign MCA courses
    for course in mca_courses:
        teacher = random.choice(mca_teachers)
        cf = CourseFaculty.objects.create(course=course, teacher=teacher)
        assignments.append(cf)
    
    print(f"   ✓ Created {len(assignments)} course-faculty assignments")
    return assignments


def seed_student_enrollments(students, mms_courses, mca_courses):
    """Enroll all students in Semester 1 courses"""
    print("\n📖 Enrolling students in courses...")
    
    enrollments = []
    
    for student in students:
        if student.program == "MMS":
            # Enroll in all 5 core courses
            core_courses = mms_courses[:5]
            # Randomly select 3 electives
            electives = random.sample(mms_courses[5:], 3)
            student_courses = core_courses + electives
        else:  # MCA
            # Enroll in all mandatory courses (4) + 1 elective + all labs (4) + project
            mandatory = mca_courses[:4]
            elective = [random.choice(mca_courses[4:8])]
            labs = mca_courses[8:12]
            project = [mca_courses[12]]
            student_courses = mandatory + elective + labs + project
        
        for course in student_courses:
            enrollment = StudentCourse.objects.create(
                student=student,
                course=course,
                academic_year=2026,
                semester=1
            )
            enrollments.append(enrollment)
    
    print(f"   ✓ Created {len(enrollments)} student enrollments")
    return enrollments


def seed_fee_structure(mms_dept, mca_dept):
    """Seed fee structures for MMS and MCA"""
    print("\n💰 Seeding fee structures...")
    
    fees = []
    
    # MMS fees (Postgraduate Management)
    mms_fee = FeeStructure.objects.create(
        fee_id="FEE-MMS-PG-2026",
        department=mms_dept,
        academic_year=2026,
        tution_fees=Decimal("75000.00"),
        development_fees=Decimal("15000.00")
    )
    fees.append(mms_fee)
    
    # MCA fees (Postgraduate Computer Applications)
    mca_fee = FeeStructure.objects.create(
        fee_id="FEE-MCA-PG-2026",
        department=mca_dept,
        academic_year=2026,
        tution_fees=Decimal("65000.00"),
        development_fees=Decimal("12000.00")
    )
    fees.append(mca_fee)
    
    print(f"   ✓ Created {len(fees)} fee structures")
    return fees


def run_seed():
    """Main seed function"""
    print("\n" + "="*70)
    print("🌱 SIES COLLEGE SEED PROCESS")
    print("="*70)
    
    clear_all_data()
    
    # Seed core data
    seed_domain()
    institution = seed_institution()
    mms_dept, mca_dept = seed_departments(institution)
    
    # Seed users
    admin_users, faculty_users, student_users = seed_users()
    
    # Seed profiles
    seed_admins(admin_users)
    teachers = seed_teachers(faculty_users, mms_dept, mca_dept)
    students = seed_students(student_users, mms_dept, mca_dept)
    
    # Seed courses
    mms_courses = seed_mms_courses(mms_dept)
    mca_courses = seed_mca_courses(mca_dept)
    
    # Seed relationships
    seed_course_faculty(mms_courses, mca_courses, teachers)
    seed_student_enrollments(students, mms_courses, mca_courses)
    seed_fee_structure(mms_dept, mca_dept)
    
    print("\n" + "="*70)
    print("✅ SEED COMPLETED SUCCESSFULLY!")
    print("="*70)
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"   • Institution: {Institution.objects.count()}")
    print(f"   • Departments: {Department.objects.count()}")
    print(f"   • Users: {User.objects.count()}")
    print(f"   • Admins: {Admin.objects.count()}")
    print(f"   • Teachers: {Teacher.objects.count()}")
    print(f"   • Students: {Student.objects.count()}")
    print(f"   • Courses: {Course.objects.count()}")
    print(f"   • Course Faculty: {CourseFaculty.objects.count()}")
    print(f"   • Student Enrollments: {StudentCourse.objects.count()}")
    print(f"   • Fee Structures: {FeeStructure.objects.count()}")
    print("\n✨ All 240 students (120 MMS + 120 MCA) enrolled in Semester 1 courses")
    print()


if __name__ == '__main__':
    run_seed()
