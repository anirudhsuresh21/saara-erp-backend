from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import (
    Department, Student, Teacher, Admin, Course, CourseFaculty,
    Attendance, FeeStructure, StudentFees, Assignment,
    AssignmentSubmission, Exam, Result
)
from .serializers import (
    DepartmentSerializer, StudentSerializer, StudentListSerializer,
    TeacherSerializer, TeacherListSerializer, AdminSerializer,
    CourseSerializer, CourseFacultySerializer, AttendanceSerializer,
    BulkAttendanceSerializer, FeeStructureSerializer, StudentFeesSerializer,
    AssignmentSerializer, AssignmentSubmissionSerializer,
    ExamSerializer, ResultSerializer
)
from .permissions import IsAdminOrReadOnly, IsAdminOrTeacher


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Department
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['department_name']
    ordering_fields = ['department_name']
    ordering = ['department_name']


class StudentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Student
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Student.objects.select_related('department', 'user').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'program']
    ordering_fields = ['first_name', 'last_name', 'year_of_study']
    ordering = ['first_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filter by year of study
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year_of_study=year)
        
        # Filter by semester
        semester = self.request.query_params.get('semester')
        if semester:
            queryset = queryset.filter(semester=semester)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Get attendance records for a specific student"""
        student = self.get_object()
        attendance = Attendance.objects.filter(student=student)
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def fees(self, request, pk=None):
        """Get fee records for a specific student"""
        student = self.get_object()
        fees = StudentFees.objects.filter(student=student)
        serializer = StudentFeesSerializer(fees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get exam results for a specific student"""
        student = self.get_object()
        results = Result.objects.filter(student=student)
        serializer = ResultSerializer(results, many=True)
        return Response(serializer.data)


class TeacherViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Teacher
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Teacher.objects.select_related('department', 'user').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'designation']
    ordering_fields = ['first_name', 'last_name']
    ordering = ['first_name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TeacherListSerializer
        return TeacherSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Get courses taught by a specific teacher"""
        teacher = self.get_object()
        course_faculty = CourseFaculty.objects.filter(teacher=teacher).select_related('course')
        courses = [cf.course for cf in course_faculty]
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


class AdminViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Admin
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Admin.objects.select_related('user').all()
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class CourseViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Course
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Course.objects.select_related('department').all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['course_name']
    ordering_fields = ['course_name', 'credits', 'semester']
    ordering = ['course_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filter by semester
        semester = self.request.query_params.get('semester')
        if semester:
            queryset = queryset.filter(semester=semester)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def faculty(self, request, pk=None):
        """Get faculty assigned to a specific course"""
        course = self.get_object()
        faculty = CourseFaculty.objects.filter(course=course).select_related('teacher')
        serializer = CourseFacultySerializer(faculty, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Get assignments for a specific course"""
        course = self.get_object()
        assignments = Assignment.objects.filter(course=course)
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def exams(self, request, pk=None):
        """Get exams for a specific course"""
        course = self.get_object()
        exams = Exam.objects.filter(course=course)
        serializer = ExamSerializer(exams, many=True)
        return Response(serializer.data)


class CourseFacultyViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Course-Faculty assignments
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = CourseFaculty.objects.select_related('course', 'teacher').all()
    serializer_class = CourseFacultySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by teacher
        teacher = self.request.query_params.get('teacher')
        if teacher:
            queryset = queryset.filter(teacher_id=teacher)
        
        return queryset


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Attendance
    
    Permissions:
    - Admin: Full access (CRUD)
    - Teacher: Full access (CRUD)
    - Students: Read-only
    """
    queryset = Attendance.objects.select_related('student', 'course').all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'status']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Mark attendance for multiple students at once"""
        serializer = BulkAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            course_id = serializer.validated_data['course']
            date = serializer.validated_data['date']
            records = serializer.validated_data['attendance_records']
            
            created_records = []
            for record in records:
                attendance, created = Attendance.objects.update_or_create(
                    student_id=record['student_id'],
                    course_id=course_id,
                    date=date,
                    defaults={'status': record['status']}
                )
                created_records.append(attendance)
            
            return Response({
                'message': f'Attendance marked for {len(created_records)} students',
                'count': len(created_records)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeeStructureViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Fee Structure
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['academic_year', 'semester', 'amount']
    ordering = ['-academic_year', 'semester']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by academic year
        year = self.request.query_params.get('academic_year')
        if year:
            queryset = queryset.filter(academic_year=year)
        
        # Filter by semester
        semester = self.request.query_params.get('semester')
        if semester:
            queryset = queryset.filter(semester=semester)
        
        return queryset


class StudentFeesViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Student Fees
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = StudentFees.objects.select_related('student', 'fee').all()
    serializer_class = StudentFeesSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['status', 'amount_paid']
    ordering = ['status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending/overdue fee payments"""
        fees = self.get_queryset().filter(status__in=['pending', 'overdue'])
        serializer = self.get_serializer(fees, many=True)
        return Response(serializer.data)


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Assignment
    
    Permissions:
    - Admin: Full access (CRUD)
    - Teacher: Full access (CRUD)
    - Students: Read-only
    """
    queryset = Assignment.objects.select_related('course', 'created_by').all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'title']
    ordering = ['-due_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by created_by (teacher)
        teacher = self.request.query_params.get('teacher')
        if teacher:
            queryset = queryset.filter(created_by_id=teacher)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get all submissions for a specific assignment"""
        assignment = self.get_object()
        submissions = AssignmentSubmission.objects.filter(assignment=assignment)
        serializer = AssignmentSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Assignment Submission
    
    Permissions:
    - Admin: Full access (CRUD)
    - Teacher: Full access (CRUD) - can grade submissions
    - Students: Read-only
    """
    queryset = AssignmentSubmission.objects.select_related('assignment', 'student').all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['submitted_date', 'score']
    ordering = ['-submitted_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by assignment
        assignment = self.request.query_params.get('assignment')
        if assignment:
            queryset = queryset.filter(assignment_id=assignment)
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        return queryset


class ExamViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Exam
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Exam.objects.select_related('course').all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['exam_date', 'exam_type']
    ordering = ['-exam_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by exam type
        exam_type = self.request.query_params.get('exam_type')
        if exam_type:
            queryset = queryset.filter(exam_type=exam_type)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get all results for a specific exam"""
        exam = self.get_object()
        results = Result.objects.filter(exam=exam)
        serializer = ResultSerializer(results, many=True)
        return Response(serializer.data)


class ResultViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Result
    
    Permissions:
    - Admin: Full access (CRUD)
    - Teacher: Full access (CRUD) - can enter/update marks
    - Students: Read-only
    """
    queryset = Result.objects.select_related('exam', 'student', 'exam__course').all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['marks_obtained', 'grade']
    ordering = ['-marks_obtained']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by exam
        exam = self.request.query_params.get('exam')
        if exam:
            queryset = queryset.filter(exam_id=exam)
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        # Filter by grade
        grade = self.request.query_params.get('grade')
        if grade:
            queryset = queryset.filter(grade=grade)
        
        return queryset
