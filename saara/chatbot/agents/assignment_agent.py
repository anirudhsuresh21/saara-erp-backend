from saara.erp.models import Assignment, AssignmentSubmission, Course, Student
from django.db.models import Q
from django.utils import timezone
from datetime import date


class AssignmentAgent:
    """Agent to handle assignment-related queries"""
    
    def __init__(self, student):
        """
        Initialize with student instance
        Args:
            student: Student model instance
        """
        self.student = student

    def get_assignments(self, course_id: str = None):
        """
        Get assignment details for the student
        Args:
            course_id: Optional course ID to filter by
        Returns:
            Dictionary with assignment data
        """
        # Get courses for student's semester and department
        student_courses = Course.objects.filter(
            semester=self.student.semester,
            department=self.student.department
        )
        
        query = Assignment.objects.filter(course__in=student_courses)
        
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

        assignments = query.select_related('course', 'created_by').all()
        
        if not assignments:
            return {"error": "No assignments found."}

        result = []
        pending_count = 0
        submitted_count = 0
        overdue_count = 0
        today = timezone.now()

        for assignment in assignments:
            # Check if student has submitted
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=self.student
            ).first()

            is_submitted = submission is not None
            is_overdue = assignment.due_date < today and not is_submitted
            
            if is_submitted:
                submitted_count += 1
            else:
                pending_count += 1
                if is_overdue:
                    overdue_count += 1

            assignment_data = {
                "assignment_id": str(assignment.assignments_id),
                "course_name": assignment.course.course_name,
                "title": assignment.title,
                "description": assignment.description,
                "file_url": assignment.file_url,
                "due_date": assignment.due_date.strftime("%Y-%m-%d %H:%M"),
                "created_by": f"{assignment.created_by.first_name} {assignment.created_by.last_name}",
                "status": "Submitted" if is_submitted else ("Overdue" if is_overdue else "Pending"),
                "overdue": is_overdue,
            }
            
            if submission:
                assignment_data["submitted_date"] = submission.submitted_date.strftime("%Y-%m-%d") if submission.submitted_date else None
                assignment_data["score"] = float(submission.score) if submission.score else None
            
            result.append(assignment_data)

        return {
            "student_name": f"{self.student.first_name} {self.student.last_name}",
            "total_assignments": len(result),
            "pending_assignments": pending_count,
            "submitted_assignments": submitted_count,
            "overdue_assignments": overdue_count,
            "assignments": result
        }
