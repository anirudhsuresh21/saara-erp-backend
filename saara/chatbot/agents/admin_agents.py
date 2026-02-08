from saara.erp.models import (
    Attendance, Course, Student, Teacher, Department,
    StudentFees, FeeStructure, Assignment, AssignmentSubmission,
    Result, Exam, Admin, StudentCourse, Announcement, Timetable,
    AcademicCalendar, LeaveRequest
)
from saara.authapp.models import User, AllowedEmailDomain
from django.db.models import Count, Q, Avg, Sum
from datetime import datetime, date
import uuid


class AdminAttendanceAgent:
    """Agent to handle attendance-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_attendance(self, course_id: str = None, department_id: str = None):
        """
        Get attendance overview for admin
        """
        query = Attendance.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(student__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        total_records = query.count()
        if total_records == 0:
            return {"error": "No attendance records found."}
        
        present_count = query.filter(Q(status='present') | Q(status='late')).count()
        absent_count = query.filter(status='absent').count()
        
        overall_attendance = (present_count / total_records) * 100 if total_records > 0 else 0
        
        # Department-wise breakdown
        dept_breakdown = []
        departments = Department.objects.all()
        for dept in departments:
            dept_records = query.filter(student__department=dept)
            dept_total = dept_records.count()
            if dept_total > 0:
                dept_present = dept_records.filter(Q(status='present') | Q(status='late')).count()
                dept_breakdown.append({
                    "department": dept.department_name,
                    "total_records": dept_total,
                    "attendance_percentage": round((dept_present / dept_total) * 100, 2)
                })

        return {
            "admin_name": self.admin.name,
            "total_records": total_records,
            "overall_attendance": round(overall_attendance, 2),
            "present": present_count,
            "absent": absent_count,
            "department_breakdown": dept_breakdown
        }

    def get_low_attendance_students(self, threshold: int = 75, department_id: str = None):
        """
        Get students with attendance below a specified threshold across all courses.
        
        Args:
            threshold: Attendance percentage threshold (default 75%)
            department_id: Optional department to filter by
        
        Returns:
            Dictionary with students who have attendance below threshold
        """
        students_query = Student.objects.all()
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id) |
                Q(dept_code__icontains=department_id)
            ).first()
            if dept:
                students_query = students_query.filter(department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}
        
        low_attendance_data = []
        
        for student in students_query:
            # Get all attendance records for this student
            attendance_records = Attendance.objects.filter(student=student)
            total_classes = attendance_records.count()
            
            if total_classes == 0:
                continue
            
            present_count = attendance_records.filter(
                Q(status='present') | Q(status='late')
            ).count()
            
            attendance_percentage = (present_count / total_classes) * 100
            
            if attendance_percentage < threshold:
                low_attendance_data.append({
                    "name": f"{student.first_name} {student.last_name}",
                    "roll_no": student.roll_no or str(student.student_id)[:8],
                    "department": student.department.department_name if student.department else "N/A",
                    "program": student.program,
                    "year": student.year_of_study,
                    "attendance_percentage": round(attendance_percentage, 2),
                    "present": present_count,
                    "total": total_classes,
                    "absent": total_classes - present_count
                })
        
        if not low_attendance_data:
            return {
                "admin_name": self.admin.name,
                "threshold": threshold,
                "message": f"Great news! No students have attendance below {threshold}%.",
                "students": []
            }
        
        # Sort by attendance percentage (lowest first)
        low_attendance_data.sort(key=lambda x: x['attendance_percentage'])
        
        # Group by department for summary
        dept_summary = {}
        for student in low_attendance_data:
            dept = student['department']
            if dept not in dept_summary:
                dept_summary[dept] = 0
            dept_summary[dept] += 1
        
        return {
            "admin_name": self.admin.name,
            "threshold": threshold,
            "total_students_below_threshold": len(low_attendance_data),
            "department_summary": [{"department": k, "count": v} for k, v in dept_summary.items()],
            "students": low_attendance_data[:50]  # Limit to first 50
        }


class AdminFeesAgent:
    """Agent to handle fees-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_fees(self, department_id: str = None):
        """
        Get fee collection overview for admin
        """
        query = StudentFees.objects.all()
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(student__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        if not query.exists():
            return {"error": "No fee records found."}

        total_collected = query.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_pending = query.aggregate(total=Sum('due_amount'))['total'] or 0
        
        # Status breakdown
        paid_count = query.filter(status='paid').count()
        partial_count = query.filter(status='partial').count()
        pending_count = query.filter(status='pending').count()
        overdue_count = query.filter(status='overdue').count()
        
        # Department-wise breakdown
        dept_breakdown = []
        departments = Department.objects.all()
        for dept in departments:
            dept_fees = query.filter(student__department=dept)
            if dept_fees.exists():
                dept_collected = dept_fees.aggregate(total=Sum('amount_paid'))['total'] or 0
                dept_pending = dept_fees.aggregate(total=Sum('due_amount'))['total'] or 0
                dept_breakdown.append({
                    "department": dept.department_name,
                    "collected": float(dept_collected),
                    "pending": float(dept_pending)
                })

        return {
            "admin_name": self.admin.name,
            "total_collected": float(total_collected),
            "total_pending": float(total_pending),
            "collection_rate": round((total_collected / (total_collected + total_pending)) * 100, 2) if (total_collected + total_pending) > 0 else 0,
            "status_breakdown": {
                "paid": paid_count,
                "partial": partial_count,
                "pending": pending_count,
                "overdue": overdue_count
            },
            "department_breakdown": dept_breakdown
        }


class AdminAssignmentAgent:
    """Agent to handle assignment-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_assignments(self, course_id: str = None, department_id: str = None):
        """
        Get assignment overview for admin
        """
        query = Assignment.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(course__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        assignments = query.select_related('course', 'created_by').all()
        
        if not assignments:
            return {"error": "No assignments found."}

        total_assignments = len(assignments)
        total_submissions = AssignmentSubmission.objects.filter(
            assignment__in=assignments
        ).count()
        
        # Get assignment summary by course
        course_summary = {}
        for assignment in assignments:
            course_name = assignment.course.course_name
            if course_name not in course_summary:
                course_summary[course_name] = {
                    "assignments": 0,
                    "submissions": 0
                }
            course_summary[course_name]["assignments"] += 1
            course_summary[course_name]["submissions"] += AssignmentSubmission.objects.filter(
                assignment=assignment
            ).count()

        return {
            "admin_name": self.admin.name,
            "total_assignments": total_assignments,
            "total_submissions": total_submissions,
            "course_summary": [
                {"course": k, **v} for k, v in course_summary.items()
            ]
        }

    def get_pending_submissions(self, course_id: str = None, department_id: str = None):
        """
        Get a comprehensive list of students who haven't submitted assignments.
        
        Args:
            course_id: Optional course ID/name to filter by
            department_id: Optional department to filter by
        
        Returns:
            Dictionary with pending submission details organized by assignment
        """
        query = Assignment.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id) |
                Q(dept_code__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(course__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}
        
        assignments = query.select_related('course', 'created_by').all()
        
        if not assignments:
            return {"error": "No assignments found matching your criteria."}
        
        pending_data = []
        total_pending_students = 0
        
        for assignment in assignments:
            # Get students enrolled in this course
            enrolled_students = StudentCourse.objects.filter(
                course=assignment.course
            ).select_related('student')
            
            # Get students who have submitted
            submitted_student_ids = set(
                AssignmentSubmission.objects.filter(
                    assignment=assignment
                ).values_list('student_id', flat=True)
            )
            
            # Find students who haven't submitted
            pending_students = []
            for enrollment in enrolled_students:
                if enrollment.student.student_id not in submitted_student_ids:
                    pending_students.append({
                        "name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
                        "roll_no": enrollment.student.roll_no or str(enrollment.student.student_id)[:8],
                        "department": enrollment.student.department.department_name if enrollment.student.department else "N/A"
                    })
            
            if pending_students:
                is_overdue = assignment.due_date.date() < assignment.due_date.now().date()
                
                pending_data.append({
                    "assignment_title": assignment.title,
                    "course_name": assignment.course.course_name,
                    "created_by": f"{assignment.created_by.first_name} {assignment.created_by.last_name}" if assignment.created_by else "Unknown",
                    "due_date": assignment.due_date.strftime("%Y-%m-%d %H:%M"),
                    "is_overdue": is_overdue,
                    "total_enrolled": enrolled_students.count(),
                    "submitted_count": len(submitted_student_ids),
                    "pending_count": len(pending_students),
                    "pending_students": pending_students[:20]  # Limit per assignment
                })
                total_pending_students += len(pending_students)
        
        if not pending_data:
            return {
                "admin_name": self.admin.name,
                "message": "All students have submitted their assignments!",
                "assignments_summary": []
            }
        
        return {
            "admin_name": self.admin.name,
            "total_assignments_with_pending": len(pending_data),
            "total_pending_students": total_pending_students,
            "assignments_summary": pending_data
        }


class AdminResultsAgent:
    """Agent to handle results-related queries for admins"""
    
    def __init__(self, admin):
        self.admin = admin

    def get_results(self, course_id: str = None, exam_type: str = None, department_id: str = None):
        """
        Get results overview for admin
        """
        query = Result.objects.all()
        
        if course_id:
            course = Course.objects.filter(
                Q(course_name__icontains=course_id) | 
                Q(course_id__icontains=course_id)
            ).first()
            if course:
                query = query.filter(exam__course=course)
            else:
                return {"error": f"Course '{course_id}' not found."}
        
        if exam_type:
            query = query.filter(exam__exam_type__iexact=exam_type)
        
        if department_id:
            dept = Department.objects.filter(
                Q(department_name__icontains=department_id)
            ).first()
            if dept:
                query = query.filter(student__department=dept)
            else:
                return {"error": f"Department '{department_id}' not found."}

        results = query.select_related('exam', 'exam__course', 'student').all()
        
        if not results:
            return {"error": "No results found."}

        total_students = query.values('student').distinct().count()
        avg_percentage = 0
        
        # Calculate overall statistics
        total_marks_obtained = sum(float(r.marks_obtained) for r in results)
        total_marks_possible = sum(r.exam.total_marks for r in results)
        
        if total_marks_possible > 0:
            avg_percentage = (total_marks_obtained / total_marks_possible) * 100
        
        # Grade distribution
        grade_dist = query.values('grade').annotate(count=Count('grade'))
        
        # Department-wise performance
        dept_performance = []
        departments = Department.objects.all()
        for dept in departments:
            dept_results = query.filter(student__department=dept)
            if dept_results.exists():
                dept_marks = sum(float(r.marks_obtained) for r in dept_results)
                dept_total = sum(r.exam.total_marks for r in dept_results)
                dept_avg = (dept_marks / dept_total) * 100 if dept_total > 0 else 0
                dept_performance.append({
                    "department": dept.department_name,
                    "students": dept_results.values('student').distinct().count(),
                    "average_percentage": round(dept_avg, 2)
                })

        return {
            "admin_name": self.admin.name,
            "total_results": len(results),
            "total_students": total_students,
            "overall_average": round(avg_percentage, 2),
            "grade_distribution": {g['grade']: g['count'] for g in grade_dist},
            "department_performance": dept_performance
        }


class AdminUserManagementAgent:
    """Agent to handle user management for admins - add teachers and students"""
    
    def __init__(self, admin):
        self.admin = admin
    
    def add_teacher(self, email: str, first_name: str, last_name: str, 
                    department_name: str, designation: str = "Assistant Professor",
                    password: str = None):
        """
        Add a new teacher to the system
        """
        # Validate email domain
        if not AllowedEmailDomain.is_domain_allowed(email):
            domain = AllowedEmailDomain.get_domain_from_email(email)
            return {
                "success": False,
                "error": f"Email domain '{domain}' is not authorized. Please use an institutional email."
            }
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return {
                "success": False,
                "error": f"A user with email '{email}' already exists."
            }
        
        # Find department
        department = Department.objects.filter(
            Q(department_name__icontains=department_name) |
            Q(dept_code__icontains=department_name)
        ).first()
        
        if not department:
            # List available departments
            available_depts = list(Department.objects.values_list('department_name', flat=True))
            return {
                "success": False,
                "error": f"Department '{department_name}' not found.",
                "available_departments": available_depts
            }
        
        try:
            # Create user account
            user = User.objects.create(
                email=email,
                role='faculty',
                is_active=True
            )
            # Set password (use default if not provided)
            default_password = password or f"{first_name.lower()}@123"
            user.set_password(default_password)
            user.save()
            
            # Generate teacher ID
            teacher_id = f"T{str(uuid.uuid4())[:8].upper()}"
            
            # Create teacher profile
            teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                user=user,
                first_name=first_name,
                last_name=last_name,
                department=department,
                designation=designation
            )
            
            return {
                "success": True,
                "message": f"Teacher '{first_name} {last_name}' added successfully!",
                "teacher_id": teacher_id,
                "email": email,
                "department": department.department_name,
                "designation": designation,
                "default_password": default_password
            }
            
        except Exception as e:
            # Rollback user creation if teacher creation fails
            User.objects.filter(email=email).delete()
            return {
                "success": False,
                "error": f"Failed to create teacher: {str(e)}"
            }
    
    def add_student(self, email: str, first_name: str, last_name: str,
                    department_name: str, program: str, year_of_study: int = 1,
                    semester: int = 1, middle_name: str = "", password: str = None,
                    roll_no: str = None):
        """
        Add a new student to the system
        """
        # Validate email domain
        if not AllowedEmailDomain.is_domain_allowed(email):
            domain = AllowedEmailDomain.get_domain_from_email(email)
            return {
                "success": False,
                "error": f"Email domain '{domain}' is not authorized. Please use an institutional email."
            }
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return {
                "success": False,
                "error": f"A user with email '{email}' already exists."
            }
        
        # Find department
        department = Department.objects.filter(
            Q(department_name__icontains=department_name) |
            Q(dept_code__icontains=department_name)
        ).first()
        
        if not department:
            # List available departments
            available_depts = list(Department.objects.values_list('department_name', flat=True))
            return {
                "success": False,
                "error": f"Department '{department_name}' not found.",
                "available_departments": available_depts
            }
        
        # Auto-generate roll number if not provided
        if not roll_no:
            roll_no = self._generate_roll_number(department.dept_code, year_of_study)
        else:
            # Check if roll_no already exists
            if Student.objects.filter(roll_no=roll_no).exists():
                return {
                    "success": False,
                    "error": f"A student with roll number '{roll_no}' already exists."
                }
        
        try:
            # Create user account
            user = User.objects.create(
                email=email,
                role='student',
                is_active=True
            )
            # Set password (use default if not provided)
            default_password = password or f"{first_name.lower()}@123"
            user.set_password(default_password)
            user.save()
            
            # Create student profile
            student = Student.objects.create(
                user=user,
                roll_no=roll_no,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                department=department,
                program=program,
                year_of_study=year_of_study,
                semester=semester
            )
            
            # Auto-enroll student in courses based on department and semester
            enrolled_courses = self._enroll_student_in_courses(student, department, semester)
            
            return {
                "success": True,
                "message": f"Student '{first_name} {last_name}' added successfully!",
                "student_id": str(student.student_id),
                "roll_no": roll_no,
                "email": email,
                "department": department.department_name,
                "program": program,
                "year_of_study": year_of_study,
                "semester": semester,
                "default_password": default_password,
                "enrolled_courses": enrolled_courses
            }
            
        except Exception as e:
            # Rollback user creation if student creation fails
            User.objects.filter(email=email).delete()
            return {
                "success": False,
                "error": f"Failed to create student: {str(e)}"
            }
    
    def _enroll_student_in_courses(self, student, department, semester):
        """
        Automatically enroll a student in all courses for their department and semester
        Returns list of enrolled course names
        """
        enrolled_courses = []
        
        # Get current academic year
        current_year = datetime.now().year
        academic_year = current_year if datetime.now().month >= 6 else current_year - 1
        
        # Find all courses for the student's department and semester
        courses = Course.objects.filter(
            department=department,
            semester=semester
        )
        
        for course in courses:
            try:
                # Check if enrollment already exists
                if not StudentCourse.objects.filter(
                    student=student,
                    course=course,
                    academic_year=academic_year,
                    semester=semester
                ).exists():
                    # Create enrollment
                    StudentCourse.objects.create(
                        student=student,
                        course=course,
                        academic_year=academic_year,
                        semester=semester
                    )
                    enrolled_courses.append({
                        "course_id": course.course_id,
                        "course_name": course.course_name,
                        "credits": course.credits
                    })
            except Exception as e:
                print(f"Error enrolling in course {course.course_id}: {e}")
                continue
        
        return enrolled_courses
    
    def _generate_roll_number(self, dept_code: str, year_of_study: int) -> str:
        """
        Auto-generate roll number for a student based on department and year.
        Format: MCA1001 for Year 1, MCA2001 for Year 2
        
        Args:
            dept_code: Department code (e.g., 'MCA', 'MMS')
            year_of_study: Year of study (1 or 2)
        
        Returns:
            Generated roll number string
        """
        # Base number: 1001 for Year 1, 2001 for Year 2
        base_number = year_of_study * 1000 + 1
        
        # Get the highest existing roll number for this department and year
        prefix = f"{dept_code}{year_of_study}"
        existing_students = Student.objects.filter(
            roll_no__startswith=prefix
        ).order_by('-roll_no')
        
        if existing_students.exists():
            # Extract the number from the last roll number
            last_roll_no = existing_students.first().roll_no
            try:
                # Extract the numeric part after the prefix (e.g., MCA1001 -> 1001)
                last_number = int(last_roll_no[len(dept_code):])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = base_number
        else:
            next_number = base_number
        
        return f"{dept_code}{next_number}"
    
    def get_departments(self):
        """Get list of all departments for selection"""
        departments = Department.objects.all()
        return {
            "departments": [
                {
                    "id": str(d.department_id),
                    "name": d.department_name,
                    "code": d.dept_code,
                    "program_type": d.program_type
                }
                for d in departments
            ]
        }
    
    def parse_add_user_request(self, query: str, user_type: str):
        """
        Parse natural language request to extract user details
        Returns parsed data or prompts for missing information
        """
        query_lower = query.lower()
        
        # This is a simple parser - the actual parsing will be done by Gemini in the NLP module
        return {
            "type": user_type,
            "requires_details": True,
            "message": f"Please provide the following details to add a {user_type}:\n"
                      f"- Email address\n"
                      f"- First name\n"
                      f"- Last name\n"
                      f"- Department\n"
                      + ("- Designation (optional)\n" if user_type == "teacher" else "- Program (e.g., MCA, MBA)\n- Year of study\n- Semester\n")
        }
    
    def update_student(self, identifier: str, **update_fields):
        """
        Update an existing student's details
        
        Args:
            identifier: Roll number (e.g., MCA1001) or student email
            **update_fields: Fields to update (semester, year_of_study, program, department, etc.)
        """
        # Find student by roll_no or email
        student = None
        
        # Try finding by roll_no first
        student = Student.objects.filter(roll_no__iexact=identifier).first()
        
        # If not found, try email
        if not student:
            student = Student.objects.filter(user__email__iexact=identifier).first()
        
        if not student:
            return {
                "success": False,
                "error": f"Student with identifier '{identifier}' not found. Please provide a valid roll number (e.g., MCA1001) or email."
            }
        
        # Track what was updated
        updated_fields = []
        old_values = {}
        
        # Update semester
        if 'semester' in update_fields and update_fields['semester'] is not None:
            old_values['semester'] = student.semester
            student.semester = int(update_fields['semester'])
            updated_fields.append(f"Semester: {old_values['semester']} → {student.semester}")
        
        # Update year_of_study
        if 'year_of_study' in update_fields and update_fields['year_of_study'] is not None:
            old_values['year_of_study'] = student.year_of_study
            student.year_of_study = int(update_fields['year_of_study'])
            updated_fields.append(f"Year: {old_values['year_of_study']} → {student.year_of_study}")
        
        # Update program
        if 'program' in update_fields and update_fields['program'] is not None:
            old_values['program'] = student.program
            student.program = update_fields['program']
            updated_fields.append(f"Program: {old_values['program']} → {student.program}")
        
        # Update department
        if 'department' in update_fields and update_fields['department'] is not None:
            dept = Department.objects.filter(
                Q(department_name__icontains=update_fields['department']) |
                Q(dept_code__icontains=update_fields['department'])
            ).first()
            if dept:
                old_dept = student.department.department_name if student.department else 'None'
                student.department = dept
                updated_fields.append(f"Department: {old_dept} → {dept.department_name}")
            else:
                return {
                    "success": False,
                    "error": f"Department '{update_fields['department']}' not found."
                }
        
        if not updated_fields:
            return {
                "success": False,
                "error": "No valid fields to update were provided."
            }
        
        try:
            student.save()
            return {
                "success": True,
                "message": f"Student '{student.roll_no}' updated successfully!",
                "student_name": f"{student.first_name} {student.last_name}",
                "roll_no": student.roll_no,
                "updates": updated_fields
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update student: {str(e)}"
            }
    
    def update_teacher(self, identifier: str, **update_fields):
        """
        Update an existing teacher's details
        
        Args:
            identifier: Teacher ID (e.g., MCA001) or teacher email
            **update_fields: Fields to update (designation, department, etc.)
        """
        # Find teacher by teacher_id or email
        teacher = None
        
        # Try finding by teacher_id first
        teacher = Teacher.objects.filter(teacher_id__iexact=identifier).first()
        
        # If not found, try email
        if not teacher:
            teacher = Teacher.objects.filter(user__email__iexact=identifier).first()
        
        if not teacher:
            return {
                "success": False,
                "error": f"Teacher with identifier '{identifier}' not found. Please provide a valid teacher ID (e.g., MCA001) or email."
            }
        
        # Track what was updated
        updated_fields = []
        old_values = {}
        
        # Update designation
        if 'designation' in update_fields and update_fields['designation'] is not None:
            old_values['designation'] = teacher.designation
            teacher.designation = update_fields['designation']
            updated_fields.append(f"Designation: {old_values['designation']} → {teacher.designation}")
        
        # Update department
        if 'department' in update_fields and update_fields['department'] is not None:
            dept = Department.objects.filter(
                Q(department_name__icontains=update_fields['department']) |
                Q(dept_code__icontains=update_fields['department'])
            ).first()
            if dept:
                old_dept = teacher.department.department_name if teacher.department else 'None'
                teacher.department = dept
                updated_fields.append(f"Department: {old_dept} → {dept.department_name}")
            else:
                return {
                    "success": False,
                    "error": f"Department '{update_fields['department']}' not found."
                }
        
        # Update first_name
        if 'first_name' in update_fields and update_fields['first_name'] is not None:
            old_values['first_name'] = teacher.first_name
            teacher.first_name = update_fields['first_name']
            updated_fields.append(f"First Name: {old_values['first_name']} → {teacher.first_name}")
        
        # Update last_name
        if 'last_name' in update_fields and update_fields['last_name'] is not None:
            old_values['last_name'] = teacher.last_name
            teacher.last_name = update_fields['last_name']
            updated_fields.append(f"Last Name: {old_values['last_name']} → {teacher.last_name}")
        
        if not updated_fields:
            return {
                "success": False,
                "error": "No valid fields to update were provided."
            }
        
        try:
            teacher.save()
            return {
                "success": True,
                "message": f"Teacher '{teacher.teacher_id}' updated successfully!",
                "teacher_name": f"{teacher.first_name} {teacher.last_name}",
                "teacher_id": teacher.teacher_id,
                "updates": updated_fields
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update teacher: {str(e)}"
            }
    
    def delete_student(self, identifier: str):
        """Delete a student by roll_no or email"""
        student = Student.objects.filter(roll_no__iexact=identifier).first()
        if not student:
            student = Student.objects.filter(user__email__iexact=identifier).first()
        
        if not student:
            return {
                "success": False,
                "error": f"Student with identifier '{identifier}' not found."
            }
        
        student_name = f"{student.first_name} {student.last_name}"
        roll_no = student.roll_no
        user_email = student.user.email
        
        try:
            # Delete user (cascades to student)
            student.user.delete()
            return {
                "success": True,
                "message": f"Student '{student_name}' (Roll: {roll_no}) deleted successfully!",
                "deleted_email": user_email
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete student: {str(e)}"
            }
    
    def delete_teacher(self, identifier: str):
        """Delete a teacher by teacher_id or email"""
        teacher = Teacher.objects.filter(teacher_id__iexact=identifier).first()
        if not teacher:
            teacher = Teacher.objects.filter(user__email__iexact=identifier).first()
        
        if not teacher:
            return {
                "success": False,
                "error": f"Teacher with identifier '{identifier}' not found."
            }
        
        teacher_name = f"{teacher.first_name} {teacher.last_name}"
        teacher_id = teacher.teacher_id
        user_email = teacher.user.email
        
        try:
            teacher.user.delete()
            return {
                "success": True,
                "message": f"Teacher '{teacher_name}' (ID: {teacher_id}) deleted successfully!",
                "deleted_email": user_email
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete teacher: {str(e)}"
            }
    
    def find_students(self, identifier=None, program=None, department=None, year_of_study=None, semester=None):
        """Find students based on various criteria"""
        query = Student.objects.select_related('department', 'user').all()
        
        # If specific identifier provided, find that student
        if identifier:
            student = query.filter(
                Q(roll_no__iexact=identifier) | Q(user__email__icontains=identifier)
            ).first()
            
            if student:
                return {
                    "success": True,
                    "single_result": True,
                    "student": {
                        "roll_no": student.roll_no,
                        "name": f"{student.first_name} {student.middle_name or ''} {student.last_name}".strip(),
                        "email": student.user.email,
                        "program": student.program,
                        "department": student.department.department_name if student.department else "N/A",
                        "year": student.year_of_study,
                        "semester": student.semester
                    }
                }
            else:
                return {"success": False, "error": f"Student '{identifier}' not found."}
        
        # Filter by criteria
        if program:
            query = query.filter(program__iexact=program)
        if department:
            query = query.filter(
                Q(department__department_name__icontains=department) |
                Q(department__dept_code__icontains=department)
            )
        if year_of_study:
            query = query.filter(year_of_study=year_of_study)
        if semester:
            query = query.filter(semester=semester)
        
        students = query[:50]  # Limit results
        
        if not students:
            return {"success": False, "error": "No students found matching the criteria."}
        
        return {
            "success": True,
            "single_result": False,
            "count": query.count(),
            "students": [
                {
                    "roll_no": s.roll_no,
                    "name": f"{s.first_name} {s.last_name}",
                    "program": s.program,
                    "year": s.year_of_study,
                    "semester": s.semester
                }
                for s in students
            ]
        }
    
    def find_teachers(self, identifier=None, department=None):
        """Find teachers based on criteria"""
        query = Teacher.objects.select_related('department', 'user').all()
        
        if identifier:
            teacher = query.filter(
                Q(teacher_id__iexact=identifier) | Q(user__email__icontains=identifier)
            ).first()
            
            if teacher:
                return {
                    "success": True,
                    "single_result": True,
                    "teacher": {
                        "teacher_id": teacher.teacher_id,
                        "name": f"{teacher.first_name} {teacher.last_name}",
                        "email": teacher.user.email,
                        "department": teacher.department.department_name if teacher.department else "N/A",
                        "designation": teacher.designation
                    }
                }
            else:
                return {"success": False, "error": f"Teacher '{identifier}' not found."}
        
        if department:
            query = query.filter(
                Q(department__department_name__icontains=department) |
                Q(department__dept_code__icontains=department)
            )
        
        teachers = query[:50]
        
        if not teachers:
            return {"success": False, "error": "No teachers found."}
        
        return {
            "success": True,
            "single_result": False,
            "count": query.count(),
            "teachers": [
                {
                    "teacher_id": t.teacher_id,
                    "name": f"{t.first_name} {t.last_name}",
                    "department": t.department.department_name if t.department else "N/A",
                    "designation": t.designation
                }
                for t in teachers
            ]
        }
    
    def reset_password(self, identifier: str, new_password: str = None):
        """Reset password for a user (student or teacher)"""
        user = None
        user_type = None
        user_name = None
        
        # Try student first
        student = Student.objects.filter(
            Q(roll_no__iexact=identifier) | Q(user__email__icontains=identifier)
        ).first()
        if student:
            user = student.user
            user_type = "student"
            user_name = f"{student.first_name} {student.last_name}"
        
        # Try teacher
        if not user:
            teacher = Teacher.objects.filter(
                Q(teacher_id__iexact=identifier) | Q(user__email__icontains=identifier)
            ).first()
            if teacher:
                user = teacher.user
                user_type = "teacher"
                user_name = f"{teacher.first_name} {teacher.last_name}"
        
        if not user:
            return {
                "success": False,
                "error": f"User with identifier '{identifier}' not found."
            }
        
        # Generate new password if not provided
        if not new_password:
            new_password = f"{identifier.lower()}@reset123"
        
        try:
            user.set_password(new_password)
            user.save()
            return {
                "success": True,
                "message": f"Password reset successfully for {user_type} '{user_name}'!",
                "user_type": user_type,
                "new_password": new_password,
                "email": user.email
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to reset password: {str(e)}"
            }
    
    def add_course(self, course_name: str, program: str, semester: int, credits: int = 4, course_id: str = None):
        """Add a new course to the system"""
        # Find department by program
        department = Department.objects.filter(
            Q(dept_code__iexact=program) | Q(department_name__icontains=program)
        ).first()
        
        if not department:
            return {
                "success": False,
                "error": f"Department/Program '{program}' not found."
            }
        
        # Generate course_id if not provided
        if not course_id:
            existing = Course.objects.filter(course_id__startswith=f"{program.upper()}{semester}").count()
            course_id = f"{program.upper()}{semester}{existing + 1:02d}"
        
        # Check if course already exists
        if Course.objects.filter(course_id=course_id).exists():
            return {
                "success": False,
                "error": f"Course with ID '{course_id}' already exists."
            }
        
        try:
            course = Course.objects.create(
                course_id=course_id,
                course_name=course_name,
                department=department,
                credits=credits,
                semester=semester
            )
            return {
                "success": True,
                "message": f"Course '{course_name}' added successfully!",
                "course_id": course_id,
                "department": department.department_name,
                "semester": semester,
                "credits": credits
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add course: {str(e)}"
            }
