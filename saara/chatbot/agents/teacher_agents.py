from saara.erp.models import (
    Attendance, Course, Student, CourseFaculty, StudentCourse,
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

    def get_low_attendance_students(self, threshold: int = 75, course_id: str = None):
        """
        Get students with attendance below a specified threshold.
        
        Args:
            threshold: Attendance percentage threshold (default 75%)
            course_id: Optional course ID/name to filter by
        
        Returns:
            Dictionary with students who have attendance below threshold
        """
        # Get courses taught by this teacher
        teacher_courses = CourseFaculty.objects.filter(
            teacher=self.teacher
        ).values_list('course', flat=True)
        
        if not teacher_courses:
            return {"error": "You are not assigned to any courses."}
        
        courses = Course.objects.filter(course_id__in=teacher_courses)
        
        if course_id:
            courses = courses.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            )
        
        if not courses.exists():
            return {"error": f"Course '{course_id}' not found or you are not assigned to it."}
        
        low_attendance_data = []
        
        for course in courses:
            # Get all students enrolled in this course
            student_enrollments = StudentCourse.objects.filter(
                course=course
            ).select_related('student')
            
            students_below_threshold = []
            
            for enrollment in student_enrollments:
                student = enrollment.student
                
                # Calculate attendance for this student in this course
                attendance_records = Attendance.objects.filter(
                    student=student,
                    course=course
                )
                
                total_classes = attendance_records.count()
                if total_classes == 0:
                    continue
                
                present_count = attendance_records.filter(
                    Q(status='present') | Q(status='late')
                ).count()
                
                attendance_percentage = (present_count / total_classes) * 100
                
                if attendance_percentage < threshold:
                    students_below_threshold.append({
                        "name": f"{student.first_name} {student.last_name}",
                        "roll_no": student.roll_no or str(student.student_id)[:8],
                        "attendance_percentage": round(attendance_percentage, 2),
                        "present": present_count,
                        "total": total_classes,
                        "absent": total_classes - present_count
                    })
            
            if students_below_threshold:
                # Sort by attendance percentage (lowest first)
                students_below_threshold.sort(key=lambda x: x['attendance_percentage'])
                
                low_attendance_data.append({
                    "course_name": course.course_name,
                    "course_id": course.course_id,
                    "threshold": threshold,
                    "students_count": len(students_below_threshold),
                    "students": students_below_threshold
                })
        
        if not low_attendance_data:
            return {
                "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
                "threshold": threshold,
                "message": f"Great news! No students have attendance below {threshold}% in your courses.",
                "courses_summary": []
            }
        
        total_students_below = sum(c['students_count'] for c in low_attendance_data)
        
        return {
            "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
            "threshold": threshold,
            "total_students_below_threshold": total_students_below,
            "courses_summary": low_attendance_data
        }


class TeacherAssignmentAgent:
    """Agent to handle assignment-related queries for teachers"""
    
    def __init__(self, teacher):
        self.teacher = teacher

    def get_assignments(self, course_id: str = None):
        """
        Get assignment details for teacher's courses including pending students
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
            # Get students enrolled in this course
            enrolled_students = StudentCourse.objects.filter(
                course=assignment.course
            ).select_related('student')
            
            # Get students who have submitted
            submitted_student_ids = AssignmentSubmission.objects.filter(
                assignment=assignment
            ).values_list('student_id', flat=True)
            
            # Find students who haven't submitted
            pending_students = []
            for enrollment in enrolled_students:
                if enrollment.student.student_id not in submitted_student_ids:
                    pending_students.append({
                        "name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
                        "student_id": str(enrollment.student.student_id)
                    })
            
            total_enrolled = enrolled_students.count()
            total_submissions = len(submitted_student_ids)
            
            graded_submissions = AssignmentSubmission.objects.filter(
                assignment=assignment,
                score__isnull=False
            ).count()
            
            result.append({
                "title": assignment.title,
                "assignment_id": str(assignment.assignments_id),
                "course_name": assignment.course.course_name,
                "due_date": assignment.due_date.strftime("%Y-%m-%d %H:%M"),
                "total_enrolled": total_enrolled,
                "total_submissions": total_submissions,
                "graded": graded_submissions,
                "pending_grading": total_submissions - graded_submissions,
                "pending_submission_count": len(pending_students),
                "pending_students": pending_students[:10]  # Limit to first 10
            })

        return {
            "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
            "total_assignments": len(result),
            "assignments": result
        }

    def get_pending_submissions(self, course_id: str = None, assignment_title: str = None):
        """
        Get a focused list of students who haven't submitted assignments.
        
        Args:
            course_id: Optional course ID/name to filter by
            assignment_title: Optional assignment title to filter by
        
        Returns:
            Dictionary with pending submission details organized by assignment
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
        
        if assignment_title:
            query = query.filter(title__icontains=assignment_title)
        
        assignments = query.select_related('course').all()
        
        if not assignments:
            return {"error": "No assignments found matching your criteria."}
        
        pending_data = []
        total_pending_students = 0
        
        for assignment in assignments:
            # Get students enrolled in this course
            enrolled_students = StudentCourse.objects.filter(
                course=assignment.course
            ).select_related('student')
            
            # Get students who have submitted
            submitted_student_ids = set(
                AssignmentSubmission.objects.filter(
                    assignment=assignment
                ).values_list('student_id', flat=True)
            )
            
            # Find students who haven't submitted
            pending_students = []
            for enrollment in enrolled_students:
                if enrollment.student.student_id not in submitted_student_ids:
                    pending_students.append({
                        "name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
                        "roll_no": enrollment.student.roll_no or str(enrollment.student.student_id)[:8],
                        "email": enrollment.student.user.email if hasattr(enrollment.student, 'user') else None
                    })
            
            if pending_students:
                # Sort by name
                pending_students.sort(key=lambda x: x['name'])
                
                is_overdue = assignment.due_date.date() < assignment.due_date.now().date()
                
                pending_data.append({
                    "assignment_title": assignment.title,
                    "assignment_id": str(assignment.assignments_id),
                    "course_name": assignment.course.course_name,
                    "due_date": assignment.due_date.strftime("%Y-%m-%d %H:%M"),
                    "is_overdue": is_overdue,
                    "total_enrolled": enrolled_students.count(),
                    "submitted_count": len(submitted_student_ids),
                    "pending_count": len(pending_students),
                    "pending_students": pending_students
                })
                total_pending_students += len(pending_students)
        
        if not pending_data:
            return {
                "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
                "message": "All students have submitted their assignments!",
                "assignments_summary": []
            }
        
        return {
            "teacher_name": f"{self.teacher.first_name} {self.teacher.last_name}",
            "total_assignments_with_pending": len(pending_data),
            "total_pending_students": total_pending_students,
            "assignments_summary": pending_data
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
