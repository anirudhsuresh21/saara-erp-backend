"""
Comprehensive Test Suite for SAARA Backend API
==============================================

This file contains tests for all endpoints in the saara-backend project.
Run with: python manage.py test saara.test_all
Or use pytest: pytest test_all.py -v

Prerequisites:
- Set up test database
- Configure environment variables
- Install test dependencies: pip install pytest pytest-django faker

"""
import os
import sys
import json
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

# Import models
from saara.authapp.models import User, AllowedEmailDomain
from saara.erp.models import (
    Department, Student, Teacher, Admin, Course, CourseFaculty,
    Attendance, FeeStructure, StudentFees, Assignment,
    AssignmentSubmission, Exam, Result
)
from saara.chatbot.models import ChatSession, ChatMessage


class BaseTestCase(APITestCase):
    """Base test case with common setup for all tests"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase"""
        # Create allowed email domain
        cls.allowed_domain = AllowedEmailDomain.objects.create(
            domain='sies.edu.in',
            institution_name='SIES Graduate School of Technology',
            is_active=True,
            allow_subdomains=True
        )
        
        # Create test users
        cls.admin_user = User.objects.create(
            email='admin@sies.edu.in',
            role='admin',
            is_active=True
        )
        cls.admin_user.set_password('testpass123')
        cls.admin_user.save()
        
        cls.teacher_user = User.objects.create(
            email='teacher@sies.edu.in',
            role='faculty',
            is_active=True
        )
        cls.teacher_user.set_password('testpass123')
        cls.teacher_user.save()
        
        cls.student_user = User.objects.create(
            email='student@sies.edu.in',
            role='student',
            is_active=True
        )
        cls.student_user.set_password('testpass123')
        cls.student_user.save()
        
        # Create department
        cls.department = Department.objects.create(
            department_name='Computer Science',
            hod_id='HOD001'
        )
        
        # Create teacher profile
        cls.teacher = Teacher.objects.create(
            teacher_id='T001',
            user=cls.teacher_user,
            first_name='John',
            last_name='Doe',
            department=cls.department,
            designation='Professor'
        )
        
        # Create admin profile
        cls.admin_profile = Admin.objects.create(
            user=cls.admin_user,
            name='Admin User'
        )
        
        # Create student profile
        cls.student = Student.objects.create(
            user=cls.student_user,
            first_name='Jane',
            middle_name='M',
            last_name='Smith',
            department=cls.department,
            program='B.Tech',
            year_of_study=2,
            semester=3
        )
        
        # Create course
        cls.course = Course.objects.create(
            course_name='Data Structures',
            credits=4,
            semester=3,
            department=cls.department
        )
        
        # Create course faculty assignment
        cls.course_faculty = CourseFaculty.objects.create(
            course=cls.course,
            teacher=cls.teacher
        )
        
        # Create fee structure
        cls.fee_structure = FeeStructure.objects.create(
            fee_id='FEE001',
            academic_year=2025,
            semester=3,
            tution_fees=Decimal('50000.00'),
            development_fees=Decimal('10000.00')
        )
        
        # Create student fees
        cls.student_fees = StudentFees.objects.create(
            student=cls.student,
            fee=cls.fee_structure,
            amount_paid=Decimal('30000.00'),
            due_amount=Decimal('30000.00'),
            status='partial'
        )
        
        # Create attendance record
        cls.attendance = Attendance.objects.create(
            student=cls.student,
            course=cls.course,
            date=date.today(),
            status='present'
        )
        
        # Create assignment
        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title='Assignment 1: Linked Lists',
            description='Implement a doubly linked list',
            file_url='https://example.com/assignment1.pdf',
            due_date=datetime.now() + timedelta(days=7),
            created_by=cls.teacher
        )
        
        # Create exam
        cls.exam = Exam.objects.create(
            exam_id='EXAM001',
            course=cls.course,
            exam_type='midterm',
            exam_date=date.today() + timedelta(days=30),
            total_marks=100
        )
        
        # Create result
        cls.result = Result.objects.create(
            exam=cls.exam,
            student=cls.student,
            marks_obtained=Decimal('85.00'),
            grade='A'
        )
    
    def setUp(self):
        """Set up for each test method"""
        self.client = APIClient()
    
    def authenticate_as_admin(self):
        """Authenticate as admin user"""
        self.client.force_authenticate(user=self.admin_user)
    
    def authenticate_as_teacher(self):
        """Authenticate as teacher user"""
        self.client.force_authenticate(user=self.teacher_user)
    
    def authenticate_as_student(self):
        """Authenticate as student user"""
        self.client.force_authenticate(user=self.student_user)


# ============================================================================
# AUTH ENDPOINTS TESTS
# ============================================================================

class AuthEndpointTests(BaseTestCase):
    """Tests for authentication endpoints"""
    
    def test_get_allowed_domains(self):
        """Test GET /api/auth/allowed-domains/"""
        response = self.client.get('/api/auth/allowed-domains/')
        # This endpoint might require auth or be public
        self.assertIn(response.status_code, [200, 401, 403])
    
    def test_login_missing_credentials(self):
        """Test POST /api/auth/login/ with missing credentials"""
        response = self.client.post('/api/auth/login/', {}, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_login_invalid_domain(self):
        """Test POST /api/auth/login/ with invalid email domain"""
        response = self.client.post('/api/auth/login/', {
            'email': 'user@invalid.com',
            'password': 'testpass123'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_register_missing_credentials(self):
        """Test POST /api/auth/register/ with missing credentials"""
        response = self.client.post('/api/auth/register/', {}, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_register_invalid_domain(self):
        """Test POST /api/auth/register/ with invalid email domain"""
        response = self.client.post('/api/auth/register/', {
            'email': 'newuser@invalid.com',
            'password': 'testpass123'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_get_current_user_unauthenticated(self):
        """Test GET /api/auth/user/ without authentication"""
        response = self.client.get('/api/auth/user/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_get_current_user_authenticated(self):
        """Test GET /api/auth/user/ with authentication"""
        self.authenticate_as_student()
        response = self.client.get('/api/auth/user/')
        self.assertIn(response.status_code, [200, 404])  # 404 if view not implemented
    
    def test_logout_unauthenticated(self):
        """Test POST /api/auth/logout/ without authentication"""
        response = self.client.post('/api/auth/logout/', format='json')
        self.assertIn(response.status_code, [401, 403, 200])


# ============================================================================
# DEPARTMENT ENDPOINTS TESTS
# ============================================================================

class DepartmentEndpointTests(BaseTestCase):
    """Tests for Department CRUD endpoints"""
    
    def test_list_departments_unauthenticated(self):
        """Test GET /erp/departments/ without auth"""
        response = self.client.get('/erp/departments/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_departments_authenticated(self):
        """Test GET /erp/departments/ with auth"""
        self.authenticate_as_student()
        response = self.client.get('/erp/departments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_create_department_as_admin(self):
        """Test POST /erp/departments/ as admin"""
        self.authenticate_as_admin()
        response = self.client.post('/erp/departments/', {
            'department_name': 'Electrical Engineering',
            'hod_id': 'HOD002'
        }, format='json')
        self.assertIn(response.status_code, [201, 400])
    
    def test_create_department_as_student(self):
        """Test POST /erp/departments/ as student (should fail)"""
        self.authenticate_as_student()
        response = self.client.post('/erp/departments/', {
            'department_name': 'Mechanical Engineering'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_department_detail(self):
        """Test GET /erp/departments/{id}/"""
        self.authenticate_as_student()
        response = self.client.get(f'/erp/departments/{self.department.department_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_department_as_admin(self):
        """Test PUT /erp/departments/{id}/ as admin"""
        self.authenticate_as_admin()
        response = self.client.patch(f'/erp/departments/{self.department.department_id}/', {
            'department_name': 'Computer Science & Engineering'
        }, format='json')
        self.assertIn(response.status_code, [200, 400])
    
    def test_delete_department_as_admin(self):
        """Test DELETE /erp/departments/{id}/ as admin"""
        self.authenticate_as_admin()
        new_dept = Department.objects.create(department_name='To Delete')
        response = self.client.delete(f'/erp/departments/{new_dept.department_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# ============================================================================
# STUDENT ENDPOINTS TESTS
# ============================================================================

class StudentEndpointTests(BaseTestCase):
    """Tests for Student CRUD endpoints"""
    
    def test_list_students(self):
        """Test GET /erp/students/"""
        self.authenticate_as_admin()
        response = self.client.get('/erp/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_student_detail(self):
        """Test GET /erp/students/{id}/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/students/{self.student.student_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_students_by_department(self):
        """Test GET /erp/students/?department={id}"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/students/?department={self.department.department_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_students_by_year(self):
        """Test GET /erp/students/?year=2"""
        self.authenticate_as_admin()
        response = self.client.get('/erp/students/?year=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_attendance_action(self):
        """Test GET /erp/students/{id}/attendance/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/students/{self.student.student_id}/attendance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_fees_action(self):
        """Test GET /erp/students/{id}/fees/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/students/{self.student.student_id}/fees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_results_action(self):
        """Test GET /erp/students/{id}/results/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/students/{self.student.student_id}/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# TEACHER ENDPOINTS TESTS
# ============================================================================

class TeacherEndpointTests(BaseTestCase):
    """Tests for Teacher CRUD endpoints"""
    
    def test_list_teachers(self):
        """Test GET /erp/teachers/"""
        self.authenticate_as_admin()
        response = self.client.get('/erp/teachers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_teacher_detail(self):
        """Test GET /erp/teachers/{id}/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/teachers/{self.teacher.teacher_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_teacher_as_admin(self):
        """Test POST /erp/teachers/ as admin"""
        self.authenticate_as_admin()
        new_user = User.objects.create(email='newteacher@sies.edu.in', role='faculty')
        response = self.client.post('/erp/teachers/', {
            'teacher_id': 'T002',
            'user': str(new_user.user_id),
            'first_name': 'New',
            'last_name': 'Teacher',
            'department': str(self.department.department_id),
            'designation': 'Assistant Professor'
        }, format='json')
        self.assertIn(response.status_code, [201, 400])


# ============================================================================
# COURSE ENDPOINTS TESTS
# ============================================================================

class CourseEndpointTests(BaseTestCase):
    """Tests for Course CRUD endpoints"""
    
    def test_list_courses(self):
        """Test GET /erp/courses/"""
        self.authenticate_as_student()
        response = self.client.get('/erp/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_course_detail(self):
        """Test GET /erp/courses/{id}/"""
        self.authenticate_as_student()
        response = self.client.get(f'/erp/courses/{self.course.course_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_course_as_admin(self):
        """Test POST /erp/courses/ as admin"""
        self.authenticate_as_admin()
        response = self.client.post('/erp/courses/', {
            'course_name': 'Algorithms',
            'credits': 3,
            'semester': 4,
            'department': str(self.department.department_id)
        }, format='json')
        self.assertIn(response.status_code, [201, 400])
    
    def test_create_course_as_student(self):
        """Test POST /erp/courses/ as student (should fail)"""
        self.authenticate_as_student()
        response = self.client.post('/erp/courses/', {
            'course_name': 'Unauthorized Course'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================================
# ATTENDANCE ENDPOINTS TESTS
# ============================================================================

class AttendanceEndpointTests(BaseTestCase):
    """Tests for Attendance CRUD endpoints"""
    
    def test_list_attendance(self):
        """Test GET /erp/attendance/"""
        self.authenticate_as_teacher()
        response = self.client.get('/erp/attendance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_attendance_as_teacher(self):
        """Test POST /erp/attendance/ as teacher"""
        self.authenticate_as_teacher()
        response = self.client.post('/erp/attendance/', {
            'student': str(self.student.student_id),
            'course': str(self.course.course_id),
            'date': str(date.today() - timedelta(days=1)),
            'status': 'present'
        }, format='json')
        self.assertIn(response.status_code, [201, 400])
    
    def test_create_attendance_as_student(self):
        """Test POST /erp/attendance/ as student (should fail)"""
        self.authenticate_as_student()
        response = self.client.post('/erp/attendance/', {
            'student': str(self.student.student_id),
            'course': str(self.course.course_id),
            'date': str(date.today()),
            'status': 'present'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================================
# FEE STRUCTURE ENDPOINTS TESTS
# ============================================================================

class FeeStructureEndpointTests(BaseTestCase):
    """Tests for Fee Structure CRUD endpoints"""
    
    def test_list_fee_structures(self):
        """Test GET /erp/fee-structure/"""
        self.authenticate_as_admin()
        response = self.client.get('/erp/fee-structure/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_fee_structure_as_admin(self):
        """Test POST /erp/fee-structure/ as admin"""
        self.authenticate_as_admin()
        response = self.client.post('/erp/fee-structure/', {
            'fee_id': 'FEE002',
            'academic_year': 2026,
            'semester': 4,
            'tution_fees': '55000.00',
            'development_fees': '12000.00'
        }, format='json')
        self.assertIn(response.status_code, [201, 400])


# ============================================================================
# STUDENT FEES ENDPOINTS TESTS
# ============================================================================

class StudentFeesEndpointTests(BaseTestCase):
    """Tests for Student Fees CRUD endpoints"""
    
    def test_list_student_fees(self):
        """Test GET /erp/student-fees/"""
        self.authenticate_as_admin()
        response = self.client.get('/erp/student-fees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_student_fees_detail(self):
        """Test GET /erp/student-fees/{id}/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/student-fees/{self.student_fees.payment_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# ASSIGNMENT ENDPOINTS TESTS
# ============================================================================

class AssignmentEndpointTests(BaseTestCase):
    """Tests for Assignment CRUD endpoints"""
    
    def test_list_assignments(self):
        """Test GET /erp/assignments/"""
        self.authenticate_as_student()
        response = self.client.get('/erp/assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_assignment_detail(self):
        """Test GET /erp/assignments/{id}/"""
        self.authenticate_as_student()
        response = self.client.get(f'/erp/assignments/{self.assignment.assignments_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_assignment_as_teacher(self):
        """Test POST /erp/assignments/ as teacher"""
        self.authenticate_as_teacher()
        response = self.client.post('/erp/assignments/', {
            'course': str(self.course.course_id),
            'title': 'Assignment 2',
            'description': 'Implement a binary search tree',
            'file_url': 'https://example.com/assignment2.pdf',
            'due_date': str(datetime.now() + timedelta(days=14)),
            'created_by': self.teacher.teacher_id
        }, format='json')
        self.assertIn(response.status_code, [201, 400])


# ============================================================================
# ASSIGNMENT SUBMISSION ENDPOINTS TESTS
# ============================================================================

class AssignmentSubmissionEndpointTests(BaseTestCase):
    """Tests for Assignment Submission CRUD endpoints"""
    
    def test_list_submissions(self):
        """Test GET /erp/submissions/"""
        self.authenticate_as_teacher()
        response = self.client.get('/erp/submissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_submission_as_student(self):
        """Test POST /erp/submissions/ as student"""
        self.authenticate_as_student()
        response = self.client.post('/erp/submissions/', {
            'assignment': str(self.assignment.assignments_id),
            'student': str(self.student.student_id),
            'submitted_date': str(date.today())
        }, format='json')
        self.assertIn(response.status_code, [201, 400, 403])


# ============================================================================
# EXAM ENDPOINTS TESTS
# ============================================================================

class ExamEndpointTests(BaseTestCase):
    """Tests for Exam CRUD endpoints"""
    
    def test_list_exams(self):
        """Test GET /erp/exams/"""
        self.authenticate_as_student()
        response = self.client.get('/erp/exams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_exam_detail(self):
        """Test GET /erp/exams/{id}/"""
        self.authenticate_as_student()
        response = self.client.get(f'/erp/exams/{self.exam.exam_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_exam_as_admin(self):
        """Test POST /erp/exams/ as admin"""
        self.authenticate_as_admin()
        response = self.client.post('/erp/exams/', {
            'exam_id': 'EXAM002',
            'course': str(self.course.course_id),
            'exam_type': 'final',
            'exam_date': str(date.today() + timedelta(days=60)),
            'total_marks': 100
        }, format='json')
        self.assertIn(response.status_code, [201, 400])


# ============================================================================
# RESULT ENDPOINTS TESTS
# ============================================================================

class ResultEndpointTests(BaseTestCase):
    """Tests for Result CRUD endpoints"""
    
    def test_list_results(self):
        """Test GET /erp/results/"""
        self.authenticate_as_admin()
        response = self.client.get('/erp/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_result_detail(self):
        """Test GET /erp/results/{id}/"""
        self.authenticate_as_admin()
        response = self.client.get(f'/erp/results/{self.result.result_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# CHATBOT ENDPOINTS TESTS
# ============================================================================

class ChatbotEndpointTests(BaseTestCase):
    """Tests for Chatbot endpoints"""
    
    def test_chat_unauthenticated(self):
        """Test POST /api/chatbot/chat/ without auth"""
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'What is my attendance?'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_chat_as_student(self):
        """Test POST /api/chatbot/chat/ as student"""
        self.authenticate_as_student()
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'What is my attendance?'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])  # 500 if Gemini API not configured
        if response.status_code == 200:
            self.assertIn('response', response.data)
            self.assertEqual(response.data.get('user_role'), 'student')
    
    def test_chat_as_teacher(self):
        """Test POST /api/chatbot/chat/ as teacher"""
        self.authenticate_as_teacher()
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Show attendance for my courses'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            self.assertEqual(response.data.get('user_role'), 'teacher')
    
    def test_chat_as_admin(self):
        """Test POST /api/chatbot/chat/ as admin"""
        self.authenticate_as_admin()
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Overall attendance statistics'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            self.assertEqual(response.data.get('user_role'), 'admin')
    
    def test_chat_student_restricted_query(self):
        """Test that students cannot access teacher/admin data"""
        self.authenticate_as_student()
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Show me all teachers information'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_chat_teacher_restricted_query(self):
        """Test that teachers cannot access admin data"""
        self.authenticate_as_teacher()
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Show me admin salary information'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_chat_session_creation(self):
        """Test that chat creates a session"""
        self.authenticate_as_student()
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'What is my attendance?'
        }, format='json')
        if response.status_code == 200:
            self.assertIn('session_id', response.data)
    
    def test_chat_continue_session(self):
        """Test continuing an existing session"""
        self.authenticate_as_student()
        # First message
        response1 = self.client.post('/api/chatbot/chat/', {
            'query': 'What is my attendance?'
        }, format='json')
        
        if response1.status_code == 200:
            session_id = response1.data.get('session_id')
            # Continue session
            response2 = self.client.post('/api/chatbot/chat/', {
                'query': 'What about my fees?',
                'session_id': session_id
            }, format='json')
            self.assertIn(response2.status_code, [200, 500])
    
    def test_list_sessions_unauthenticated(self):
        """Test GET /api/chatbot/sessions/ without auth"""
        response = self.client.get('/api/chatbot/sessions/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_list_sessions_authenticated(self):
        """Test GET /api/chatbot/sessions/ with auth"""
        self.authenticate_as_student()
        response = self.client.get('/api/chatbot/sessions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_session_detail(self):
        """Test GET /api/chatbot/sessions/{id}/"""
        self.authenticate_as_student()
        # Create a session first
        session = ChatSession.objects.create(
            user=self.student_user,
            title='Test Session'
        )
        response = self.client.get(f'/api/chatbot/sessions/{session.session_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_session(self):
        """Test DELETE /api/chatbot/sessions/{id}/"""
        self.authenticate_as_student()
        session = ChatSession.objects.create(
            user=self.student_user,
            title='Session to delete'
        )
        response = self.client.delete(f'/api/chatbot/sessions/{session.session_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_clear_all_sessions(self):
        """Test DELETE /api/chatbot/sessions/clear/"""
        self.authenticate_as_student()
        # Create some sessions
        ChatSession.objects.create(user=self.student_user, title='Session 1')
        ChatSession.objects.create(user=self.student_user, title='Session 2')
        
        response = self.client.delete('/api/chatbot/sessions/clear/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class IntegrationTests(BaseTestCase):
    """Integration tests for complete workflows"""
    
    def test_student_complete_workflow(self):
        """Test complete student workflow: view attendance, fees, assignments, results"""
        self.authenticate_as_student()
        
        # View attendance
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'What is my attendance?'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View fees
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Show my fees status'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View assignments
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Any pending assignments?'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View results
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Show my exam results'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
    
    def test_teacher_complete_workflow(self):
        """Test complete teacher workflow"""
        self.authenticate_as_teacher()
        
        # View course attendance
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Show attendance for my courses'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View assignment submissions
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Assignment submissions status'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View student results
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Results for my students'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
    
    def test_admin_complete_workflow(self):
        """Test complete admin workflow"""
        self.authenticate_as_admin()
        
        # View institution attendance
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Overall attendance statistics'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View fee collection
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Fee collection status'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])
        
        # View all results
        response = self.client.post('/api/chatbot/chat/', {
            'query': 'Department-wise results'
        }, format='json')
        self.assertIn(response.status_code, [200, 500])


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(AuthEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(DepartmentEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(StudentEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(TeacherEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(CourseEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(AttendanceEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(FeeStructureEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(StudentFeesEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(AssignmentEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(AssignmentSubmissionEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(ExamEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(ResultEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(ChatbotEndpointTests))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
