from saara.erp.models import (
    Attendance, Course, Student, CourseFaculty, 
    Assignment, AssignmentSubmission, Result, Exam
)
from django.db.models import Count, Q, Avg


class TeacherAttendanceAgent:
    """Agent to handle attendance-related queries for teachers"""
    
    def __init__(self, teacher):
        self.teacher = teacher

    def get_attendance(self, course_id: str = None, student_id: str = None):
        """
        Get attendance details for teacher's courses
        """
        # Get courses taught by this teacher
        teacher_courses = CourseFaculty.objects.filter(
            teacher=self.teacher
        ).values_list('course', flat=True)
        
        if not teacher_courses:
            return {"error": "You are not assigned to any courses."}
        
        query = Attendance.objects.filter(course__in=teacher_courses)
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                if course.course_id not in teacher_courses:
                    return {"error": f"You are not assigned to course '{course_id}'."}
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}

        records = query.all()
        
        if not records:
            return {"error": "No attendance records found."}

        # Get course-wise summary
        courses = Course.objects.filter(course_id__in=teacher_courses)
        course_summary = []
        
        for course in courses:
            if course_id and course_id.lower() not in course.course_name.lower():
                continue
                
            course_records = Attendance.objects.filter(course=course)
            total_records = course_records.count()
            if total_records == 0:
                continue
                
            present_count = course_records.filter(
                Q(status='present') | Q(status='late')
            ).count()
            
            avg_attendance = (present_count / total_records) * 100 if total_records > 0 else 0
            
            # Get student count
            student_count = course_records.values('student').distinct().count()
            
            course_summary.append({
                "course_name": course.course_name,
                "total_students": student_count,
                "total_records": total_records,
                "average_attendance": round(avg_attendance, 2)
            })

        return {
            "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
            "courses_taught": len(course_summary),
            "course_summary": course_summary
        }


class TeacherAssignmentAgent:
    """Agent to handle assignment-related queries for teachers"""
    
    def __init__(self, teacher):
        self.teacher = teacher

    def get_assignments(self, course_id: str = None):
        """
        Get assignment details for teacher's courses
        """
        query = Assignment.objects.filter(created_by=self.teacher)
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}

        assignments = query.select_related('course').all()
        
        if not assignments:
            return {"error": "No assignments found."}

        result = []
        for assignment in assignments:
            # Get submission stats
            total_submissions = AssignmentSubmission.objects.filter(
                assignment=assignment
            ).count()
            
            graded_submissions = AssignmentSubmission.objects.filter(
                assignment=assignment,
                score__isnull=False
            ).count()
            
            result.append({
                "title": assignment.title,
                "course_name": assignment.course.course_name,
                "due_date": assignment.due_date.strftime("%Y-%m-%d %H:%M"),
                "total_submissions": total_submissions,
                "graded": graded_submissions,
                "pending_grading": total_submissions - graded_submissions
            })

        return {
            "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
            "total_assignments": len(result),
            "assignments": result
        }


class TeacherResultsAgent:
    """Agent to handle results-related queries for teachers"""
    
    def __init__(self, teacher):
        self.teacher = teacher

    def get_results(self, course_id: str = None, exam_type: str = None):
        """
        Get exam results for teacher's courses
        """
        # Get courses taught by this teacher
        teacher_courses = CourseFaculty.objects.filter(
            teacher=self.teacher
        ).values_list('course', flat=True)
        
        if not teacher_courses:
            return {"error": "You are not assigned to any courses."}
        
        query = Exam.objects.filter(course__in=teacher_courses)
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if exam_type:
            query = query.filter(exam_type__iexact=exam_type)

        exams = query.select_related('course').all()
        
        if not exams:
            return {"error": "No exams found."}

        result = []
        for exam in exams:
            results = Result.objects.filter(exam=exam)
            total_students = results.count()
            
            if total_students > 0:
                avg_marks = results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
                pass_count = results.filter(marks_obtained__gte=exam.total_marks * 0.4).count()
                pass_percentage = (pass_count / total_students) * 100
            else:
                avg_marks = 0
                pass_percentage = 0
            
            result.append({
                "course_name": exam.course.course_name,
                "exam_type": exam.exam_type,
                "exam_date": exam.exam_date.strftime("%Y-%m-%d"),
                "total_marks": exam.total_marks,
                "students_appeared": total_students,
                "average_marks": round(avg_marks, 2),
                "pass_percentage": round(pass_percentage, 2)
            })

        return {
            "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
            "total_exams": len(result),
            "exam_results": result
        }
