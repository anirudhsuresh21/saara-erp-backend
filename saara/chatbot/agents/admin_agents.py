from saara.erp.models import (
    Attendance, Course, Student, Teacher, Department,
    StudentFees, FeeStructure, Assignment, AssignmentSubmission,
    Result, Exam, Admin
)
from django.db.models import Count, Q, Avg, Sum


class AdminAttendanceAgent:
    """Agent to handle attendance-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_attendance(self, course_id: str = None, department_id: str = None):
        """
        Get attendance overview for admin
        """
        query = Attendance.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(student__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        total_records = query.count()
        if total_records == 0:
            return {"error": "No attendance records found."}
        
        present_count = query.filter(Q(status='present') | Q(status='late')).count()
        absent_count = query.filter(status='absent').count()
        
        overall_attendance = (present_count / total_records) * 100 if total_records > 0 else 0
        
        # Department-wise breakdown
        dept_breakdown = []
        departments = Department.objects.all()
        for dept in departments:
            dept_records = query.filter(student__department=dept)
            dept_total = dept_records.count()
            if dept_total > 0:
                dept_present = dept_records.filter(Q(status='present') | Q(status='late')).count()
                dept_breakdown.append({
                    "department": dept.department_name,
                    "total_records": dept_total,
                    "attendance_percentage": round((dept_present / dept_total) * 100, 2)
                })

        return {
            "admin_name": self.admin.name,
            "total_records": total_records,
            "overall_attendance": round(overall_attendance, 2),
            "present": present_count,
            "absent": absent_count,
            "department_breakdown": dept_breakdown
        }


class AdminFeesAgent:
    """Agent to handle fees-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_fees(self, department_id: str = None):
        """
        Get fee collection overview for admin
        """
        query = StudentFees.objects.all()
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(student__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        if not query.exists():
            return {"error": "No fee records found."}

        total_collected = query.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_pending = query.aggregate(total=Sum('due_amount'))['total'] or 0
        
        # Status breakdown
        paid_count = query.filter(status='paid').count()
        partial_count = query.filter(status='partial').count()
        pending_count = query.filter(status='pending').count()
        overdue_count = query.filter(status='overdue').count()
        
        # Department-wise breakdown
        dept_breakdown = []
        departments = Department.objects.all()
        for dept in departments:
            dept_fees = query.filter(student__department=dept)
            if dept_fees.exists():
                dept_collected = dept_fees.aggregate(total=Sum('amount_paid'))['total'] or 0
                dept_pending = dept_fees.aggregate(total=Sum('due_amount'))['total'] or 0
                dept_breakdown.append({
                    "department": dept.department_name,
                    "collected": float(dept_collected),
                    "pending": float(dept_pending)
                })

        return {
            "admin_name": self.admin.name,
            "total_collected": float(total_collected),
            "total_pending": float(total_pending),
            "collection_rate": round((total_collected / (total_collected + total_pending)) * 100, 2) if (total_collected + total_pending) > 0 else 0,
            "status_breakdown": {
                "paid": paid_count,
                "partial": partial_count,
                "pending": pending_count,
                "overdue": overdue_count
            },
            "department_breakdown": dept_breakdown
        }


class AdminAssignmentAgent:
    """Agent to handle assignment-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_assignments(self, course_id: str = None, department_id: str = None):
        """
        Get assignment overview for admin
        """
        query = Assignment.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(course__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        assignments = query.select_related('course', 'created_by').all()
        
        if not assignments:
            return {"error": "No assignments found."}

        total_assignments = len(assignments)
        total_submissions = AssignmentSubmission.objects.filter(
            assignment__in=assignments
        ).count()
        
        # Get assignment summary by course
        course_summary = {}
        for assignment in assignments:
            course_name = assignment.course.course_name
            if course_name not in course_summary:
                course_summary[course_name] = {
                    "assignments": 0,
                    "submissions": 0
                }
            course_summary[course_name]["assignments"] += 1
            course_summary[course_name]["submissions"] += AssignmentSubmission.objects.filter(
                assignment=assignment
            ).count()

        return {
            "admin_name": self.admin.name,
            "total_assignments": total_assignments,
            "total_submissions": total_submissions,
            "course_summary": [
                {"course": k, **v} for k, v in course_summary.items()
            ]
        }


class AdminResultsAgent:
    """Agent to handle results-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_results(self, course_id: str = None, exam_type: str = None, department_id: str = None):
        """
        Get results overview for admin
        """
        query = Result.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(exam__course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if exam_type:
            query = query.filter(exam__exam_type__iexact=exam_type)
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(student__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        results = query.select_related('exam', 'exam__course', 'student').all()
        
        if not results:
            return {"error": "No results found."}

        total_students = query.values('student').distinct().count()
        avg_percentage = 0
        
        # Calculate overall statistics
        total_marks_obtained = sum(float(r.marks_obtained) for r in results)
        total_marks_possible = sum(r.exam.total_marks for r in results)
        
        if total_marks_possible > 0:
            avg_percentage = (total_marks_obtained / total_marks_possible) * 100
        
        # Grade distribution
        grade_dist = query.values('grade').annotate(count=Count('grade'))
        
        # Department-wise performance
        dept_performance = []
        departments = Department.objects.all()
        for dept in departments:
            dept_results = query.filter(student__department=dept)
            if dept_results.exists():
                dept_marks = sum(float(r.marks_obtained) for r in dept_results)
                dept_total = sum(r.exam.total_marks for r in dept_results)
                dept_avg = (dept_marks / dept_total) * 100 if dept_total > 0 else 0
                dept_performance.append({
                    "department": dept.department_name,
                    "students": dept_results.values('student').distinct().count(),
                    "average_percentage": round(dept_avg, 2)
                })

        return {
            "admin_name": self.admin.name,
            "total_results": len(results),
            "total_students": total_students,
            "overall_average": round(avg_percentage, 2),
            "grade_distribution": {g['grade']: g['count'] for g in grade_dist},
            "department_performance": dept_performance
        }
