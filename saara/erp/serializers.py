from rest_framework import serializers
from .models import (
    Department, Student, Teacher, Admin, Course, CourseFaculty,
    Attendance, FeeStructure, StudentFees, Assignment,
    AssignmentSubmission, Exam, Result
)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department_id', 'department_name', 'hod_id']
        read_only_fields = ['department_id']


class StudentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'user', 'first_name', 'middle_name', 'last_name',
            'department', 'department_name', 'program', 'year_of_study', 'semester'
        ]
        read_only_fields = ['student_id']


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['student_id', 'full_name', 'department_name', 'program', 'year_of_study', 'semester']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.middle_name} {obj.last_name}".strip()


class TeacherSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'teacher_id', 'user', 'first_name', 'last_name',
            'department', 'department_name', 'designation'
        ]


class TeacherListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['teacher_id', 'full_name', 'department_name', 'designation']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['admin_id', 'user', 'name']
        read_only_fields = ['admin_id']


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'course_id', 'course_name', 'credits', 'semester',
            'department', 'department_name'
        ]
        read_only_fields = ['course_id']


class CourseFacultySerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseFaculty
        fields = ['id', 'course', 'course_name', 'teacher', 'teacher_name']
    
    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'attendence_id', 'student', 'student_name', 'course',
            'course_name', 'date', 'status'
        ]
        read_only_fields = ['attendence_id']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class BulkAttendanceSerializer(serializers.Serializer):
    """Serializer for marking attendance in bulk"""
    course = serializers.UUIDField()
    date = serializers.DateField()
    attendance_records = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )


class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = [
            'fee_id', 'academic_year', 'semester',
            'tution_fees', 'development_fees', 'amount'
        ]
        read_only_fields = ['amount']


class StudentFeesSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    fee_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = StudentFees
        fields = [
            'payment_id', 'student', 'student_name', 'fee',
            'fee_details', 'amount_paid', 'due_amount', 'status'
        ]
        read_only_fields = ['payment_id']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    
    def get_fee_details(self, obj):
        return {
            'academic_year': obj.fee.academic_year,
            'semester': obj.fee.semester,
            'total_amount': str(obj.fee.amount)
        }


class AssignmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'assignments_id', 'course', 'course_name', 'title',
            'description', 'file_url', 'due_date', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['assignments_id']
    
    def get_created_by_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}"


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    student_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'submission_id', 'assignment', 'assignment_title',
            'student', 'student_name', 'submitted_date', 'score'
        ]
        read_only_fields = ['submission_id']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class ExamSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    
    class Meta:
        model = Exam
        fields = [
            'exam_id', 'course', 'course_name', 'exam_type',
            'exam_date', 'total_marks'
        ]


class ResultSerializer(serializers.ModelSerializer):
    exam_details = serializers.SerializerMethodField(read_only=True)
    student_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Result
        fields = [
            'result_id', 'exam', 'exam_details', 'student',
            'student_name', 'marks_obtained', 'grade'
        ]
        read_only_fields = ['result_id']
    
    def get_exam_details(self, obj):
        return {
            'exam_type': obj.exam.exam_type,
            'course': obj.exam.course.course_name,
            'date': str(obj.exam.exam_date),
            'total_marks': obj.exam.total_marks
        }
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
