"""
General agents for timetable, announcements, academic calendar, and leave requests
These are available to all user types (students, teachers, admins)
"""

from saara.erp.models import (
    Course, Student, Teacher, Department, StudentCourse,
    Announcement, Timetable, AcademicCalendar, LeaveRequest
)
from saara.authapp.models import User
from django.db.models import Q
from datetime import datetime, date, timedelta


class TimetableAgent:
    """Agent to handle timetable/schedule queries"""
    
    def __init__(self, user, profile=None, role=None):
        self.user = user
        self.profile = profile
        self.role = role
    
    def get_timetable(self, day=None):
        """
        Get timetable for the user
        - Students: Get timetable for enrolled courses
        - Teachers: Get timetable for courses they teach
        """
        today = date.today()
        day_of_week = day or today.strftime('%A').lower()
        
        if self.role == 'student' and self.profile:
            # Get student's enrolled courses
            enrollments = StudentCourse.objects.filter(student=self.profile).select_related('course')
            course_ids = [e.course.course_id for e in enrollments]
            
            slots = Timetable.objects.filter(
                course__course_id__in=course_ids,
                day_of_week=day_of_week,
                is_active=True
            ).select_related('course', 'teacher').order_by('start_time')
            
        elif self.role == 'teacher' and self.profile:
            slots = Timetable.objects.filter(
                teacher=self.profile,
                day_of_week=day_of_week,
                is_active=True
            ).select_related('course').order_by('start_time')
            
        else:
            # Admin - show all
            slots = Timetable.objects.filter(
                day_of_week=day_of_week,
                is_active=True
            ).select_related('course', 'teacher').order_by('start_time')[:20]
        
        if not slots.exists():
            return {
                "success": True,
                "day": day_of_week.title(),
                "slots": [],
                "message": f"No classes scheduled for {day_of_week.title()}."
            }
        
        return {
            "success": True,
            "day": day_of_week.title(),
            "slots": [
                {
                    "course": slot.course.course_name,
                    "course_id": slot.course.course_id,
                    "time": f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}",
                    "room": slot.room_number or "TBA",
                    "teacher": f"{slot.teacher.first_name} {slot.teacher.last_name}" if slot.teacher else "TBA"
                }
                for slot in slots
            ]
        }
    
    def get_weekly_schedule(self):
        """Get the entire week's schedule"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        weekly = {}
        
        for day in days:
            result = self.get_timetable(day)
            if result.get('slots'):
                weekly[day.title()] = result['slots']
        
        return {
            "success": True,
            "weekly_schedule": weekly
        }


class AnnouncementAgent:
    """Agent to handle announcement queries"""
    
    def __init__(self, user, profile=None, role=None):
        self.user = user
        self.profile = profile
        self.role = role
    
    def get_announcements(self, limit=10):
        """Get relevant announcements for the user"""
        query = Announcement.objects.filter(is_active=True)
        
        # Filter by target audience
        if self.role == 'student':
            query = query.filter(
                Q(target_audience='all') | Q(target_audience='students')
            )
            # Also filter by department if student has one
            if self.profile and self.profile.department:
                query = query.filter(
                    Q(department__isnull=True) | Q(department=self.profile.department)
                )
        elif self.role == 'teacher':
            query = query.filter(
                Q(target_audience='all') | Q(target_audience='teachers')
            )
            if self.profile and self.profile.department:
                query = query.filter(
                    Q(department__isnull=True) | Q(department=self.profile.department)
                )
        # Admins see all
        
        announcements = query.order_by('-created_at')[:limit]
        
        if not announcements:
            return {
                "success": True,
                "announcements": [],
                "message": "No announcements found."
            }
        
        return {
            "success": True,
            "count": announcements.count(),
            "announcements": [
                {
                    "title": a.title,
                    "content": a.content[:200] + "..." if len(a.content) > 200 else a.content,
                    "date": a.created_at.strftime('%b %d, %Y'),
                    "target": a.get_target_audience_display(),
                    "posted_by": a.created_by.email.split('@')[0] if a.created_by else "Admin"
                }
                for a in announcements
            ]
        }


class AcademicCalendarAgent:
    """Agent to handle academic calendar queries"""
    
    def __init__(self, user, profile=None, role=None):
        self.user = user
        self.profile = profile
        self.role = role
    
    def get_events(self, event_type=None, upcoming_only=True):
        """Get academic calendar events"""
        query = AcademicCalendar.objects.filter(is_active=True)
        
        if upcoming_only:
            query = query.filter(start_date__gte=date.today())
        
        if event_type:
            query = query.filter(event_type=event_type)
        
        # Filter by department if user has one
        if self.profile and hasattr(self.profile, 'department') and self.profile.department:
            query = query.filter(
                Q(department__isnull=True) | Q(department=self.profile.department)
            )
        
        events = query.order_by('start_date')[:20]
        
        if not events:
            return {
                "success": True,
                "events": [],
                "message": "No upcoming events found."
            }
        
        return {
            "success": True,
            "count": events.count(),
            "events": [
                {
                    "title": e.title,
                    "description": e.description,
                    "event_type": e.event_type,
                    "type_display": e.get_event_type_display(),
                    "start_date": e.start_date.strftime('%b %d, %Y'),
                    "end_date": e.end_date.strftime('%b %d, %Y') if e.end_date else None
                }
                for e in events
            ]
        }
    
    def get_exam_schedule(self):
        """Get upcoming exams"""
        return self.get_events(event_type='exam')
    
    def get_holidays(self):
        """Get upcoming holidays"""
        return self.get_events(event_type='holiday')


class LeaveAgent:
    """Agent to handle leave requests"""
    
    def __init__(self, user, profile=None, role=None):
        self.user = user
        self.profile = profile
        self.role = role
    
    def apply_leave(self, leave_type: str, start_date: str, end_date: str = None, reason: str = ""):
        """Apply for leave"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else start
        except ValueError:
            return {
                "success": False,
                "error": "Invalid date format. Please use YYYY-MM-DD format."
            }
        
        # Validate dates
        if start < date.today():
            return {
                "success": False,
                "error": "Cannot apply for leave in the past."
            }
        
        if end < start:
            return {
                "success": False,
                "error": "End date cannot be before start date."
            }
        
        # Check for overlapping leaves
        existing = LeaveRequest.objects.filter(
            user=self.user,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exists()
        
        if existing:
            return {
                "success": False,
                "error": "You already have a leave request for overlapping dates."
            }
        
        try:
            leave = LeaveRequest.objects.create(
                user=self.user,
                leave_type=leave_type,
                start_date=start,
                end_date=end,
                reason=reason or f"{leave_type.title()} leave request"
            )
            
            days = (end - start).days + 1
            
            return {
                "success": True,
                "message": "Leave request submitted successfully!",
                "leave_id": str(leave.leave_id),
                "leave_type": leave.get_leave_type_display(),
                "start_date": start.strftime('%b %d, %Y'),
                "end_date": end.strftime('%b %d, %Y'),
                "days": days,
                "status": "Pending",
                "reason": reason or ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to submit leave request: {str(e)}"
            }
    
    def get_leave_status(self):
        """Get status of leave requests"""
        leaves = LeaveRequest.objects.filter(user=self.user).order_by('-created_at')[:10]
        
        if not leaves:
            return {
                "success": True,
                "leaves": [],
                "message": "No leave requests found."
            }
        
        return {
            "success": True,
            "count": leaves.count(),
            "leaves": [
                {
                    "leave_type": l.get_leave_type_display(),
                    "start_date": l.start_date.strftime('%b %d, %Y'),
                    "end_date": l.end_date.strftime('%b %d, %Y'),
                    "days": (l.end_date - l.start_date).days + 1,
                    "status": l.status,
                    "reason": l.reason[:50] + "..." if len(l.reason) > 50 else l.reason
                }
                for l in leaves
            ]
        }
