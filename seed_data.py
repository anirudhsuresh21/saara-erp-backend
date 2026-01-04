"""
Seed script to populate all database tables with demo data.
Run with: python manage.py shell < seed_data.py
Or: python -c "exec(open('seed_data.py').read())"
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')
django.setup()

import uuid
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from saara.authapp.models import AllowedEmailDomain, User, UserSession, AuditLog
from saara.erp.models import (
    Institution, Department, Student, Teacher, Admin, Course, CourseFaculty,
    Attendance, FeeStructure, StudentFees, Assignment, AssignmentSubmission,
    Exam, Result
)
from saara.chatbot.models import ChatSession, ChatMessage


def clear_all_data():
    """Clear all existing data from tables"""
    print("🗑️  Clearing existing data...")
    
    # Delete in reverse dependency order
    ChatMessage.objects.all().delete()
    ChatSession.objects.all().delete()
    Result.objects.all().delete()
    Exam.objects.all().delete()
    AssignmentSubmission.objects.all().delete()
    Assignment.objects.all().delete()
    StudentFees.objects.all().delete()
    FeeStructure.objects.all().delete()
    Attendance.objects.all().delete()
    CourseFaculty.objects.all().delete()
    Course.objects.all().delete()
    from saara.erp.models import StudentCourse
    StudentCourse.objects.all().delete()
    Admin.objects.all().delete()
    Teacher.objects.all().delete()
    Student.objects.all().delete()
    # Department.objects.all().delete()
    # Institution.objects.all().delete()
    AuditLog.objects.all().delete()
    UserSession.objects.all().delete()
    User.objects.all().delete()
    AllowedEmailDomain.objects.all().delete()
    
    print("✅ All data cleared!")


def seed_allowed_email_domains():
    """Seed allowed email domains"""
    print("\n📧 Seeding allowed email domains...")
    
    domains = [
        {"domain": "sies.edu.in", "institution_name": "SIES Group of Institutions", "allow_subdomains": True},
        {"domain": "siescoms.edu.in", "institution_name": "SIES College of Management Studies", "allow_subdomains": True},
        {"domain": "siesascn.edu.in", "institution_name": "SIES Arts, Science & Commerce College", "allow_subdomains": False},
        {"domain": "university.edu", "institution_name": "Demo University", "allow_subdomains": True},
        {"domain": "college.edu.in", "institution_name": "Demo College", "allow_subdomains": True},
    ]
    
    created_domains = []
    for d in domains:
        domain = AllowedEmailDomain.objects.create(**d)
        created_domains.append(domain)
        print(f"   ✓ Created domain: {domain.domain}")
    
    return created_domains


def seed_users():
    """Seed users with different roles"""
    print("\n👤 Seeding users...")
    
    # Create admin users
    admin_users = []
    admin_emails = [
        "admin@sies.edu.in",
        "superadmin@sies.edu.in",
        "hradmin@sies.edu.in",
    ]
    
    for email in admin_emails:
        user = User.objects.create(
            email=email,
            password_hash=make_password("admin123"),
            role="admin",
            is_active=True,
            last_login=timezone.now() - timedelta(days=random.randint(0, 30))
        )
        admin_users.append(user)
        print(f"   ✓ Created admin: {email}")
    
    # Create faculty users
    faculty_users = []
    faculty_data = [
        "dr.sharma@sies.edu.in",
        "prof.patel@sies.edu.in",
        "dr.desai@sies.edu.in",
        "prof.mehta@sies.edu.in",
        "dr.iyer@sies.edu.in",
        "prof.gupta@sies.edu.in",
        "dr.verma@sies.edu.in",
        "prof.nair@sies.edu.in",
        "dr.rao@sies.edu.in",
        "prof.khan@sies.edu.in",
        "dr.singh@sies.edu.in",
        "prof.joshi@sies.edu.in",
    ]
    
    for email in faculty_data:
        user = User.objects.create(
            email=email,
            password_hash=make_password("faculty123"),
            role="faculty",
            is_active=True,
            last_login=timezone.now() - timedelta(days=random.randint(0, 60))
        )
        faculty_users.append(user)
        print(f"   ✓ Created faculty: {email}")
    
    # Create student users
    student_users = []
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", 
                   "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav", "Advaith", "Ayaan",
                   "Ananya", "Diya", "Saanvi", "Aanya", "Aadhya", "Pari", "Myra", "Sara",
                   "Navya", "Anika", "Prisha", "Riya", "Anvi", "Ira", "Kiara"]
    
    last_names = ["Sharma", "Patel", "Desai", "Mehta", "Shah", "Joshi", "Kumar", "Singh",
                  "Gupta", "Verma", "Iyer", "Nair", "Rao", "Reddy", "Kapoor", "Malhotra"]
    
    for i in range(50):
        first = random.choice(first_names)
        last = random.choice(last_names)
        email = f"{first.lower()}.{last.lower()}{i}@sies.edu.in"
        user = User.objects.create(
            email=email,
            password_hash=make_password("student123"),
            role="student",
            is_active=True,
            last_login=timezone.now() - timedelta(days=random.randint(0, 90))
        )
        student_users.append(user)
    
    print(f"   ✓ Created {len(student_users)} students")
    
    return admin_users, faculty_users, student_users


def seed_institutions():
    """Seed institutions/colleges"""
    print("\n🏛️  Seeding institutions...")
    
    institutions_data = [
        {
            "name": "SIES College of Management Studies",
            "short_name": "SIES",
            "city": "Mumbai",
            "state": "Maharashtra",
            "contact_email": "info@sies.edu.in",
            "contact_phone": "+91-22-12345678",
            "website": "https://www.sies.edu.in"
        },
        {
            "name": "D Y Patil University",
            "short_name": "DYPATIL",
            "city": "Pune",
            "state": "Maharashtra",
            "contact_email": "info@dypatil.edu",
            "contact_phone": "+91-20-87654321",
            "website": "https://www.dypatil.edu"
        },
        {
            "name": "Mumbai University",
            "short_name": "MU",
            "city": "Mumbai",
            "state": "Maharashtra",
            "contact_email": "contact@mu.ac.in",
            "contact_phone": "+91-22-11223344",
            "website": "https://www.mu.ac.in"
        },
    ]
    
    institutions = []
    for inst_data in institutions_data:
        inst = Institution.objects.create(**inst_data)
        institutions.append(inst)
        print(f"   ✓ Created institution: {inst.name}")
    
    return institutions


def seed_departments(institutions):
    """Seed departments for multiple institutions"""
    print("\n🏢 Seeding departments...")
    
    # SIES - MMS and MCA only
    sies = institutions[0]
    # DY Patil - Multiple departments
    dypatil = institutions[1]
    # Mumbai University - General departments
    mu = institutions[2]
    
    departments_data = [
        # SIES College departments
        {"institution": sies, "department_name": "Management Studies", "dept_code": "MMS", "program_type": "pg", "hod_id": "HOD001"},
        {"institution": sies, "department_name": "Computer Applications", "dept_code": "MCA", "program_type": "pg", "hod_id": "HOD002"},
        
        # DY Patil University - Engineering
        {"institution": dypatil, "department_name": "Computer Science", "dept_code": "CS", "program_type": "engg", "hod_id": "HOD003"},
        {"institution": dypatil, "department_name": "Information Technology", "dept_code": "IT", "program_type": "engg", "hod_id": "HOD004"},
        {"institution": dypatil, "department_name": "Electronics & Communication", "dept_code": "EC", "program_type": "engg", "hod_id": "HOD005"},
        {"institution": dypatil, "department_name": "Mechanical Engineering", "dept_code": "MECH", "program_type": "engg", "hod_id": "HOD006"},
        
        # DY Patil University - Undergraduate
        {"institution": dypatil, "department_name": "Computer Science", "dept_code": "CS", "program_type": "ug", "hod_id": "HOD007"},
        {"institution": dypatil, "department_name": "Management Studies", "dept_code": "BMS", "program_type": "ug", "hod_id": "HOD008"},
        
        # Mumbai University departments
        {"institution": mu, "department_name": "Data Science", "dept_code": "DS", "program_type": "pg", "hod_id": "HOD009"},
        {"institution": mu, "department_name": "Artificial Intelligence", "dept_code": "AI", "program_type": "pg", "hod_id": "HOD010"},
    ]
    
    departments = []
    for d in departments_data:
        dept = Department.objects.create(**d)
        departments.append(dept)
        print(f"   ✓ Created department: {dept.department_name} ({dept.get_program_type_display()}) - {dept.institution.short_name}")
    
    return departments


def seed_admins(admin_users):
    """Seed admin profiles"""
    print("\n👔 Seeding admin profiles...")
    
    admin_names = ["Rajesh Kumar", "Priya Sharma", "Amit Verma"]
    
    admins = []
    for user, name in zip(admin_users, admin_names):
        admin = Admin.objects.create(
            user=user,
            name=name
        )
        admins.append(admin)
        print(f"   ✓ Created admin profile: {name}")
    
    return admins


def seed_teachers(faculty_users, departments):
    """Seed teacher profiles"""
    print("\n👨‍🏫 Seeding teacher profiles...")
    
    teacher_data = [
        {"teacher_id": "TCH001", "first_name": "Rajendra", "last_name": "Sharma", "designation": "Professor"},
        {"teacher_id": "TCH002", "first_name": "Meera", "last_name": "Patel", "designation": "Associate Professor"},
        {"teacher_id": "TCH003", "first_name": "Suresh", "last_name": "Desai", "designation": "Professor"},
        {"teacher_id": "TCH004", "first_name": "Kavita", "last_name": "Mehta", "designation": "Assistant Professor"},
        {"teacher_id": "TCH005", "first_name": "Lakshmi", "last_name": "Iyer", "designation": "Professor"},
        {"teacher_id": "TCH006", "first_name": "Rahul", "last_name": "Gupta", "designation": "Associate Professor"},
        {"teacher_id": "TCH007", "first_name": "Sanjay", "last_name": "Verma", "designation": "Assistant Professor"},
        {"teacher_id": "TCH008", "first_name": "Deepa", "last_name": "Nair", "designation": "Professor"},
        {"teacher_id": "TCH009", "first_name": "Venkat", "last_name": "Rao", "designation": "Associate Professor"},
        {"teacher_id": "TCH010", "first_name": "Zara", "last_name": "Khan", "designation": "Assistant Professor"},
        {"teacher_id": "TCH011", "first_name": "Manjeet", "last_name": "Singh", "designation": "Professor"},
        {"teacher_id": "TCH012", "first_name": "Anita", "last_name": "Joshi", "designation": "Associate Professor"},
    ]
    
    teachers = []
    for i, (user, data) in enumerate(zip(faculty_users, teacher_data)):
        teacher = Teacher.objects.create(
            teacher_id=data["teacher_id"],
            user=user,
            first_name=data["first_name"],
            last_name=data["last_name"],
            department=departments[i % len(departments)],
            designation=data["designation"]
        )
        teachers.append(teacher)
        print(f"   ✓ Created teacher: {data['first_name']} {data['last_name']}")
    
    return teachers


def seed_students(student_users, departments):
    """Seed student profiles"""
    print("\n👨‍🎓 Seeding student profiles...")
    
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", 
                   "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav", "Advaith", "Ayaan",
                   "Ananya", "Diya", "Saanvi", "Aanya", "Aadhya", "Pari", "Myra", "Sara",
                   "Navya", "Anika", "Prisha", "Riya", "Anvi", "Ira", "Kiara"]
    
    middle_names = ["Kumar", "Raj", "Priya", "Devi", "Lal", "Chand", "Nath", "Das", "Mohan", "Ram"]
    
    last_names = ["Sharma", "Patel", "Desai", "Mehta", "Shah", "Joshi", "Kumar", "Singh",
                  "Gupta", "Verma", "Iyer", "Nair", "Rao", "Reddy", "Kapoor", "Malhotra"]
    
    programs = ["B.Tech", "M.Tech", "BCA", "MCA", "B.Sc IT", "M.Sc IT"]
    
    students = []
    for i, user in enumerate(student_users):
        student = Student.objects.create(
            user=user,
            first_name=random.choice(first_names),
            middle_name=random.choice(middle_names),
            last_name=random.choice(last_names),
            department=random.choice(departments),
            program=random.choice(programs),
            year_of_study=random.randint(1, 4),
            semester=random.randint(1, 8)
        )
        students.append(student)
    
    print(f"   ✓ Created {len(students)} student profiles")
    return students


def seed_courses(departments):
    """Seed courses"""
    print("\n📚 Seeding courses...")
    
    courses_data = [
        # CS Courses
        {"course_name": "Data Structures & Algorithms", "credits": 4, "semester": 3, "dept_idx": 0},
        {"course_name": "Database Management Systems", "credits": 4, "semester": 4, "dept_idx": 0},
        {"course_name": "Operating Systems", "credits": 4, "semester": 5, "dept_idx": 0},
        {"course_name": "Computer Networks", "credits": 3, "semester": 5, "dept_idx": 0},
        {"course_name": "Software Engineering", "credits": 3, "semester": 6, "dept_idx": 0},
        {"course_name": "Web Development", "credits": 3, "semester": 4, "dept_idx": 0},
        {"course_name": "Machine Learning", "credits": 4, "semester": 7, "dept_idx": 0},
        {"course_name": "Cloud Computing", "credits": 3, "semester": 7, "dept_idx": 0},
        
        # IT Courses
        {"course_name": "Information Security", "credits": 3, "semester": 6, "dept_idx": 1},
        {"course_name": "Mobile App Development", "credits": 3, "semester": 5, "dept_idx": 1},
        {"course_name": "Big Data Analytics", "credits": 4, "semester": 7, "dept_idx": 1},
        {"course_name": "DevOps Practices", "credits": 3, "semester": 8, "dept_idx": 1},
        
        # Electronics Courses
        {"course_name": "Digital Electronics", "credits": 4, "semester": 3, "dept_idx": 2},
        {"course_name": "Microprocessors", "credits": 4, "semester": 4, "dept_idx": 2},
        {"course_name": "VLSI Design", "credits": 3, "semester": 6, "dept_idx": 2},
        {"course_name": "Embedded Systems", "credits": 4, "semester": 7, "dept_idx": 2},
        
        # Mechanical Courses
        {"course_name": "Thermodynamics", "credits": 4, "semester": 3, "dept_idx": 3},
        {"course_name": "Fluid Mechanics", "credits": 4, "semester": 4, "dept_idx": 3},
        {"course_name": "Machine Design", "credits": 3, "semester": 5, "dept_idx": 3},
        {"course_name": "Automobile Engineering", "credits": 3, "semester": 7, "dept_idx": 3},
        
        # Data Science Courses
        {"course_name": "Statistical Methods", "credits": 3, "semester": 3, "dept_idx": 6},
        {"course_name": "Data Mining", "credits": 4, "semester": 5, "dept_idx": 6},
        {"course_name": "Deep Learning", "credits": 4, "semester": 6, "dept_idx": 6},
        {"course_name": "Natural Language Processing", "credits": 3, "semester": 7, "dept_idx": 6},
        
        # AI/ML Courses
        {"course_name": "Artificial Intelligence", "credits": 4, "semester": 5, "dept_idx": 7},
        {"course_name": "Neural Networks", "credits": 4, "semester": 6, "dept_idx": 7},
        {"course_name": "Computer Vision", "credits": 3, "semester": 7, "dept_idx": 7},
        {"course_name": "Reinforcement Learning", "credits": 3, "semester": 8, "dept_idx": 7},
    ]
    
    courses = []
    for c in courses_data:
        course = Course.objects.create(
            course_name=c["course_name"],
            credits=c["credits"],
            semester=c["semester"],
            department=departments[c["dept_idx"]]
        )
        courses.append(course)
        print(f"   ✓ Created course: {course.course_name}")
    
    return courses


def seed_course_faculty(courses, teachers):
    """Seed course-faculty assignments"""
    print("\n👥 Seeding course-faculty assignments...")
    
    assignments = []
    for course in courses:
        # Assign 1-2 teachers per course
        num_teachers = random.randint(1, 2)
        assigned_teachers = random.sample(teachers, min(num_teachers, len(teachers)))
        
        for teacher in assigned_teachers:
            cf = CourseFaculty.objects.create(
                course=course,
                teacher=teacher
            )
            assignments.append(cf)
    
    print(f"   ✓ Created {len(assignments)} course-faculty assignments")
    return assignments


def seed_student_courses(students, courses):
    """Seed student course enrollments"""
    print("\n📖 Seeding student course enrollments...")
    from saara.erp.models import StudentCourse
    
    enrollments = []
    academic_years = [2024, 2025, 2026]
    
    for student in students:
        # Each student enrolls in 4-6 courses
        num_courses = random.randint(4, 6)
        # Filter courses by student's department if possible
        dept_courses = [c for c in courses if c.department == student.department]
        
        if len(dept_courses) >= num_courses:
            selected_courses = random.sample(dept_courses, num_courses)
        else:
            # If not enough dept courses, add some from other departments
            selected_courses = dept_courses + random.sample(
                [c for c in courses if c not in dept_courses],
                min(num_courses - len(dept_courses), len(courses) - len(dept_courses))
            )
        
        for course in selected_courses:
            # Random academic year and semester
            academic_year = random.choice(academic_years)
            semester = student.semester if random.random() > 0.3 else random.randint(1, 8)
            
            # Some students have grades (completed courses), others don't (ongoing)
            grade = None
            if random.random() > 0.4:  # 60% have grades
                grade = random.choice(['A+', 'A', 'B+', 'B', 'C+', 'C', 'D'])
            
            try:
                enrollment = StudentCourse.objects.create(
                    student=student,
                    course=course,
                    academic_year=academic_year,
                    semester=semester,
                    grade=grade
                )
                enrollments.append(enrollment)
            except:
                # Skip if duplicate (unique constraint)
                pass
    
    print(f"   ✓ Created {len(enrollments)} student course enrollments")
    return enrollments


def seed_attendance(students, courses):
    """Seed attendance records"""
    print("\n📋 Seeding attendance records...")
    
    statuses = ['present', 'present', 'present', 'present', 'absent', 'late', 'excused']  # Weighted towards present
    
    attendance_records = []
    # Generate attendance for past 60 days
    start_date = date.today() - timedelta(days=60)
    
    for student in students[:30]:  # For first 30 students
        student_courses = random.sample(courses, min(5, len(courses)))  # Each student has 5 courses
        
        for course in student_courses:
            # Generate attendance for ~20 class days
            for i in range(20):
                class_date = start_date + timedelta(days=i * 3)  # Every 3 days
                if class_date.weekday() < 5:  # Weekdays only
                    attendance = Attendance.objects.create(
                        student=student,
                        course=course,
                        date=class_date,
                        status=random.choice(statuses)
                    )
                    attendance_records.append(attendance)
    
    print(f"   ✓ Created {len(attendance_records)} attendance records")
    return attendance_records


def seed_fee_structure(departments):
    """Seed fee structures per department (annual fees, no semester)"""
    print("\n💰 Seeding fee structures...")
    
    fee_structures = []
    academic_years = [2024, 2025, 2026]
    
    for dept in departments:
        for year in academic_years:
            # Vary fees based on program type
            if dept.program_type == 'engg':
                tuition = Decimal(random.randint(80000, 120000))
                development = Decimal(random.randint(15000, 25000))
            elif dept.program_type == 'pg':
                tuition = Decimal(random.randint(60000, 90000))
                development = Decimal(random.randint(10000, 20000))
            else:  # ug, diploma, phd, other
                tuition = Decimal(random.randint(40000, 60000))
                development = Decimal(random.randint(5000, 15000))
            
            fee = FeeStructure.objects.create(
                fee_id=f"FEE-{dept.dept_code}-{dept.program_type}-{year}",
                department=dept,
                academic_year=year,
                tution_fees=tuition,
                development_fees=development
            )
            fee_structures.append(fee)
    
    print(f"   ✓ Created {len(fee_structures)} fee structures ({len(departments)} departments x 3 years)")
    return fee_structures


def seed_student_fees(students, fee_structures):
    """Seed student fee payments"""
    print("\n💳 Seeding student fee payments...")
    
    statuses = ['paid', 'paid', 'paid', 'partial', 'pending', 'overdue']  # Weighted towards paid
    
    student_fees = []
    for student in students:
        # Each student has 1-3 fee records
        num_fees = random.randint(1, 3)
        fees = random.sample(fee_structures, min(num_fees, len(fee_structures)))
        
        for fee in fees:
            status = random.choice(statuses)
            total = fee.amount
            
            if status == 'paid':
                amount_paid = total
                due_amount = Decimal('0.00')
            elif status == 'partial':
                amount_paid = total * Decimal(str(random.uniform(0.3, 0.7)))
                due_amount = total - amount_paid
            else:
                amount_paid = Decimal('0.00')
                due_amount = total
            
            sf = StudentFees.objects.create(
                student=student,
                fee=fee,
                amount_paid=round(amount_paid, 2),
                due_amount=round(due_amount, 2),
                status=status
            )
            student_fees.append(sf)
    
    print(f"   ✓ Created {len(student_fees)} student fee records")
    return student_fees


def seed_assignments(courses, teachers):
    """Seed assignments"""
    print("\n📝 Seeding assignments...")
    
    assignment_titles = [
        "Lab Exercise 1", "Lab Exercise 2", "Lab Exercise 3",
        "Programming Assignment", "Research Paper Review",
        "Case Study Analysis", "Mini Project", "Group Project",
        "Technical Report", "Presentation Slides",
        "Design Document", "Code Review Assignment",
        "Problem Set 1", "Problem Set 2", "Quiz Preparation"
    ]
    
    assignments = []
    for course in courses:
        # 2-4 assignments per course
        num_assignments = random.randint(2, 4)
        
        for i in range(num_assignments):
            due_date = timezone.now() + timedelta(days=random.randint(-30, 60))
            teacher = random.choice(teachers)
            
            assignment = Assignment.objects.create(
                course=course,
                title=f"{random.choice(assignment_titles)} - {course.course_name[:20]}",
                description=f"Complete the following tasks for {course.course_name}. Submit before the deadline.",
                file_url=f"https://assignments.example.com/{uuid.uuid4()}.pdf",
                due_date=due_date,
                created_by=teacher
            )
            assignments.append(assignment)
    
    print(f"   ✓ Created {len(assignments)} assignments")
    return assignments


def seed_assignment_submissions(assignments, students):
    """Seed assignment submissions"""
    print("\n📤 Seeding assignment submissions...")
    
    submissions = []
    for assignment in assignments:
        # 30-80% of students submit each assignment
        submission_rate = random.uniform(0.3, 0.8)
        submitting_students = random.sample(students, int(len(students) * submission_rate))
        
        for student in submitting_students:
            submitted_date = assignment.due_date.date() - timedelta(days=random.randint(0, 7))
            score = Decimal(str(random.uniform(50, 100))) if random.random() > 0.1 else None  # 10% not graded yet
            
            submission = AssignmentSubmission.objects.create(
                assignment=assignment,
                student=student,
                submitted_date=submitted_date,
                score=round(score, 2) if score else None
            )
            submissions.append(submission)
    
    print(f"   ✓ Created {len(submissions)} assignment submissions")
    return submissions


def seed_exams(courses):
    """Seed exams"""
    print("\n📋 Seeding exams...")
    
    exam_types = ['midterm', 'final', 'quiz', 'practical']
    
    exams = []
    exam_counter = 1
    
    for course in courses:
        # Each course has 2-4 exams
        num_exams = random.randint(2, 4)
        
        for _ in range(num_exams):
            exam_type = random.choice(exam_types)
            exam_date = date.today() + timedelta(days=random.randint(-60, 60))
            
            if exam_type == 'quiz':
                total_marks = random.choice([10, 20, 25])
            elif exam_type == 'practical':
                total_marks = random.choice([25, 50])
            else:
                total_marks = random.choice([50, 100])
            
            exam = Exam.objects.create(
                exam_id=f"EXAM{exam_counter:04d}",
                course=course,
                exam_type=exam_type,
                exam_date=exam_date,
                total_marks=total_marks
            )
            exams.append(exam)
            exam_counter += 1
    
    print(f"   ✓ Created {len(exams)} exams")
    return exams


def seed_results(exams, students):
    """Seed exam results"""
    print("\n📊 Seeding exam results...")
    
    def calculate_grade(percentage):
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 35:
            return 'D'
        else:
            return 'F'
    
    results = []
    for exam in exams:
        # 60-90% of students have results
        result_rate = random.uniform(0.6, 0.9)
        students_with_results = random.sample(students, int(len(students) * result_rate))
        
        for student in students_with_results:
            marks = Decimal(str(random.uniform(30, 100))) * exam.total_marks / 100
            percentage = (marks / exam.total_marks) * 100
            
            result = Result.objects.create(
                exam=exam,
                student=student,
                marks_obtained=round(marks, 2),
                grade=calculate_grade(float(percentage))
            )
            results.append(result)
    
    print(f"   ✓ Created {len(results)} exam results")
    return results


def seed_user_sessions(all_users):
    """Seed user sessions"""
    print("\n🔐 Seeding user sessions...")
    
    sessions = []
    for user in random.sample(all_users, min(30, len(all_users))):
        # 1-3 sessions per user
        num_sessions = random.randint(1, 3)
        
        for _ in range(num_sessions):
            created = timezone.now() - timedelta(days=random.randint(0, 30))
            expires = created + timedelta(days=7)
            
            session = UserSession.objects.create(
                user=user,
                created_at=created,
                expires_at=expires
            )
            sessions.append(session)
    
    print(f"   ✓ Created {len(sessions)} user sessions")
    return sessions


def seed_audit_logs(all_users):
    """Seed audit logs"""
    print("\n📜 Seeding audit logs...")
    
    actions = [
        "User logged in",
        "User logged out",
        "Password changed",
        "Profile updated",
        "Viewed attendance records",
        "Downloaded report",
        "Submitted assignment",
        "Viewed grades",
        "Accessed course materials",
        "Updated settings",
        "Exported data",
        "Viewed fee details",
        "Made payment",
        "Requested document",
    ]
    
    logs = []
    for user in all_users:
        # 3-10 log entries per user
        num_logs = random.randint(3, 10)
        
        for _ in range(num_logs):
            log = AuditLog.objects.create(
                user=user,
                action=random.choice(actions)
            )
            logs.append(log)
    
    print(f"   ✓ Created {len(logs)} audit log entries")
    return logs


def seed_chat_sessions(all_users):
    """Seed chat sessions and messages"""
    print("\n💬 Seeding chat sessions and messages...")
    
    chat_titles = [
        "Help with attendance",
        "Fee payment inquiry",
        "Course registration",
        "Assignment deadline",
        "Grade inquiry",
        "Exam schedule",
        "General query",
        "Technical support",
        "Library access",
        "Campus facilities",
    ]
    
    user_messages = [
        "Hi, I need help with my attendance records.",
        "Can you tell me my current attendance percentage?",
        "What is the deadline for fee payment?",
        "How do I register for next semester courses?",
        "When is the midterm exam?",
        "Can you show me my grades?",
        "I have a question about my assignment.",
        "How do I access the library database?",
        "What are the campus timings?",
        "Can you help me with my fee structure?",
    ]
    
    assistant_responses = [
        "Sure, I'd be happy to help you with that! Let me check your records.",
        "Based on your records, your current attendance percentage is 85%.",
        "The fee payment deadline is December 31st, 2025.",
        "You can register for courses through the student portal from January 1st.",
        "Your midterm exam is scheduled for next week.",
        "Here are your current grades for this semester.",
        "Of course! Please provide more details about your assignment query.",
        "You can access the library database using your student credentials.",
        "The campus is open from 8 AM to 8 PM on weekdays.",
        "Let me pull up your fee structure details.",
    ]
    
    sessions = []
    messages = []
    
    for user in random.sample(all_users, min(40, len(all_users))):
        # 1-3 chat sessions per user
        num_sessions = random.randint(1, 3)
        
        for _ in range(num_sessions):
            session = ChatSession.objects.create(
                user=user,
                title=random.choice(chat_titles),
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            sessions.append(session)
            
            # 2-8 messages per session
            num_messages = random.randint(2, 8)
            
            for j in range(num_messages):
                if j % 2 == 0:  # User message
                    msg = ChatMessage.objects.create(
                        session=session,
                        role='user',
                        content=random.choice(user_messages),
                        tokens_used=random.randint(10, 50)
                    )
                else:  # Assistant response
                    msg = ChatMessage.objects.create(
                        session=session,
                        role='assistant',
                        content=random.choice(assistant_responses),
                        tokens_used=random.randint(50, 200)
                    )
                messages.append(msg)
    
    print(f"   ✓ Created {len(sessions)} chat sessions with {len(messages)} messages")
    return sessions, messages


def run_seed():
    """Main function to run all seeders"""
    print("\n" + "="*60)
    print("🌱 STARTING DATABASE SEED PROCESS")
    print("="*60)
    
    # Clear existing data
    clear_all_data()
    
    # Seed in order of dependencies
    seed_allowed_email_domains()
    admin_users, faculty_users, student_users = seed_users()
    all_users = admin_users + faculty_users + student_users
    
    institutions = seed_institutions()
    departments = seed_departments(institutions)
    
    seed_admins(admin_users)
    teachers = seed_teachers(faculty_users, departments)
    students = seed_students(student_users, departments)
    
    courses = seed_courses(departments)
    seed_course_faculty(courses, teachers)
    seed_student_courses(students, courses)
    
    seed_attendance(students, courses)
    
    fee_structures = seed_fee_structure(departments)
    seed_student_fees(students, fee_structures)
    
    assignments = seed_assignments(courses, teachers)
    seed_assignment_submissions(assignments, students)
    
    exams = seed_exams(courses)
    seed_results(exams, students)
    
    seed_user_sessions(all_users)
    seed_audit_logs(all_users)
    
    seed_chat_sessions(all_users)
    
    print("\n" + "="*60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Print summary
    print("\n📊 SUMMARY:")
    print(f"   • Allowed Email Domains: {AllowedEmailDomain.objects.count()}")
    print(f"   • Users: {User.objects.count()}")
    print(f"   • Institutions: {Institution.objects.count()}")
    print(f"   • Departments: {Department.objects.count()}")
    print(f"   • Admins: {Admin.objects.count()}")
    print(f"   • Teachers: {Teacher.objects.count()}")
    print(f"   • Students: {Student.objects.count()}")
    print(f"   • Courses: {Course.objects.count()}")
    print(f"   • Course-Faculty Assignments: {CourseFaculty.objects.count()}")
    from saara.erp.models import StudentCourse
    print(f"   • Student Course Enrollments: {StudentCourse.objects.count()}")
    print(f"   • Attendance Records: {Attendance.objects.count()}")
    print(f"   • Fee Structures: {FeeStructure.objects.count()}")
    print(f"   • Student Fees: {StudentFees.objects.count()}")
    print(f"   • Assignments: {Assignment.objects.count()}")
    print(f"   • Assignment Submissions: {AssignmentSubmission.objects.count()}")
    print(f"   • Exams: {Exam.objects.count()}")
    print(f"   • Results: {Result.objects.count()}")
    print(f"   • User Sessions: {UserSession.objects.count()}")
    print(f"   • Audit Logs: {AuditLog.objects.count()}")
    print(f"   • Chat Sessions: {ChatSession.objects.count()}")
    print(f"   • Chat Messages: {ChatMessage.objects.count()}")
    print("")


if __name__ == '__main__':
    run_seed()
