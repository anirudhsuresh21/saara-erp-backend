from rest_framework import serializers
from .models import (
    Institution, Department, Student, Teacher, Admin, Course, CourseFaculty, StudentCourse,
    Attendance, FeeStructure, StudentFees, Assignment,
    AssignmentSubmission, Exam, Result, Announcement
)


class InstitutionSerializer(serializers.ModelSerializer):
    department_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Institution
        fields = [
            'institution_id', 'name', 'short_name', 'address', 'city', 'state',
            'contact_email', 'contact_phone', 'website', 'logo_url', 'is_active',
            'created_at', 'department_count'
        ]
        read_only_fields = ['institution_id', 'created_at']
    
    def get_department_count(self, obj):
        return obj.departments.count()


class DepartmentSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    institution_short_name = serializers.CharField(source='institution.short_name', read_only=True)
    program_type_display = serializers.CharField(source='get_program_type_display', read_only=True)
    
    class Meta:
        model = Department
        fields = ['department_id', 'institution', 'institution_name', 'institution_short_name', 
                  'department_name', 'dept_code', 'program_type', 'program_type_display', 'hod_id']
        read_only_fields = ['department_id']


class StudentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    enrolled_courses = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of course IDs (course codes) to enroll the student in"
    )
    course_enrollments = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'student_id', 'roll_no', 'user', 'first_name', 'middle_name', 'last_name',
            'department', 'department_name', 'program', 'year_of_study', 'semester',
            'enrolled_courses', 'course_enrollments'
        ]
        read_only_fields = ['student_id']
        extra_kwargs = {
            'middle_name': {'required': False, 'allow_blank': True},
            'roll_no': {'required': False, 'allow_blank': True}
        }
    
    def get_course_enrollments(self, obj):
        enrollments = StudentCourse.objects.filter(student=obj).select_related('course')
        return [{
            'enrollment_id': str(e.enrollment_id),
            'course_id': str(e.course.course_id),
            'course_name': e.course.course_name,
            'academic_year': e.academic_year,
            'semester': e.semester
        } for e in enrollments]
    
    def create(self, validated_data):
        enrolled_courses = validated_data.pop('enrolled_courses', [])
        student = super().create(validated_data)
        
        # Create course enrollments
        if enrolled_courses:
            from datetime import date
            current_year = date.today().year
            for course_id in enrolled_courses:
                try:
                    course = Course.objects.get(course_id=course_id)
                    StudentCourse.objects.create(
                        student=student,
                        course=course,
                        academic_year=current_year,
                        semester=student.semester
                    )
                except Course.DoesNotExist:
                    pass
        
        return student
    
    def update(self, instance, validated_data):
        enrolled_courses = validated_data.pop('enrolled_courses', None)
        student = super().update(instance, validated_data)
        
        # Update course enrollments if provided
        if enrolled_courses is not None:
            from datetime import date
            current_year = date.today().year
            # Get existing enrollment course IDs
            existing_enrollments = set(
                StudentCourse.objects.filter(student=student, academic_year=current_year)
                .values_list('course_id', flat=True)
            )
            new_courses = set(enrolled_courses)
            
            # Add new enrollments
            for course_id in new_courses - existing_enrollments:
                try:
                    course = Course.objects.get(course_id=course_id)
                    StudentCourse.objects.get_or_create(
                        student=student,
                        course=course,
                        academic_year=current_year,
                        semester=student.semester
                    )
                except Course.DoesNotExist:
                    pass
        
        return student


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    course_enrollments = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Student
        fields = ['student_id', 'roll_no', 'first_name', 'middle_name', 'last_name', 'full_name', 'user_email',
                  'department', 'department_name', 'program', 'year_of_study', 'semester', 'course_enrollments']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.middle_name} {obj.last_name}".strip()
    
    def get_course_enrollments(self, obj):
        enrollments = StudentCourse.objects.filter(student=obj).select_related('course')
        return [{
            'enrollment_id': str(e.enrollment_id),
            'course_id': str(e.course.course_id),
            'course_name': e.course.course_name,
            'academic_year': e.academic_year,
            'semester': e.semester
        } for e in enrollments]


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
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['teacher_id', 'full_name', 'user_email', 'department_name', 'designation']
    
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
        # course_id is required as it's a CharField primary key (course code like "MCA11")


class CourseFacultySerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseFaculty
        fields = ['id', 'course', 'course_name', 'teacher', 'teacher_name']
    
    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"


class StudentCourseSerializer(serializers.ModelSerializer):
    """Serializer for student course enrollment"""
    student_name = serializers.SerializerMethodField(read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    department_name = serializers.CharField(source='course.department.department_name', read_only=True)
    credits = serializers.IntegerField(source='course.credits', read_only=True)
    
    class Meta:
        model = StudentCourse
        fields = [
            'enrollment_id', 'student', 'student_name', 'course', 'course_name',
            'department_name', 'credits', 'academic_year', 'semester',
            'enrollment_date', 'grade'
        ]
        read_only_fields = ['enrollment_id', 'enrollment_date']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class StudentCourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing enrollments"""
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    credits = serializers.IntegerField(source='course.credits', read_only=True)
    
    class Meta:
        model = StudentCourse
        fields = ['enrollment_id', 'course', 'course_name', 'credits', 'academic_year', 'semester', 'grade']


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
    course = serializers.CharField(max_length=50)  # Course ID like "MCA201"
    date = serializers.DateField()
    attendance_records = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )


class FeeStructureSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    
    class Meta:
        model = FeeStructure
        fields = [
            'fee_id', 'department', 'department_name', 'academic_year',
            'tution_fees', 'development_fees', 'amount'
        ]
        read_only_fields = ['amount']


class StudentFeesSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    fee_details = serializers.SerializerMethodField(read_only=True)
    fee_structure_name = serializers.SerializerMethodField(read_only=True)
    balance = serializers.DecimalField(source='due_amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = StudentFees
        fields = [
            'payment_id', 'student', 'student_name', 'fee',
            'fee_details', 'fee_structure_name', 'amount_paid', 'due_amount', 'balance',
            'status', 'receipt_number', 'payment_date', 'description'
        ]
        read_only_fields = ['payment_id']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    
    def get_fee_details(self, obj):
        return {
            'department': obj.fee.department.department_name,
            'academic_year': obj.fee.academic_year,
            'total_amount': str(obj.fee.amount)
        }
    
    def get_fee_structure_name(self, obj):
        return f"{obj.fee.department.department_name} - AY {obj.fee.academic_year}"


class AssignmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    created_by_name = serializers.SerializerMethodField(read_only=True)
    file_url = serializers.CharField(required=False, allow_blank=True, default='')
    description = serializers.CharField(required=False, allow_blank=True, default='')
    
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

class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for announcements"""
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    date = serializers.DateField(source='created_at', read_only=True)
    
    class Meta:
        model = Announcement
        fields = [
            'announcement_id', 'title', 'content', 'created_by', 'created_by_email',
            'department', 'department_name', 'course', 'course_name',
            'target_audience', 'is_active', 'created_at', 'updated_at', 'date'
        ]
        read_only_fields = ['announcement_id', 'created_at', 'updated_at']


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing announcements"""
    date = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    
    class Meta:
        model = Announcement
        fields = ['announcement_id', 'title', 'content', 'date', 'target_audience', 'course', 'course_name', 'is_active']
    
    def get_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')


# Import new models for Timetable and AcademicCalendar
from .models import Timetable, AcademicCalendar, LeaveRequest


class TimetableSerializer(serializers.ModelSerializer):
    """Serializer for timetable entries"""
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    course_code = serializers.CharField(source='course.course_id', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Timetable
        fields = [
            'timetable_id', 'course', 'course_name', 'course_code',
            'teacher', 'teacher_name', 'day_of_week',
            'start_time', 'end_time', 'room_number', 'is_active'
        ]
        read_only_fields = ['timetable_id']
    
    def get_teacher_name(self, obj):
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}"
        return "TBA"


class AcademicCalendarSerializer(serializers.ModelSerializer):
    """Serializer for academic calendar events"""
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    
    class Meta:
        model = AcademicCalendar
        fields = [
            'event_id', 'title', 'description', 'event_type',
            'start_date', 'end_date', 'department', 'department_name',
            'is_active', 'created_at'
        ]
        read_only_fields = ['event_id', 'created_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for leave requests"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    approved_by_email = serializers.CharField(source='approved_by.email', read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_id', 'user', 'user_email', 'leave_type',
            'start_date', 'end_date', 'reason', 'status',
            'approved_by', 'approved_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['leave_id', 'created_at', 'updated_at']