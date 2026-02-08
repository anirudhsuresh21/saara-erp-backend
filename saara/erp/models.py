from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
import uuid
from saara.authapp.models import User


class Institution(models.Model):
    """Institution/College Model - supports multi-tenancy"""
    institution_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, unique=True)  # e.g., "SIES", "DYPATIL"
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "institutions"
    
    def __str__(self):
        return f"{self.name} ({self.short_name})"


class Department(models.Model):
    """Department Model"""
    PROGRAM_TYPE_CHOICES = [
        ('ug', 'Undergraduate'),      # BSc, BA, BCom, etc.
        ('pg', 'Postgraduate'),       # MSc, MA, MCom, MCA, MBA, etc.
        ('engg', 'Engineering'),      # BTech, BE, MTech, ME
        ('diploma', 'Diploma'),
        ('phd', 'Doctoral'),
        ('other', 'Other'),
    ]
    
    department_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='departments', null=True, blank=True)
    department_name = models.CharField(max_length=255)  # e.g., "Computer Science", "Management Studies"
    dept_code = models.CharField(max_length=20, null=True, blank=True)  # e.g., "CS", "MMS", "MCA"
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPE_CHOICES, default='ug')
    hod_id = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = "departments"
        unique_together = ('institution', 'dept_code', 'program_type')
    
    def __str__(self):
        program_label = dict(self.PROGRAM_TYPE_CHOICES).get(self.program_type, '')
        if self.institution:
            return f"{self.department_name} ({program_label}) - {self.institution.short_name}"
        return f"{self.department_name} ({program_label})"
    
class Student(models.Model):
    """Student Profile Model"""
    student_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, default='')
    last_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='students')
    program = models.CharField(max_length=100)
    year_of_study = models.IntegerField()
    semester = models.IntegerField()
    
    class Meta:
        db_table = "students"
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.roll_no or self.student_id})"

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
    course_id = models.CharField(primary_key=True, max_length=50)  # Course code like "MCA11", "MMS101"
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


class StudentCourse(models.Model):
    """Student course enrollment/registration"""
    enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_enrollments')
    academic_year = models.IntegerField()
    semester = models.IntegerField()
    enrollment_date = models.DateField(auto_now_add=True)
    grade = models.CharField(max_length=5, null=True, blank=True)  # Final grade for the course
    
    class Meta:
        db_table = 'student_courses'
        unique_together = ('student', 'course', 'academic_year', 'semester')
        ordering = ['-academic_year', '-semester']
    
    def __str__(self):
        return f"{self.student} - {self.course}"


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
    """Fee structure for different departments, academic years and semesters"""
    fee_id = models.CharField(primary_key=True, max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.IntegerField()
    # semester = models.IntegerField()
    tution_fees = models.DecimalField(max_digits=10, decimal_places=2)
    development_fees = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        db_table = 'fee_structure'
        unique_together = ('department', 'academic_year')

    def save(self, *args, **kwargs):
        self.amount = self.tution_fees + self.development_fees
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fee {self.fee_id} - {self.department.department_name} - AY {self.academic_year}"



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
    receipt_number = models.CharField(max_length=100, blank=True, default='')
    payment_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, default='')
    
    class Meta:
        db_table = 'student_fees'
    
    def __str__(self):
        return f"{self.student} - {self.fee} - {self.status}"
    
class Assignment(models.Model):
    assignments_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=400, blank=True, default='')
    file_url = models.CharField(max_length=255, blank=True, default='')
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


class Announcement(models.Model):
    """Announcements posted by teachers/admins"""
    TARGET_CHOICES = [
        ('all', 'All'),
        ('students', 'Students Only'),
        ('teachers', 'Teachers Only'),
        ('department', 'Department Specific'),
        ('course', 'Course Specific'),
    ]
    
    announcement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"


class Timetable(models.Model):
    """Timetable/Schedule for courses"""
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    timetable_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timetable_slots')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=50, blank=True, default='')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'timetables'
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.course.course_name} - {self.day_of_week} {self.start_time}-{self.end_time}"


class AcademicCalendar(models.Model):
    """Academic calendar events - exams, holidays, etc."""
    EVENT_TYPE_CHOICES = [
        ('exam', 'Examination'),
        ('holiday', 'Holiday'),
        ('event', 'Event'),
        ('deadline', 'Deadline'),
        ('semester_start', 'Semester Start'),
        ('semester_end', 'Semester End'),
    ]
    
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'academic_calendar'
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.title} ({self.start_date})"


class LeaveRequest(models.Model):
    """Leave requests from students and teachers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('emergency', 'Emergency Leave'),
        ('other', 'Other'),
    ]
    
    leave_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.leave_type} ({self.start_date} to {self.end_date})"