from saara.erp.models import Attendance, Course, Student
from django.db.models import Count, Q


class AttendanceAgent:
    """Agent to handle attendance-related queries"""
    
    def __init__(self, student):
        """
        Initialize with student instance
        Args:
            student: Student model instance
        """
        self.student = student

    def get_attendance(self, course_id: str = None):
        """
        Get attendance details for the student
        Args:
            course_id: Optional course ID to filter by
        Returns:
            Dictionary with attendance data
        """
        query = Attendance.objects.filter(student=self.student)

        if course_id:
            # Try to find course by name or ID
            try:
                course = Course.objects.filter(
                    Q(course_name__icontains=course_id) | 
                    Q(course_id__icontains=course_id)
                ).first()
                if course:
                    query = query.filter(course=course)
                else:
                    return {"error": f"Course '{course_id}' not found."}
            except Exception:
                return {"error": f"Invalid course identifier: {course_id}"}

        records = query.all()
        
        if not records:
            return {"error": "No attendance records found."}

        total = len(records)
        present = sum(1 for r in records if r.status == "present")
        late = sum(1 for r in records if r.status == "late")
        absent = sum(1 for r in records if r.status == "absent")
        excused = sum(1 for r in records if r.status == "excused")
        
        # Consider present and late as attended
        attended = present + late
        percentage = (attended / total) * 100 if total > 0 else 0

        # Get course-wise breakdown if no specific course requested
        course_breakdown = []
        if not course_id:
            courses = Attendance.objects.filter(student=self.student).values('course').distinct()
            for course_entry in courses:
                course_obj = Course.objects.filter(course_id=course_entry['course']).first()
                if course_obj:
                    course_records = query.filter(course=course_obj)
                    course_total = course_records.count()
                    course_present = course_records.filter(
                        Q(status='present') | Q(status='late')
                    ).count()
                    course_percentage = (course_present / course_total) * 100 if course_total > 0 else 0
                    course_breakdown.append({
                        "course_name": course_obj.course_name,
                        "total_classes": course_total,
                        "attended": course_present,
                        "percentage": round(course_percentage, 2)
                    })

        result = {
            "student_name": f"{self.student.first_name} {self.student.last_name}",
            "total_classes": total,
            "present": present,
            "late": late,
            "absent": absent,
            "excused": excused,
            "attendance_percentage": round(percentage, 2)
        }
        
        if course_breakdown:
            result["course_breakdown"] = course_breakdown
            
        return result
