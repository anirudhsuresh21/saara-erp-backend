"""
Seed script to populate all database tables with demo data.
Run with: python manage.py shell < seed_data.py
Or: python -c "exec(open('seed_data.py').read())"

Constraints:
- Only 2 departments: Computer Applications (MCA) and Management (MMS)
- 60 students per department per academic year
- First Year → Semester 2, Second Year → Semester 4
- Students enrolled only in their department's courses
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
    Exam, Result, StudentCourse
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
    StudentCourse.objects.all().delete()
    Course.objects.all().delete()
    Admin.objects.all().delete()
    Teacher.objects.all().delete()
    Student.objects.all().delete()
    Department.objects.all().delete()
    Institution.objects.all().delete()
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
    
    # Create faculty users - 6 for MCA, 6 for MMS
    faculty_users = []
    faculty_data = [
        # MCA Faculty
        ("dr.sharma@sies.edu.in", "MCA"),
        ("prof.patel@sies.edu.in", "MCA"),
        ("dr.desai@sies.edu.in", "MCA"),
        ("prof.mehta@sies.edu.in", "MCA"),
        ("dr.iyer@sies.edu.in", "MCA"),
        ("prof.gupta@sies.edu.in", "MCA"),
        # MMS Faculty
        ("dr.verma@sies.edu.in", "MMS"),
        ("prof.nair@sies.edu.in", "MMS"),
        ("dr.rao@sies.edu.in", "MMS"),
        ("prof.khan@sies.edu.in", "MMS"),
        ("dr.singh@sies.edu.in", "MMS"),
        ("prof.joshi@sies.edu.in", "MMS"),
    ]
    
    for email, dept in faculty_data:
        user = User.objects.create(
            email=email,
            password_hash=make_password("faculty123"),
            role="faculty",
            is_active=True,
            last_login=timezone.now() - timedelta(days=random.randint(0, 60))
        )
        faculty_users.append((user, dept))
        print(f"   ✓ Created faculty: {email} ({dept})")
    
    # Create student users - 60 per department per year = 240 total
    student_users = []
    
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", 
                   "Ishaan", "Shaurya", "Atharva", "Advik", "Pranav", "Advaith", "Ayaan",
                   "Ananya", "Diya", "Saanvi", "Aanya", "Aadhya", "Pari", "Myra", "Sara",
                   "Navya", "Anika", "Prisha", "Riya", "Anvi", "Ira", "Kiara", "Rohan",
                   "Kabir", "Arnav", "Dhruv", "Yash", "Om", "Harsh", "Karan", "Rahul", "Amit"]
    
    last_names = ["Sharma", "Patel", "Desai", "Mehta", "Shah", "Joshi", "Kumar", "Singh",
                  "Gupta", "Verma", "Iyer", "Nair", "Rao", "Reddy", "Kapoor", "Malhotra",
                  "Pillai", "Menon", "Kulkarni", "Patil", "Deshpande", "Sawant", "Thakur"]
    
    # Generate students for each department and year
    # Roll numbers: MCA1001 for Year 1, MCA2001 for Year 2
    student_configs = [
        ("MCA", 1, 2, 60, 1001),   # MCA First Year, Semester 2, 60 students, start from 1001
        ("MCA", 2, 4, 60, 2001),   # MCA Second Year, Semester 4, 60 students, start from 2001
        ("MMS", 1, 2, 60, 1001),   # MMS First Year, Semester 2, 60 students, start from 1001
        ("MMS", 2, 4, 60, 2001),   # MMS Second Year, Semester 4, 60 students, start from 2001
    ]
    
    for dept, year, semester, count, roll_start in student_configs:
        for i in range(count):
            first = random.choice(first_names)
            last = random.choice(last_names)
            roll_no = f"{dept}{roll_start + i}"  # MCA1001, MCA1002, ... MCA2001, MCA2002
            email = f"{first.lower()}.{last.lower()}.{roll_no.lower()}@sies.edu.in"
            
            user = User.objects.create(
                email=email,
                password_hash=make_password("student123"),
                role="student",
                is_active=True,
                last_login=timezone.now() - timedelta(days=random.randint(0, 90))
            )
            student_users.append({
                "user": user,
                "first_name": first,
                "last_name": last,
                "dept": dept,
                "year": year,
                "semester": semester,
                "roll_no": roll_no
            })
            student_counter += 1
    
    print(f"   ✓ Created {len(student_users)} students (60 per dept per year)")
    
    return admin_users, faculty_users, student_users


def seed_institution():
    """Seed single institution"""
    print("\n🏛️  Seeding institution...")
    
    institution = Institution.objects.create(
        name="SIES College of Management Studies",
        short_name="SIESCOMS",
        city="Mumbai",
        state="Maharashtra",
        contact_email="info@siescoms.edu.in",
        contact_phone="+91-22-12345678",
        website="https://www.siescoms.edu"
    )
    print(f"   ✓ Created institution: {institution.name}")
    
    return institution


def seed_departments(institution):
    """Seed only 2 departments: Computer Applications (MCA) and Management (MMS)"""
    print("\n🏢 Seeding departments...")
    
    departments_data = [
        {"department_name": "Computer Applications", "dept_code": "MCA", "program_type": "pg", "hod_id": "HOD001"},
        {"department_name": "Management Studies", "dept_code": "MMS", "program_type": "pg", "hod_id": "HOD002"},
    ]
    
    departments = {}
    for d in departments_data:
        dept = Department.objects.create(
            institution=institution,
            **d
        )
        departments[d["dept_code"]] = dept
        print(f"   ✓ Created department: {dept.department_name} ({dept.dept_code})")
    
    return departments


def seed_admins(admin_users):
    """Seed admin profiles"""
    print("\n👔 Seeding admin profiles...")
    
    admin_names = ["Rajesh Kumar", "Priya Sharma"]
    
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
        # MCA Teachers
        {"teacher_id": "MCA001", "first_name": "Rajendra", "last_name": "Sharma", "designation": "Professor", "dept": "MCA"},
        {"teacher_id": "MCA002", "first_name": "Meera", "last_name": "Patel", "designation": "Associate Professor", "dept": "MCA"},
        {"teacher_id": "MCA003", "first_name": "Suresh", "last_name": "Desai", "designation": "Professor", "dept": "MCA"},
        {"teacher_id": "MCA004", "first_name": "Kavita", "last_name": "Mehta", "designation": "Assistant Professor", "dept": "MCA"},
        {"teacher_id": "MCA005", "first_name": "Lakshmi", "last_name": "Iyer", "designation": "Professor", "dept": "MCA"},
        {"teacher_id": "MCA006", "first_name": "Rahul", "last_name": "Gupta", "designation": "Associate Professor", "dept": "MCA"},
        # MMS Teachers
        {"teacher_id": "MMS001", "first_name": "Sanjay", "last_name": "Verma", "designation": "Professor", "dept": "MMS"},
        {"teacher_id": "MMS002", "first_name": "Deepa", "last_name": "Nair", "designation": "Associate Professor", "dept": "MMS"},
        {"teacher_id": "MMS003", "first_name": "Venkat", "last_name": "Rao", "designation": "Professor", "dept": "MMS"},
        {"teacher_id": "MMS004", "first_name": "Zara", "last_name": "Khan", "designation": "Assistant Professor", "dept": "MMS"},
        {"teacher_id": "MMS005", "first_name": "Manjeet", "last_name": "Singh", "designation": "Professor", "dept": "MMS"},
        {"teacher_id": "MMS006", "first_name": "Anita", "last_name": "Joshi", "designation": "Associate Professor", "dept": "MMS"},
    ]
    
    teachers = {"MCA": [], "MMS": []}
    for (user, dept_code), data in zip(faculty_users, teacher_data):
        teacher = Teacher.objects.create(
            teacher_id=data["teacher_id"],
            user=user,
            first_name=data["first_name"],
            last_name=data["last_name"],
            department=departments[data["dept"]],
            designation=data["designation"]
        )
        teachers[data["dept"]].append(teacher)
        print(f"   ✓ Created teacher: {data['first_name']} {data['last_name']} ({data['dept']})")
    
    return teachers


def seed_students(student_users, departments):
    """Seed student profiles"""
    print("\n👨‍🎓 Seeding student profiles...")
    
    middle_names = ["Kumar", "Raj", "Priya", "Devi", "Lal", "Chand", "Nath", "Das", "Mohan", "Ram", ""]
    
    students = {"MCA": {"2": [], "4": []}, "MMS": {"2": [], "4": []}}
    
    for s in student_users:
        student = Student.objects.create(
            user=s["user"],
            roll_no=s["roll_no"],
            first_name=s["first_name"],
            middle_name=random.choice(middle_names),
            last_name=s["last_name"],
            department=departments[s["dept"]],
            program=s["dept"],
            year_of_study=s["year"],
            semester=s["semester"]
        )
        students[s["dept"]][str(s["semester"])].append(student)
        print(f"   ✓ Created student: {s['roll_no']} - {s['first_name']} {s['last_name']} ({s['dept']} Year {s['year']})")
    
    print(f"\n   📋 Summary:")
    print(f"   ✓ MCA Year 1 (Sem 2): 60 students (Roll: MCA1001-MCA1060)")
    print(f"   ✓ MCA Year 2 (Sem 4): 60 students (Roll: MCA2001-MCA2060)")
    print(f"   ✓ MMS Year 1 (Sem 2): 60 students (Roll: MMS1001-MMS1060)")
    print(f"   ✓ MMS Year 2 (Sem 4): 60 students (Roll: MMS2001-MMS2060)")
    
    return students


def seed_courses(departments):
    """Seed courses/subjects for MCA and MMS"""
    print("\n📚 Seeding courses...")
    
    courses_data = [
        # MCA Semester 2 Subjects
        {"course_id": "MCA201", "course_name": "Data Structures & Algorithms", "credits": 4, "semester": 2, "dept": "MCA"},
        {"course_id": "MCA202", "course_name": "Database Management Systems", "credits": 4, "semester": 2, "dept": "MCA"},
        {"course_id": "MCA203", "course_name": "Object Oriented Programming with Java", "credits": 4, "semester": 2, "dept": "MCA"},
        {"course_id": "MCA204", "course_name": "Computer Networks", "credits": 3, "semester": 2, "dept": "MCA"},
        {"course_id": "MCA205", "course_name": "Web Technologies", "credits": 3, "semester": 2, "dept": "MCA"},
        {"course_id": "MCA206", "course_name": "Soft Skills & Communication", "credits": 2, "semester": 2, "dept": "MCA"},
        
        # MCA Semester 4 Subjects
        {"course_id": "MCA401", "course_name": "Machine Learning", "credits": 4, "semester": 4, "dept": "MCA"},
        {"course_id": "MCA402", "course_name": "Cloud Computing", "credits": 4, "semester": 4, "dept": "MCA"},
        {"course_id": "MCA403", "course_name": "Mobile Application Development", "credits": 4, "semester": 4, "dept": "MCA"},
        {"course_id": "MCA404", "course_name": "Information Security", "credits": 3, "semester": 4, "dept": "MCA"},
        {"course_id": "MCA405", "course_name": "Big Data Analytics", "credits": 3, "semester": 4, "dept": "MCA"},
        {"course_id": "MCA406", "course_name": "Project Work", "credits": 4, "semester": 4, "dept": "MCA"},
        
        # MMS Semester 2 Subjects
        {"course_id": "MMS201", "course_name": "Financial Management", "credits": 4, "semester": 2, "dept": "MMS"},
        {"course_id": "MMS202", "course_name": "Marketing Management", "credits": 4, "semester": 2, "dept": "MMS"},
        {"course_id": "MMS203", "course_name": "Human Resource Management", "credits": 4, "semester": 2, "dept": "MMS"},
        {"course_id": "MMS204", "course_name": "Operations Management", "credits": 3, "semester": 2, "dept": "MMS"},
        {"course_id": "MMS205", "course_name": "Business Communication", "credits": 3, "semester": 2, "dept": "MMS"},
        {"course_id": "MMS206", "course_name": "Managerial Economics", "credits": 2, "semester": 2, "dept": "MMS"},
        
        # MMS Semester 4 Subjects
        {"course_id": "MMS401", "course_name": "Strategic Management", "credits": 4, "semester": 4, "dept": "MMS"},
        {"course_id": "MMS402", "course_name": "International Business", "credits": 4, "semester": 4, "dept": "MMS"},
        {"course_id": "MMS403", "course_name": "Entrepreneurship Development", "credits": 4, "semester": 4, "dept": "MMS"},
        {"course_id": "MMS404", "course_name": "Business Analytics", "credits": 3, "semester": 4, "dept": "MMS"},
        {"course_id": "MMS405", "course_name": "Corporate Governance & Ethics", "credits": 3, "semester": 4, "dept": "MMS"},
        {"course_id": "MMS406", "course_name": "Summer Internship Project", "credits": 4, "semester": 4, "dept": "MMS"},
    ]
    
    courses = {"MCA": {"2": [], "4": []}, "MMS": {"2": [], "4": []}}
    
    for c in courses_data:
        course = Course.objects.create(
            course_id=c["course_id"],
            course_name=c["course_name"],
            credits=c["credits"],
            semester=c["semester"],
            department=departments[c["dept"]]
        )
        courses[c["dept"]][str(c["semester"])].append(course)
        print(f"   ✓ Created course: {course.course_id} - {course.course_name}")
    
    return courses


def seed_course_faculty(courses, teachers):
    """Assign teachers to courses"""
    print("\n👥 Seeding course-faculty assignments...")
    
    assignments = []
    
    # Assign MCA teachers to MCA courses
    mca_teachers = teachers["MCA"]
    for semester in ["2", "4"]:
        for i, course in enumerate(courses["MCA"][semester]):
            teacher = mca_teachers[i % len(mca_teachers)]
            cf = CourseFaculty.objects.create(course=course, teacher=teacher)
            assignments.append(cf)
    
    # Assign MMS teachers to MMS courses
    mms_teachers = teachers["MMS"]
    for semester in ["2", "4"]:
        for i, course in enumerate(courses["MMS"][semester]):
            teacher = mms_teachers[i % len(mms_teachers)]
            cf = CourseFaculty.objects.create(course=course, teacher=teacher)
            assignments.append(cf)
    
    print(f"   ✓ Created {len(assignments)} course-faculty assignments")
    return assignments


def seed_student_courses(students, courses):
    """Enroll students in their department's courses based on semester"""
    print("\n📖 Seeding student course enrollments...")
    
    enrollments = []
    academic_year = 2026
    
    # Enroll MCA students
    for semester in ["2", "4"]:
        semester_courses = courses["MCA"][semester]
        semester_students = students["MCA"][semester]
        
        for student in semester_students:
            for course in semester_courses:
                enrollment = StudentCourse.objects.create(
                    student=student,
                    course=course,
                    academic_year=academic_year,
                    semester=int(semester)
                )
                enrollments.append(enrollment)
    
    # Enroll MMS students
    for semester in ["2", "4"]:
        semester_courses = courses["MMS"][semester]
        semester_students = students["MMS"][semester]
        
        for student in semester_students:
            for course in semester_courses:
                enrollment = StudentCourse.objects.create(
                    student=student,
                    course=course,
                    academic_year=academic_year,
                    semester=int(semester)
                )
                enrollments.append(enrollment)
    
    print(f"   ✓ Created {len(enrollments)} student course enrollments")
    print(f"      - MCA Sem 2: 60 students × 6 courses = 360 enrollments")
    print(f"      - MCA Sem 4: 60 students × 6 courses = 360 enrollments")
    print(f"      - MMS Sem 2: 60 students × 6 courses = 360 enrollments")
    print(f"      - MMS Sem 4: 60 students × 6 courses = 360 enrollments")
    
    return enrollments


def seed_attendance(students, courses):
    """Seed attendance records for all students"""
    print("\n📋 Seeding attendance records...")
    
    statuses = ['present', 'present', 'present', 'present', 'present', 'absent', 'late']  # 70% present
    
    attendance_records = []
    start_date = date.today() - timedelta(days=45)  # Last 45 days
    
    # Generate attendance for each department and semester
    for dept in ["MCA", "MMS"]:
        for semester in ["2", "4"]:
            semester_students = students[dept][semester]
            semester_courses = courses[dept][semester]
            
            for course in semester_courses:
                # Generate 15 class sessions per course
                for day_offset in range(15):
                    class_date = start_date + timedelta(days=day_offset * 3)
                    if class_date.weekday() < 6:  # Monday to Saturday
                        for student in semester_students:
                            attendance = Attendance.objects.create(
                                student=student,
                                course=course,
                                date=class_date,
                                status=random.choice(statuses)
                            )
                            attendance_records.append(attendance)
    
    print(f"   ✓ Created {len(attendance_records)} attendance records")
    return attendance_records


def seed_assignments(courses, teachers):
    """Seed assignments for each course"""
    print("\n📝 Seeding assignments...")
    
    # Assignment templates per department
    mca_assignments = [
        ("Lab Exercise", "Complete the programming lab exercise"),
        ("Case Study", "Analyze the given case study and submit report"),
        ("Mini Project", "Develop a mini project as per specifications"),
        ("Quiz Preparation", "Prepare for upcoming quiz"),
        ("Research Paper Review", "Review and summarize the research paper"),
    ]
    
    mms_assignments = [
        ("Case Study Analysis", "Analyze the business case study"),
        ("Group Presentation", "Prepare group presentation on the topic"),
        ("Industry Report", "Submit industry analysis report"),
        ("Assignment", "Complete the assignment questions"),
        ("Field Survey", "Conduct and report field survey findings"),
    ]
    
    assignments = []
    
    # Create assignments for MCA courses
    for semester in ["2", "4"]:
        mca_teachers_list = teachers["MCA"]
        for course in courses["MCA"][semester]:
            # 3 assignments per course
            for i in range(3):
                title, desc = random.choice(mca_assignments)
                due_date = timezone.now() + timedelta(days=random.randint(7, 45))
                
                assignment = Assignment.objects.create(
                    course=course,
                    title=f"{title} - {course.course_name[:30]}",
                    description=f"{desc} for {course.course_name}. Submit before the deadline.",
                    due_date=due_date,
                    created_by=random.choice(mca_teachers_list)
                )
                assignments.append(assignment)
    
    # Create assignments for MMS courses
    for semester in ["2", "4"]:
        mms_teachers_list = teachers["MMS"]
        for course in courses["MMS"][semester]:
            # 3 assignments per course
            for i in range(3):
                title, desc = random.choice(mms_assignments)
                due_date = timezone.now() + timedelta(days=random.randint(7, 45))
                
                assignment = Assignment.objects.create(
                    course=course,
                    title=f"{title} - {course.course_name[:30]}",
                    description=f"{desc} for {course.course_name}. Submit before the deadline.",
                    due_date=due_date,
                    created_by=random.choice(mms_teachers_list)
                )
                assignments.append(assignment)
    
    print(f"   ✓ Created {len(assignments)} assignments (3 per course × 24 courses)")
    return assignments


def seed_assignment_submissions(assignments, students, courses):
    """Seed assignment submissions"""
    print("\n📤 Seeding assignment submissions...")
    
    submissions = []
    
    for assignment in assignments:
        course = assignment.course
        dept = "MCA" if course.course_id.startswith("MCA") else "MMS"
        semester = str(course.semester)
        
        # Get students enrolled in this course's semester
        semester_students = students[dept][semester]
        
        # 70-90% submission rate
        submission_rate = random.uniform(0.7, 0.9)
        submitting_students = random.sample(semester_students, int(len(semester_students) * submission_rate))
        
        for student in submitting_students:
            submitted_date = assignment.due_date.date() - timedelta(days=random.randint(0, 5))
            score = Decimal(str(random.uniform(60, 100))) if random.random() > 0.15 else None
            
            submission = AssignmentSubmission.objects.create(
                assignment=assignment,
                student=student,
                submitted_date=submitted_date,
                score=round(score, 2) if score else None
            )
            submissions.append(submission)
    
    print(f"   ✓ Created {len(submissions)} assignment submissions")
    return submissions


def seed_fee_structure(departments):
    """Seed fee structures"""
    print("\n💰 Seeding fee structures...")
    
    fee_structures = []
    
    for dept_code, dept in departments.items():
        fee = FeeStructure.objects.create(
            fee_id=f"FEE-{dept_code}-2026",
            department=dept,
            academic_year=2026,
            tution_fees=Decimal("75000.00"),
            development_fees=Decimal("15000.00")
        )
        fee_structures.append(fee)
        print(f"   ✓ Created fee structure for {dept_code}: ₹90,000")
    
    return fee_structures


def seed_student_fees(students, fee_structures):
    """Seed student fee payments"""
    print("\n💳 Seeding student fee payments...")
    
    statuses = ['paid', 'paid', 'paid', 'paid', 'partial', 'pending']  # Mostly paid
    
    student_fees = []
    
    for dept in ["MCA", "MMS"]:
        fee = [f for f in fee_structures if dept in f.fee_id][0]
        
        for semester in ["2", "4"]:
            for student in students[dept][semester]:
                status = random.choice(statuses)
                total = fee.amount
                
                if status == 'paid':
                    amount_paid = total
                    due_amount = Decimal('0.00')
                elif status == 'partial':
                    amount_paid = total * Decimal('0.5')
                    due_amount = total - amount_paid
                else:
                    amount_paid = Decimal('0.00')
                    due_amount = total
                
                # Generate receipt number and payment date for paid/partial
                payment_date = None
                receipt_number = ""
                description = f"{fee.department.department_name} Fees - AY {fee.academic_year}"
                
                if status in ['paid', 'partial']:
                    payment_date = date.today() - timedelta(days=random.randint(1, 60))
                    receipt_number = f"SIESCOMS/{fee.department.dept_code}/{fee.academic_year}-{fee.academic_year+1}/1/{random.randint(1,200)}"
                
                sf = StudentFees.objects.create(
                    student=student,
                    fee=fee,
                    amount_paid=round(amount_paid, 2),
                    due_amount=round(due_amount, 2),
                    status=status,
                    receipt_number=receipt_number,
                    payment_date=payment_date,
                    description=description
                )
                student_fees.append(sf)
    
    print(f"   ✓ Created {len(student_fees)} student fee records")
    return student_fees


def seed_exams(courses):
    """Seed exams for each course"""
    print("\n📋 Seeding exams...")
    
    exams = []
    exam_counter = 1
    
    for dept in ["MCA", "MMS"]:
        for semester in ["2", "4"]:
            for course in courses[dept][semester]:
                # Create midterm and final exam for each course
                for exam_type, marks in [("midterm", 30), ("final", 70)]:
                    exam_date = date.today() + timedelta(days=random.randint(30, 90))
                    
                    exam = Exam.objects.create(
                        exam_id=f"EXAM{exam_counter:04d}",
                        course=course,
                        exam_type=exam_type,
                        exam_date=exam_date,
                        total_marks=marks
                    )
                    exams.append(exam)
                    exam_counter += 1
    
    print(f"   ✓ Created {len(exams)} exams (2 per course)")
    return exams


def seed_results(exams, students, courses):
    """Seed exam results"""
    print("\n📊 Seeding exam results...")
    
    def calculate_grade(percentage):
        if percentage >= 90: return 'A+'
        elif percentage >= 80: return 'A'
        elif percentage >= 70: return 'B+'
        elif percentage >= 60: return 'B'
        elif percentage >= 50: return 'C+'
        elif percentage >= 40: return 'C'
        elif percentage >= 35: return 'D'
        else: return 'F'
    
    results = []
    
    for exam in exams:
        course = exam.course
        dept = "MCA" if course.course_id.startswith("MCA") else "MMS"
        semester = str(course.semester)
        
        semester_students = students[dept][semester]
        
        for student in semester_students:
            marks = Decimal(str(random.uniform(35, 100))) * exam.total_marks / 100
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


def run_seed():
    """Main function to run all seeders"""
    print("\n" + "="*60)
    print("🌱 STARTING DATABASE SEED PROCESS")
    print("   College ERP - MCA & MMS Setup")
    print("="*60)
    
    # Clear existing data
    clear_all_data()
    
    # Seed in order of dependencies
    seed_allowed_email_domains()
    admin_users, faculty_users, student_users = seed_users()
    
    institution = seed_institution()
    departments = seed_departments(institution)
    
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
    seed_assignment_submissions(assignments, students, courses)
    
    exams = seed_exams(courses)
    seed_results(exams, students, courses)
    
    print("\n" + "="*60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Print summary
    print("\n📊 SUMMARY:")
    print(f"   • Allowed Email Domains: {AllowedEmailDomain.objects.count()}")
    print(f"   • Users: {User.objects.count()}")
    print(f"   • Institution: {Institution.objects.count()}")
    print(f"   • Departments: {Department.objects.count()} (MCA, MMS)")
    print(f"   • Admins: {Admin.objects.count()}")
    print(f"   • Teachers: {Teacher.objects.count()} (6 MCA + 6 MMS)")
    print(f"   • Students: {Student.objects.count()} (60 per dept per year)")
    print(f"   • Courses: {Course.objects.count()} (6 per semester × 2 depts × 2 sems)")
    print(f"   • Course-Faculty: {CourseFaculty.objects.count()}")
    print(f"   • Student Enrollments: {StudentCourse.objects.count()}")
    print(f"   • Attendance Records: {Attendance.objects.count()}")
    print(f"   • Fee Structures: {FeeStructure.objects.count()}")
    print(f"   • Student Fees: {StudentFees.objects.count()}")
    print(f"   • Assignments: {Assignment.objects.count()}")
    print(f"   • Submissions: {AssignmentSubmission.objects.count()}")
    print(f"   • Exams: {Exam.objects.count()}")
    print(f"   • Results: {Result.objects.count()}")
    
    print("\n📌 LOGIN CREDENTIALS:")
    print("   Admin:   admin@sies.edu.in / admin123")
    print("   Faculty: dr.sharma@sies.edu.in / faculty123 (MCA)")
    print("   Faculty: dr.verma@sies.edu.in / faculty123 (MMS)")
    print("   Student: Check student emails in database / student123")
    print("")


if __name__ == '__main__':
    run_seed()
