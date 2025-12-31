from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
import uuid
from saara.authapp.models import User

class Department(models.Model):
    """Department Model"""
    department_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    department_name = models.CharField(max_length=255)
    hod_id = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = "departments"
    
    def __str__(self):
        return self.department_name
    
class Student(models.Model):
    """Student Profile Model"""
    student_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='students')
    program = models.CharField(max_length=100)
    year_of_study = models.IntegerField()
    semester = models.IntegerField()
    
    class Meta:
        db_table = "students"
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

class Teacher(models.Model):
    """Teacher profile model"""
    teacher_id = models.CharField(primary_key=True, max_length=50)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='teachers')
    designation = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'teachers'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.teacher_id})"

class Admin(models.Model):
    admin_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    name = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'admins'
    
    def __str__(self):
        return f"{self.name} ({self.admin_id})"
    
class Course(models.Model):
    course_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_name = models.CharField(max_length=255)
    credits = models.IntegerField()
    semester = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    
    class Meta:
        db_table = 'course'
        
    def __str__(self):
        return f"{self.course_name} ({self.course_id})"
    
class CourseFaculty(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='faculty_assignments')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_assignments')
    
    class Meta:
        db_table = 'course_faculty'
        unique_together = ('course', 'teacher')
        
    def __str__(self):
        return f"{self.teacher} teaches {self.course}"
    
class Attendance(models.Model):
    STATUS_CHOICE = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    attendence_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICE)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ('student', 'course', 'date')
        
    def __str__(self):
        return f"{self.student} - {self.course} - {self.date} - {self.status}"
    
class FeeStructure(models.Model):
    """Fee structure for different academic years and semesters"""
    fee_id = models.CharField(primary_key=True, max_length=50)
    academic_year = models.IntegerField()
    semester = models.IntegerField()
    tution_fees = models.DecimalField(max_digits=10, decimal_places=2)
    development_fees = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        db_table = 'fee_structure'

    def save(self, *args, **kwargs):
        self.amount = self.tution_fees + self.development_fees
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fee {self.fee_id} - AY {self.academic_year} - Sem {self.semester}"



class StudentFees(models.Model):
    """Student fee payments"""
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
    ]
    
    payment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='student_payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    class Meta:
        db_table = 'student_fees'
    
    def __str__(self):
        return f"{self.student} - {self.fee} - {self.status}"
    
class Assignment(models.Model):
    assignments_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=400)
    file_url = models.CharField(max_length=255)
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='created_assignments')
    
    class Meta:
        db_table = 'assignments'
    
    def __str__(self):
        return f"{self.title} - {self.course}"


class AssignmentSubmission(models.Model):
    """Assignment submission records"""
    submission_id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    submitted_date = models.DateField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'assignment_submissions'
        unique_together = ('assignment', 'student')
    
    def __str__(self):
        return f"{self.student} - {self.assignment} - {self.submitted_date}"


class Exam(models.Model):
    """Exam model"""
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('quiz', 'Quiz'),
        ('practical', 'Practical'),
    ]
    
    exam_id = models.CharField(primary_key=True, max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES)
    exam_date = models.DateField()
    total_marks = models.IntegerField()
    
    class Meta:
        db_table = 'exams'
    
    def __str__(self):
        return f"{self.exam_type} - {self.course} - {self.exam_date}"


class Result(models.Model):
    """Exam results"""
    GRADE_CHOICES = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    ]
    
    result_id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5, choices=GRADE_CHOICES)
    
    class Meta:
        db_table = 'results'
        unique_together = ('exam', 'student')
    
    def __str__(self):
        return f"{self.student} - {self.exam} - {self.grade}"