"""
Seed Attendance and Announcements
Adds attendance records and announcements to existing data
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')
django.setup()

import random
from datetime import date, timedelta
from django.utils import timezone

from saara.erp.models import (
    Student, Course, StudentCourse, Attendance, Announcement, 
    Department, User
)


def seed_attendance():
    """Create attendance records for all students in their enrolled courses"""
    print("\n📋 Seeding attendance records...")
    
    # Delete existing attendance
    Attendance.objects.all().delete()
    
    attendance_records = []
    statuses = ['present', 'present', 'present', 'present', 'absent', 'late']  # 66% present
    
    # Get all students
    students = Student.objects.all()
    
    # Generate attendance for past 30 days
    start_date = date.today() - timedelta(days=30)
    
    for student in students:
        # Get courses this student is enrolled in
        enrollments = StudentCourse.objects.filter(
            student=student,
            academic_year=2026,
            semester=1
        ).select_related('course')
        
        enrolled_courses = [enrollment.course for enrollment in enrollments]
        
        if not enrolled_courses:
            continue
        
        # Create attendance for each enrolled course
        for course in enrolled_courses:
            # Generate attendance for ~15 class days (every 2 days)
            for i in range(15):
                class_date = start_date + timedelta(days=i * 2)
                
                # Only weekdays
                if class_date.weekday() < 5:
                    try:
                        attendance = Attendance.objects.create(
                            student=student,
                            course=course,
                            date=class_date,
                            status=random.choice(statuses)
                        )
                        attendance_records.append(attendance)
                    except:
                        # Skip if duplicate (unique constraint)
                        pass
    
    print(f"   ✓ Created {len(attendance_records)} attendance records")
    return attendance_records


def seed_announcements():
    """Create announcements for departments and courses"""
    print("\n📢 Seeding announcements...")
    
    # Delete existing announcements
    Announcement.objects.all().delete()
    
    announcements = []
    
    # Get departments and courses
    mms_dept = Department.objects.filter(dept_code='MMS').first()
    mca_dept = Department.objects.filter(dept_code='MCA').first()
    
    # Get admin and faculty users
    admin_users = User.objects.filter(role='admin')
    faculty_users = User.objects.filter(role='faculty')
    
    if not admin_users.exists():
        print("   ⚠️ No admin users found. Skipping announcements.")
        return []
    
    # General announcements
    general_announcements = [
        {
            "title": "Welcome to Academic Year 2026",
            "content": "Welcome to SIES College! We wish all students a successful academic year. Please ensure you attend all classes regularly and participate actively.",
            "target_audience": "all"
        },
        {
            "title": "Library Timings Update",
            "content": "The library will be open from 8 AM to 8 PM on weekdays and 9 AM to 5 PM on Saturdays. Sunday closed.",
            "target_audience": "students"
        },
        {
            "title": "Faculty Meeting",
            "content": "All faculty members are requested to attend the department meeting on Monday at 3 PM in the conference room.",
            "target_audience": "teachers"
        },
    ]
    
    # MMS specific announcements
    mms_announcements = [
        {
            "title": "MMS Orientation Program",
            "content": "Orientation program for MMS Semester 1 students will be conducted on January 10th, 2026 at 10 AM in the auditorium.",
            "target_audience": "department",
            "department": mms_dept
        },
        {
            "title": "MMS Industry Visit",
            "content": "An industry visit has been organized for MMS students to a leading manufacturing company. Registration open.",
            "target_audience": "department",
            "department": mms_dept
        },
    ]
    
    # MCA specific announcements
    mca_announcements = [
        {
            "title": "MCA Lab Schedule",
            "content": "Lab sessions for MCA Semester 1 will begin from January 8th. Check your timetable for allocated slots.",
            "target_audience": "department",
            "department": mca_dept
        },
        {
            "title": "Coding Competition",
            "content": "Inter-college coding competition will be held on January 20th. Interested students can register at the MCA office.",
            "target_audience": "department",
            "department": mca_dept
        },
    ]
    
    # Course-specific announcements
    mca_courses = Course.objects.filter(department=mca_dept)[:3]
    course_announcements = []
    
    if mca_courses.exists():
        course_announcements = [
            {
                "title": f"Assignment Due - {mca_courses[0].course_name}",
                "content": f"Assignment for {mca_courses[0].course_name} is due on January 15th. Please submit before the deadline.",
                "target_audience": "course",
                "course": mca_courses[0]
            },
            {
                "title": f"Extra Class - {mca_courses[1].course_name}",
                "content": f"An extra class for {mca_courses[1].course_name} will be conducted on Saturday at 11 AM.",
                "target_audience": "course",
                "course": mca_courses[1]
            },
        ]
    
    # Create general announcements
    admin_user = admin_users.first()
    for ann_data in general_announcements:
        announcement = Announcement.objects.create(
            title=ann_data["title"],
            content=ann_data["content"],
            created_by=admin_user,
            target_audience=ann_data["target_audience"],
            is_active=True
        )
        announcements.append(announcement)
    
    # Create department-specific announcements
    for ann_data in mms_announcements + mca_announcements:
        announcement = Announcement.objects.create(
            title=ann_data["title"],
            content=ann_data["content"],
            created_by=admin_user,
            target_audience=ann_data["target_audience"],
            department=ann_data.get("department"),
            is_active=True
        )
        announcements.append(announcement)
    
    # Create course-specific announcements
    if faculty_users.exists():
        faculty_user = faculty_users.first()
        for ann_data in course_announcements:
            announcement = Announcement.objects.create(
                title=ann_data["title"],
                content=ann_data["content"],
                created_by=faculty_user,
                target_audience=ann_data["target_audience"],
                course=ann_data.get("course"),
                is_active=True
            )
            announcements.append(announcement)
    
    print(f"   ✓ Created {len(announcements)} announcements")
    return announcements


def run():
    """Main function"""
    print("\n" + "="*70)
    print("🌱 SEEDING ATTENDANCE & ANNOUNCEMENTS")
    print("="*70)
    
    # Seed attendance
    attendance_records = seed_attendance()
    
    # Seed announcements
    announcements = seed_announcements()
    
    print("\n" + "="*70)
    print("✅ SEED COMPLETED!")
    print("="*70)
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"   • Attendance Records: {Attendance.objects.count()}")
    print(f"   • Announcements: {Announcement.objects.count()}")
    print(f"   • Students with Attendance: {Student.objects.filter(attendance_records__isnull=False).distinct().count()}")
    print()


if __name__ == '__main__':
    run()
