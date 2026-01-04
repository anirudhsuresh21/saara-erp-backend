from saara.erp.models import Result, Exam, Course
from django.db.models import Q


class ResultsAgent:
    """Agent to handle results-related queries"""
    
    def __init__(self, student):
        """
        Initialize with student instance
        Args:
            student: Student model instance
        """
        self.student = student

    def get_results(self, course_id: str = None, exam_type: str = None):
        """
        Get exam results for the student
        Args:
            course_id: Optional course ID to filter by
            exam_type: Optional exam type to filter by (midterm, final, quiz, practical)
        Returns:
            Dictionary with result data
        """
        query = Result.objects.filter(student=self.student).select_related('exam', 'exam__course')

        results = query.all()

        if not results:
            return {"error": "No results found."}

        result_data = []
        total_marks = 0
        total_obtained = 0

        for result in results:
            exam = result.exam
            course = exam.course

            # Filter by course_id if provided
            if course_id:
                if not (course_id.lower() in course.course_name.lower() or 
                        course_id.lower() in str(course.course_id).lower()):
                    continue

            # Filter by exam_type if provided
            if exam_type:
                if exam.exam_type.lower() != exam_type.lower():
                    continue

            marks_obtained = float(result.marks_obtained)
            exam_total = exam.total_marks
            
            total_marks += exam_total
            total_obtained += marks_obtained

            result_data.append({
                "exam_id": exam.exam_id,
                "course_name": course.course_name,
                "exam_type": exam.exam_type,
                "exam_date": exam.exam_date.strftime("%Y-%m-%d"),
                "total_marks": exam_total,
                "marks_obtained": marks_obtained,
                "grade": result.grade,
                "percentage": round((marks_obtained / exam_total) * 100, 2) if exam_total > 0 else 0
            })

        if not result_data:
            return {"error": "No matching results found."}

        overall_percentage = round((total_obtained / total_marks) * 100, 2) if total_marks > 0 else 0

        # Calculate GPA (simplified 10-point scale)
        grade_points = {
            'A+': 10, 'A': 9, 'B+': 8, 'B': 7,
            'C+': 6, 'C': 5, 'D': 4, 'F': 0
        }
        total_grade_points = sum(grade_points.get(r['grade'], 0) for r in result_data)
        gpa = round(total_grade_points / len(result_data), 2) if result_data else 0

        return {
            "student_name": f"{self.student.first_name} {self.student.last_name}",
            "total_exams": len(result_data),
            "overall_percentage": overall_percentage,
            "gpa": gpa,
            "total_marks_obtained": total_obtained,
            "total_marks_possible": total_marks,
            "results": result_data
        }
