from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import (
    Institution, Department, Student, Teacher, Admin, Course, CourseFaculty, StudentCourse,
    Attendance, FeeStructure, StudentFees, Assignment,
    AssignmentSubmission, Exam, Result, Announcement
)
from .serializers import (
    InstitutionSerializer, DepartmentSerializer, StudentSerializer, StudentListSerializer,
    TeacherSerializer, TeacherListSerializer, AdminSerializer,
    CourseSerializer, CourseFacultySerializer, StudentCourseSerializer,
    StudentCourseListSerializer, AttendanceSerializer,
    BulkAttendanceSerializer, FeeStructureSerializer, StudentFeesSerializer,
    AssignmentSerializer, AssignmentSubmissionSerializer,
    ExamSerializer, ResultSerializer, AnnouncementSerializer, AnnouncementListSerializer
)
from .permissions import IsAdminOrReadOnly, IsAdminOrTeacher


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Institution/College
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_name', 'city']
    ordering_fields = ['name', 'short_name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def departments(self, request, pk=None):
        """Get all departments for an institution"""
        institution = self.get_object()
        departments = institution.departments.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Department
    
    Permissions:
    - Admin: Full access (CRUD)
    - Others: Read-only
    """
    queryset = Department.objects.select_related('institution').all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['department_name', 'dept_code']
    ordering_fields = ['department_name', 'institution__name']
    ordering = ['department_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by institution
        institution_id = self.request.query_params.get('institution')
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)
        
        return queryset


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


class StudentCourseViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Student Course Enrollments
    
    Permissions:
    - Admin: Full access (CRUD)
    - Teacher: Can view enrollments for their courses
    - Students: Can view their own enrollments
    """
    queryset = StudentCourse.objects.select_related('student', 'course', 'course__department').all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['course__course_name', 'student__first_name', 'student__last_name']
    ordering_fields = ['academic_year', 'semester', 'enrollment_date']
    ordering = ['-academic_year', '-semester']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudentCourseListSerializer
        return StudentCourseSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students can only see their own enrollments
        if user.role == 'student':
            try:
                student = Student.objects.get(user=user)
                queryset = queryset.filter(student=student)
            except Student.DoesNotExist:
                queryset = queryset.none()
        
        # Filter by student
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by academic year
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        # Filter by semester
        semester = self.request.query_params.get('semester')
        if semester:
            queryset = queryset.filter(semester=semester)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Get courses for the current logged-in student"""
        user = request.user
        if user.role != 'student':
            return Response({'error': 'Only students can access this endpoint'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            student = Student.objects.get(user=user)
            enrollments = StudentCourse.objects.filter(student=student)
            serializer = StudentCourseListSerializer(enrollments, many=True)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """Enroll a student in a course"""
        serializer = StudentCourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    queryset = FeeStructure.objects.select_related('department').all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['academic_year', 'amount', 'department__department_name']
    ordering = ['-academic_year',]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by department
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Filter by academic year
        year = self.request.query_params.get('academic_year')
        if year:
            queryset = queryset.filter(academic_year=year)
        
        # Filter by semester
        # semester = self.request.query_params.get('semester')
        # if semester:
        #     queryset = queryset.filter(semester=semester)
        
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

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Announcements
    
    Permissions:
    - Admin: Full access (CRUD)
    - Teacher: Can create, update, delete their own announcements
    - Students: Read-only (only active announcements)
    """
    queryset = Announcement.objects.select_related('created_by', 'department').all()
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AnnouncementListSerializer
        return AnnouncementSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students only see active announcements targeted at them or their enrolled courses
        if user.role == 'student':
            try:
                student = Student.objects.get(user=user)
                enrolled_course_ids = StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)
                queryset = queryset.filter(is_active=True).filter(
                    Q(target_audience='all') | 
                    Q(target_audience='students') |
                    Q(target_audience='course', course_id__in=enrolled_course_ids)
                )
            except Student.DoesNotExist:
                queryset = queryset.filter(
                    is_active=True
                ).filter(
                    Q(target_audience='all') | Q(target_audience='students')
                )
        # Teachers see announcements for all, teachers, and their courses
        elif user.role == 'faculty':
            queryset = queryset.filter(
                Q(target_audience='all') | Q(target_audience='teachers') | Q(created_by=user)
            )
        
        # Filter by target audience
        target = self.request.query_params.get('target')
        if target:
            queryset = queryset.filter(target_audience=target)
        
        # Filter by active status
        active = self.request.query_params.get('active')
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() == 'true')
        
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        return queryset
    
    def perform_create(self, serializer):
        """Automatically set the created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_announcements(self, request):
        """Get announcements created by the current user"""
        announcements = Announcement.objects.filter(created_by=request.user)
        serializer = AnnouncementListSerializer(announcements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of an announcement"""
        announcement = self.get_object()
        announcement.is_active = not announcement.is_active
        announcement.save()
        return Response({
            'announcement_id': str(announcement.announcement_id),
            'is_active': announcement.is_active
        })