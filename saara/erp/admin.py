from django.contrib import admin
from django.contrib import admin
from .models import (
    Department, Student, Teacher, Admin,
    Course, CourseFaculty, Attendance, FeeStructure, StudentFees,
    Assignment, AssignmentSubmission, Exam, Result
)
# Register your models here.
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['department_id', 'department_name', 'hod_id']
    search_fields = ['department_name', 'department_id']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'department', 'year_of_study', 'semester']
    list_filter = ['department', 'year_of_study', 'semester']
    search_fields = ['student_id', 'first_name', 'last_name']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'first_name', 'last_name', 'department', 'designation']
    list_filter = ['department', 'designation']
    search_fields = ['teacher_id', 'first_name', 'last_name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_id', 'course_name', 'credits', 'semester', 'department']
    list_filter = ['department', 'semester']
    search_fields = ['course_id', 'course_name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['attendence_id', 'student', 'course', 'date', 'status']
    list_filter = ['status', 'date', 'course']
    search_fields = ['student__student_id', 'student__first_name', 'student__last_name']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['fee_id', 'academic_year', 'semester', 'amount']
    list_filter = ['academic_year', 'semester']


@admin.register(StudentFees)
class StudentFeesAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'student', 'fee', 'amount_paid', 'due_amount', 'status']
    list_filter = ['status', 'fee']
    search_fields = ['student__student_id', 'student__first_name']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['assignments_id', 'title', 'course', 'due_date', 'created_by']
    list_filter = ['course', 'due_date']
    search_fields = ['title', 'assignments_id']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['exam_id', 'course', 'exam_type', 'exam_date', 'total_marks']
    list_filter = ['exam_type', 'exam_date', 'course']
    search_fields = ['exam_id']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['result_id', 'student', 'exam', 'marks_obtained', 'grade']
    list_filter = ['grade', 'exam']
    search_fields = ['student__student_id', 'student__first_name']


admin.site.register(Admin)
admin.site.register(CourseFaculty)
admin.site.register(AssignmentSubmission)