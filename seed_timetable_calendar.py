"""
Seed script for Timetable and Academic Calendar data
"""
import os
import sys
import django
from datetime import datetime, time, date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')
django.setup()

from saara.erp.models import Course, Teacher, Department, Timetable, AcademicCalendar, Announcement
from saara.authapp.models import User

def seed_timetable():
    """Create timetable entries for courses"""
    print("Seeding Timetable data...")
    
    # Clear existing data
    Timetable.objects.all().delete()
    
    # Get courses and teachers
    courses = Course.objects.all()
    teachers = Teacher.objects.all()
    
    if not courses.exists():
        print("No courses found! Please run seed_data.py first.")
        return
    
    if not teachers.exists():
        print("No teachers found! Please run seed_data.py first.")
        return
    
    # Time slots
    time_slots = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 15), time(12, 15)),
        (time(12, 15), time(13, 15)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    rooms = ['101', '102', '103', '201', '202', '203', 'Lab-1', 'Lab-2']
    
    teacher_list = list(teachers)
    room_idx = 0
    
    for i, course in enumerate(courses):
        # Assign a teacher to each course
        teacher = teacher_list[i % len(teacher_list)]
        
        # Schedule 3 sessions per week for each course
        for j, day in enumerate(days[:3]):  # Mon, Tue, Wed
            slot_idx = (i + j) % len(time_slots)
            start_time, end_time = time_slots[slot_idx]
            
            Timetable.objects.create(
                course=course,
                teacher=teacher,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                room_number=rooms[room_idx % len(rooms)],
                is_active=True
            )
            room_idx += 1
    
    print(f"Created {Timetable.objects.count()} timetable entries")


def seed_academic_calendar():
    """Create academic calendar events"""
    print("Seeding Academic Calendar data...")
    
    # Clear existing data
    AcademicCalendar.objects.all().delete()
    
    today = date.today()
    current_year = today.year
    
    # Exam schedules
    exams = [
        ("Mid-Semester Examinations", today + timedelta(days=30), today + timedelta(days=37)),
        ("End-Semester Examinations", today + timedelta(days=90), today + timedelta(days=104)),
        ("Internal Assessment 1", today + timedelta(days=15), None),
        ("Internal Assessment 2", today + timedelta(days=45), None),
        ("Practical Examinations", today + timedelta(days=85), today + timedelta(days=89)),
    ]
    
    for title, start, end in exams:
        AcademicCalendar.objects.create(
            title=title,
            description=f"Scheduled {title.lower()} for all departments",
            event_type='exam',
            start_date=start,
            end_date=end,
            is_active=True
        )
    
    # Holidays
    holidays = [
        ("Republic Day", date(current_year, 1, 26), None),
        ("Holi", date(current_year, 3, 25), None),
        ("Good Friday", date(current_year, 4, 18), None),
        ("Independence Day", date(current_year, 8, 15), None),
        ("Ganesh Chaturthi", date(current_year, 9, 7), date(current_year, 9, 12)),
        ("Dussehra", date(current_year, 10, 12), None),
        ("Diwali Break", date(current_year, 10, 31), date(current_year, 11, 5)),
        ("Christmas Break", date(current_year, 12, 25), date(current_year, 12, 31)),
    ]
    
    for title, start, end in holidays:
        AcademicCalendar.objects.create(
            title=title,
            description=f"{title} - Holiday",
            event_type='holiday',
            start_date=start,
            end_date=end,
            is_active=True
        )
    
    # Deadlines
    deadlines = [
        ("Assignment Submission Deadline - Module 1", today + timedelta(days=10)),
        ("Project Proposal Submission", today + timedelta(days=20)),
        ("Fee Payment Last Date", today + timedelta(days=7)),
        ("Scholarship Application Deadline", today + timedelta(days=25)),
        ("Final Project Submission", today + timedelta(days=75)),
    ]
    
    for title, deadline_date in deadlines:
        AcademicCalendar.objects.create(
            title=title,
            description=f"Last date: {deadline_date.strftime('%B %d, %Y')}",
            event_type='deadline',
            start_date=deadline_date,
            end_date=None,
            is_active=True
        )
    
    # Events
    events = [
        ("College Annual Day", today + timedelta(days=60), None, "Annual celebration with cultural programs"),
        ("Tech Fest 2025", today + timedelta(days=40), today + timedelta(days=42), "Three-day technology festival"),
        ("Alumni Meet", today + timedelta(days=55), None, "Annual alumni gathering"),
        ("Placement Drive - TCS", today + timedelta(days=35), None, "Campus recruitment drive"),
        ("Guest Lecture - AI/ML", today + timedelta(days=12), None, "Industry expert lecture on AI trends"),
    ]
    
    for title, start, end, desc in events:
        AcademicCalendar.objects.create(
            title=title,
            description=desc,
            event_type='event',
            start_date=start,
            end_date=end,
            is_active=True
        )
    
    print(f"Created {AcademicCalendar.objects.count()} calendar events")


def seed_announcements():
    """Create sample announcements"""
    print("Seeding Announcements...")
    
    # Check if announcements already exist
    if Announcement.objects.count() > 5:
        print(f"Announcements already exist ({Announcement.objects.count()}). Skipping...")
        return
    
    # Get admin user for created_by
    admin_user = User.objects.filter(role='admin').first()
    
    announcements_data = [
        {
            'title': 'Mid-Semester Examination Schedule Released',
            'content': 'The mid-semester examination schedule has been released. Please check the academic calendar for detailed timings. Examination will start from next month. Students are advised to prepare accordingly.',
            'target_audience': 'students',
        },
        {
            'title': 'Library Extended Hours',
            'content': 'The college library will remain open till 9 PM during the examination period. Students are encouraged to utilize this facility for their exam preparation.',
            'target_audience': 'all',
        },
        {
            'title': 'Faculty Meeting - Curriculum Review',
            'content': 'All faculty members are requested to attend the curriculum review meeting scheduled for next Friday at 3 PM in the Conference Hall.',
            'target_audience': 'teachers',
        },
        {
            'title': 'Placement Drive Announcement',
            'content': 'TCS will be conducting a campus recruitment drive next month. Eligible students are requested to register on the placement portal by end of this week.',
            'target_audience': 'students',
        },
        {
            'title': 'New Computer Lab Inauguration',
            'content': 'A new state-of-the-art computer lab has been inaugurated in Block C. The lab is equipped with high-performance workstations and is available for all students.',
            'target_audience': 'all',
        },
    ]
    
    for data in announcements_data:
        Announcement.objects.create(
            title=data['title'],
            content=data['content'],
            target_audience=data['target_audience'],
            created_by=admin_user,
            is_active=True
        )
    
    print(f"Created {len(announcements_data)} announcements")


if __name__ == '__main__':
    print("=" * 50)
    print("Seeding Timetable, Academic Calendar & Announcements")
    print("=" * 50)
    
    seed_timetable()
    seed_academic_calendar()
    seed_announcements()
    
    print("\n✅ Seeding completed successfully!")
