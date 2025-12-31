from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, StudentViewSet, TeacherViewSet, AdminViewSet,
    CourseViewSet, CourseFacultyViewSet, AttendanceViewSet,
    FeeStructureViewSet, StudentFeesViewSet, AssignmentViewSet,
    AssignmentSubmissionViewSet, ExamViewSet, ResultViewSet
)

router = DefaultRouter()

# Register all viewsets with the router
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'admins', AdminViewSet, basename='admin')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'course-faculty', CourseFacultyViewSet, basename='course-faculty')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'fee-structure', FeeStructureViewSet, basename='fee-structure')
router.register(r'student-fees', StudentFeesViewSet, basename='student-fees')
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'submissions', AssignmentSubmissionViewSet, basename='submission')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'results', ResultViewSet, basename='result')

urlpatterns = [
    path('', include(router.urls)),
]
