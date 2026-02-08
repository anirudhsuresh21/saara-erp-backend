from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer, 
    ChatSessionListSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer
)
from .agents import (
    # Student agents
    AttendanceAgent, FeesAgent, AssignmentAgent, ResultsAgent,
    # Teacher agents
    TeacherAttendanceAgent, TeacherAssignmentAgent, TeacherResultsAgent,
    # Admin agents
    AdminAttendanceAgent, AdminFeesAgent, AdminAssignmentAgent, AdminResultsAgent,
    AdminUserManagementAgent
)
from .agents.general_agents import (
    TimetableAgent, AnnouncementAgent, AcademicCalendarAgent, LeaveAgent
)
from .nlp import parse_intent, make_chat_response
from saara.erp.models import Student, Teacher, Admin


class ChatView(APIView):
    """
    Main chat endpoint that routes to appropriate agents based on intent and user role.
    Supports students, teachers, and admins with role-based access control.
    """
    permission_classes = [IsAuthenticated]
    
    # Keywords restricted for students (they can only access their own data)
    STUDENT_RESTRICTED_KEYWORDS = [
        'teacher', 'faculty', 'admin', 'administrator', 'staff',
        'all students', 'other student', 'another student',
        'salary', 'payroll', 'teacher salary', 'faculty salary',
        'department head', 'hod', 'principal',
        'all results', 'class results', 'batch results',
        'all attendance', 'class attendance',
        'all fees', 'fee collection',
        'user credentials', 'password', 'login details'
    ]
    
    # Keywords restricted for teachers
    TEACHER_RESTRICTED_KEYWORDS = [
        'admin', 'administrator',
        'salary', 'payroll', 'my salary', 'teacher salary',
        'all teachers', 'other teacher',
        'user credentials', 'password', 'login details',
        'fee collection', 'total fees'
    ]
    
    def post(self, request):
        """
        Handle chat request based on user role
        """
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        session_id = serializer.validated_data.get('session_id')
        user = request.user
        
        print(f"\n=== NEW CHAT REQUEST ===")
        print(f"Query: {query}")
        print(f"User: {user}")
        print(f"User Role: {getattr(user, 'role', 'unknown')}")
        
        # Determine user role and get profile
        user_role, profile = self._get_user_role_and_profile(user)
        
        if user_role is None:
            return Response({
                "error": "Profile not found",
                "message": "No valid profile found for this user. Please contact administrator."
            }, status=status.HTTP_404_NOT_FOUND)
        
        print(f"Detected Role: {user_role}")
        
        # Check for restricted keywords based on role
        if user_role == 'student' and self._contains_restricted_query(query, self.STUDENT_RESTRICTED_KEYWORDS):
            return Response({
                "error": "Unauthorized",
                "message": "You are not authorized to access this information.",
                "response": "Sorry, I can only help you with your own academic information like attendance, fees, assignments, and exam results. I cannot provide information about teachers, admins, or other students. 🔒"
            }, status=status.HTTP_403_FORBIDDEN)
        
        if user_role == 'teacher' and self._contains_restricted_query(query, self.TEACHER_RESTRICTED_KEYWORDS):
            return Response({
                "error": "Unauthorized", 
                "message": "You are not authorized to access this information.",
                "response": "Sorry, I can only help you with information about your courses, students' attendance, assignments, and results. I cannot provide administrative or salary information. 🔒"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create chat session
        session = self._get_or_create_session(user, session_id)
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=query
        )
        
        # Parse intent using Gemini/NLP
        print("Parsing intent...")
        parsed = parse_intent(query)
        print(f"Parsed: {parsed}")
        
        intent = parsed.get("intent", "unknown")
        course_id = parsed.get("course_id")
        exam_type = parsed.get("exam_type")
        user_data = parsed.get("user_data")
        
        try:
            # Route to appropriate agent based on role
            print(f"Intent: {intent}, Course: {course_id}, Exam Type: {exam_type}, Role: {user_role}")
            
            if user_role == 'student':
                response_text = self._handle_student_query(profile, intent, course_id, exam_type, user_data)
            elif user_role == 'teacher':
                response_text = self._handle_teacher_query(profile, intent, course_id, exam_type, user_data)
            elif user_role == 'admin':
                response_text = self._handle_admin_query(profile, intent, course_id, exam_type, user_data)
            else:
                response_text = "Sorry, I couldn't determine your role. Please contact support."

            print(f"Response: {response_text[:100]}...")
            
            # Save assistant response
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=response_text
            )
            
            # Update session title if it's new
            if not session.title:
                session.title = query[:50] + ('...' if len(query) > 50 else '')
                session.save()
            
            return Response({
                "response": response_text,
                "intent": intent,
                "parsed": parsed,
                "session_id": str(session.session_id),
                "user_role": user_role
            })
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
            error_response = "Sorry, something went wrong while processing your request. Please try again later."
            
            # Save error response
            ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=error_response
            )
            
            return Response({
                "error": str(e),
                "response": error_response,
                "intent": intent,
                "parsed": parsed,
                "session_id": str(session.session_id)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_role_and_profile(self, user):
        """
        Determine user role and return the appropriate profile
        Returns tuple: (role_string, profile_object) or (None, None)
        """
        # Check for student profile
        try:
            student = Student.objects.get(user=user)
            return ('student', student)
        except Student.DoesNotExist:
            pass
        
        # Check for teacher profile
        try:
            teacher = Teacher.objects.get(user=user)
            return ('teacher', teacher)
        except Teacher.DoesNotExist:
            pass
        
        # Check for admin profile
        try:
            admin = Admin.objects.get(user=user)
            return ('admin', admin)
        except Admin.DoesNotExist:
            pass
        
        return (None, None)
    
    def _handle_student_query(self, student, intent, course_id, exam_type, user_data=None):
        """Handle queries for student users"""
        if intent == "attendance":
            agent = AttendanceAgent(student)
            raw_data = agent.get_attendance(course_id)
            return make_chat_response(raw_data, intent="attendance")
            
        elif intent == "fees":
            agent = FeesAgent(student)
            raw_data = agent.get_fees()
            return make_chat_response(raw_data, intent="fees")
            
        elif intent == "assignments":
            agent = AssignmentAgent(student)
            raw_data = agent.get_assignments(course_id)
            return make_chat_response(raw_data, intent="assignments")
            
        elif intent == "results":
            agent = ResultsAgent(student)
            raw_data = agent.get_results(course_id, exam_type)
            return make_chat_response(raw_data, intent="results")
        
        elif intent == "timetable":
            agent = TimetableAgent(student.user, student, 'student')
            raw_data = agent.get_timetable()
            return self._format_timetable_response(raw_data)
        
        elif intent == "announcements":
            agent = AnnouncementAgent(student.user, student, 'student')
            raw_data = agent.get_announcements()
            return self._format_announcements_response(raw_data)
        
        elif intent == "academic_calendar":
            agent = AcademicCalendarAgent(student.user, student, 'student')
            raw_data = agent.get_events()
            return self._format_calendar_response(raw_data)
        
        elif intent == "apply_leave":
            agent = LeaveAgent(student.user, student, 'student')
            return self._handle_apply_leave(agent, user_data)
        
        elif intent == "leave_status":
            agent = LeaveAgent(student.user, student, 'student')
            raw_data = agent.get_leave_status()
            return self._format_leave_status_response(raw_data)
            
        else:
            return """I'm not sure how to help with that. As a student, I can assist you with:

📊 **Attendance** - Check your attendance percentage and records
💰 **Fees** - View your fee status and payment details
📝 **Assignments** - See pending and submitted assignments
🎓 **Results** - Check your exam results and grades
📅 **Timetable** - View your class schedule
📢 **Announcements** - See latest notices
📆 **Academic Calendar** - Check exam dates and holidays
🏖️ **Leave** - Apply for leave or check status

Just ask me something like:
- "What's my attendance?"
- "Show my fees status"
- "What's my schedule today?"
- "Show latest announcements"
- "When are the exams?"
- "Apply for sick leave on Feb 10"
"""

    def _handle_teacher_query(self, teacher, intent, course_id, exam_type, user_data=None):
        """Handle queries for teacher users"""
        if intent == "attendance":
            agent = TeacherAttendanceAgent(teacher)
            raw_data = agent.get_attendance(course_id)
            return make_chat_response(raw_data, intent="attendance")
        
        elif intent == "low_attendance_students":
            agent = TeacherAttendanceAgent(teacher)
            threshold = user_data.get('threshold', 75) if user_data else 75
            raw_data = agent.get_low_attendance_students(threshold=threshold, course_id=course_id)
            return make_chat_response(raw_data, intent="low_attendance_students")
        
        elif intent == "pending_submissions":
            agent = TeacherAssignmentAgent(teacher)
            raw_data = agent.get_pending_submissions(course_id=course_id)
            return make_chat_response(raw_data, intent="pending_submissions")
            
        elif intent == "fees":
            return "As a teacher, you don't have access to fee information. Please contact the admin office for fee-related queries."
            
        elif intent == "assignments":
            agent = TeacherAssignmentAgent(teacher)
            raw_data = agent.get_assignments(course_id)
            return make_chat_response(raw_data, intent="assignments")
            
        elif intent == "results":
            agent = TeacherResultsAgent(teacher)
            raw_data = agent.get_results(course_id, exam_type)
            return make_chat_response(raw_data, intent="results")
        
        elif intent == "timetable":
            agent = TimetableAgent(teacher.user, teacher, 'teacher')
            raw_data = agent.get_timetable()
            return self._format_timetable_response(raw_data)
        
        elif intent == "announcements":
            agent = AnnouncementAgent(teacher.user, teacher, 'teacher')
            raw_data = agent.get_announcements()
            return self._format_announcements_response(raw_data)
        
        elif intent == "academic_calendar":
            agent = AcademicCalendarAgent(teacher.user, teacher, 'teacher')
            raw_data = agent.get_events()
            return self._format_calendar_response(raw_data)
        
        elif intent == "apply_leave":
            agent = LeaveAgent(teacher.user, teacher, 'teacher')
            return self._handle_apply_leave(agent, user_data)
        
        elif intent == "leave_status":
            agent = LeaveAgent(teacher.user, teacher, 'teacher')
            raw_data = agent.get_leave_status()
            return self._format_leave_status_response(raw_data)
            
        else:
            return """I'm not sure how to help with that. As a teacher, I can assist you with:

📊 **Attendance** - View attendance statistics for your courses
⚠️ **Low Attendance** - Find students with attendance below a threshold
📝 **Assignments** - See assignments you've created and submission status
👥 **Pending Submissions** - See which students haven't submitted assignments
🎓 **Results** - Check exam results and performance analytics for your courses
📅 **Timetable** - View your teaching schedule
📢 **Announcements** - See latest notices
📆 **Academic Calendar** - Check exam dates and holidays
🏖️ **Leave** - Apply for leave or check status

Just ask me something like:
- "Show attendance for my courses"
- "Which students have below 50% attendance?"
- "How many students have less than 75% attendance?"
- "Which students haven't submitted the assignment?"
- "Who is remaining to submit assignment?"
- "Assignment submissions status"
- "What's my schedule today?"
- "Show latest announcements"
- "Apply for leave on Feb 10"
"""

    def _handle_admin_query(self, admin, intent, course_id, exam_type, user_data=None):
        """Handle queries for admin users"""
        if intent == "attendance":
            agent = AdminAttendanceAgent(admin)
            raw_data = agent.get_attendance(course_id)
            return make_chat_response(raw_data, intent="attendance")
        
        elif intent == "low_attendance_students":
            agent = AdminAttendanceAgent(admin)
            threshold = user_data.get('threshold', 75) if user_data else 75
            raw_data = agent.get_low_attendance_students(threshold=threshold)
            return make_chat_response(raw_data, intent="low_attendance_students")
            
        elif intent == "fees":
            agent = AdminFeesAgent(admin)
            raw_data = agent.get_fees()
            return make_chat_response(raw_data, intent="fees")
        
        elif intent == "pending_submissions":
            agent = AdminAssignmentAgent(admin)
            raw_data = agent.get_pending_submissions(course_id=course_id)
            return make_chat_response(raw_data, intent="pending_submissions")
            
        elif intent == "assignments":
            agent = AdminAssignmentAgent(admin)
            raw_data = agent.get_assignments(course_id)
            return make_chat_response(raw_data, intent="assignments")
            
        elif intent == "results":
            agent = AdminResultsAgent(admin)
            raw_data = agent.get_results(course_id, exam_type)
            return make_chat_response(raw_data, intent="results")
        
        elif intent == "add_teacher":
            agent = AdminUserManagementAgent(admin)
            return self._handle_add_teacher(agent, user_data)
        
        elif intent == "add_student":
            agent = AdminUserManagementAgent(admin)
            return self._handle_add_student(agent, user_data)
        
        elif intent == "edit_student":
            agent = AdminUserManagementAgent(admin)
            return self._handle_edit_student(agent, user_data)
        
        elif intent == "edit_teacher":
            agent = AdminUserManagementAgent(admin)
            return self._handle_edit_teacher(agent, user_data)
        
        elif intent == "delete_student":
            agent = AdminUserManagementAgent(admin)
            return self._handle_delete_student(agent, user_data)
        
        elif intent == "delete_teacher":
            agent = AdminUserManagementAgent(admin)
            return self._handle_delete_teacher(agent, user_data)
        
        elif intent == "find_student":
            agent = AdminUserManagementAgent(admin)
            return self._handle_find_students(agent, user_data)
        
        elif intent == "find_teacher":
            agent = AdminUserManagementAgent(admin)
            return self._handle_find_teachers(agent, user_data)
        
        elif intent == "reset_password":
            agent = AdminUserManagementAgent(admin)
            return self._handle_reset_password(agent, user_data)
        
        elif intent == "add_course":
            agent = AdminUserManagementAgent(admin)
            return self._handle_add_course(agent, user_data)
        
        elif intent == "list_departments":
            agent = AdminUserManagementAgent(admin)
            raw_data = agent.get_departments()
            return self._format_departments_response(raw_data)
        
        elif intent == "timetable":
            agent = TimetableAgent(admin.user, admin, 'admin')
            raw_data = agent.get_timetable()
            return self._format_timetable_response(raw_data)
        
        elif intent == "announcements":
            agent = AnnouncementAgent(admin.user, admin, 'admin')
            raw_data = agent.get_announcements()
            return self._format_announcements_response(raw_data)
        
        elif intent == "academic_calendar":
            agent = AcademicCalendarAgent(admin.user, admin, 'admin')
            raw_data = agent.get_events()
            return self._format_calendar_response(raw_data)
        
        elif intent == "apply_leave":
            return "As an admin, you manage leave requests. Use the admin dashboard to approve or reject leave applications."
        
        elif intent == "leave_status":
            return "As an admin, you can view all leave requests in the admin dashboard."
            
        else:
            return """I'm not sure how to help with that. As an admin, I can assist you with:

📊 **Attendance** - View institution-wide attendance statistics
⚠️ **Low Attendance** - Find students with attendance below a threshold
💰 **Fees** - Check fee collection status and pending dues
📝 **Assignments** - Overview of all assignments across departments
👥 **Pending Submissions** - See which students haven't submitted assignments
🎓 **Results** - Institution-wide performance analytics
📅 **Timetable** - View all schedules
📢 **Announcements** - See latest notices
📆 **Academic Calendar** - Check exam dates and holidays

👥 **User Management** (Admin Only):
- "Add a new teacher" - Register a new faculty member
- "Add a new student" - Enroll a new student
- "Edit student MCA1001 semester to 3" - Update student details
- "Edit teacher MCA001 designation to Professor" - Update teacher details
- "Delete student MCA1001" - Remove a student
- "Delete teacher MCA001" - Remove a teacher
- "Find all MCA students" - Search students
- "Show student MCA1001 details" - View specific student
- "Reset password for student MCA1001" - Reset user password
- "Add course Database Systems to MCA semester 3" - Add new course
- "List departments" - View all available departments

Just ask me something like:
- "Overall attendance statistics"
- "How many students have below 50% attendance?"
- "Students with less than 75% attendance"
- "Who hasn't submitted assignments?"
- "Which students are remaining to submit?"
- "Fee collection status"
- "Find students in MCA year 2"
- "Reset password for teacher MCA001"
"""
    
    def _handle_add_teacher(self, agent, user_data):
        """Handle add teacher request"""
        if not user_data:
            return """📋 **Add New Teacher**

To add a new teacher, please provide all the details in one message like this:

**Example:**
"Add teacher with email john.doe@sies.edu.in, first name John, last name Doe, department Computer Science, designation Professor"

**Required fields:**
- Email (must be from an allowed institutional domain)
- First name
- Last name  
- Department

**Optional fields:**
- Designation (default: Assistant Professor)

💡 **Tip:** You can also say "list departments" to see available departments."""

        # Validate required fields
        email = user_data.get('email')
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        department = user_data.get('department')
        designation = user_data.get('designation', 'Assistant Professor')
        
        missing_fields = []
        if not email:
            missing_fields.append("email")
        if not first_name:
            missing_fields.append("first name")
        if not last_name:
            missing_fields.append("last name")
        if not department:
            missing_fields.append("department")
        
        if missing_fields:
            return f"""⚠️ **Missing Information**

I couldn't find the following required fields: **{', '.join(missing_fields)}**

Please provide all details in one message like this:
"Add teacher with email john@sies.edu.in, first name John, last name Doe, department Computer Science"

💡 Say "list departments" to see available departments."""
        
        # Call the agent to add teacher
        result = agent.add_teacher(
            email=email,
            first_name=first_name,
            last_name=last_name,
            department_name=department,
            designation=designation
        )
        
        if result.get('success'):
            return f"""✅ **Teacher Added Successfully!**

👤 **Name:** {first_name} {last_name}
📧 **Email:** {email}
🆔 **Teacher ID:** {result.get('teacher_id')}
🏢 **Department:** {result.get('department')}
📌 **Designation:** {result.get('designation')}

🔐 **Temporary Password:** `{result.get('default_password')}`

⚠️ Please share the credentials securely with the new teacher and ask them to change their password after first login."""
        else:
            error_msg = result.get('error', 'Unknown error')
            available_depts = result.get('available_departments', [])
            
            response = f"❌ **Failed to Add Teacher**\n\n{error_msg}"
            
            if available_depts:
                response += f"\n\n📋 **Available Departments:**\n"
                for dept in available_depts[:10]:
                    response += f"• {dept}\n"
            
            return response
    
    def _handle_add_student(self, agent, user_data):
        """Handle add student request"""
        if not user_data:
            return """📋 **Add New Student**

To add a new student, please provide all the details in one message like this:

**Example:**
"Add student with email jane.smith@sies.edu.in, first name Jane, last name Smith, department Computer Science, program MCA, year 1, semester 1"

**Required fields:**
- Email (must be from an allowed institutional domain)
- First name
- Last name
- Department
- Program (e.g., MCA, MBA, BSc, etc.)

**Optional fields:**
- Year of study (default: 1)
- Semester (default: 1)

💡 **Tip:** You can also say "list departments" to see available departments."""

        # Validate required fields
        email = user_data.get('email')
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        department = user_data.get('department')
        program = user_data.get('program')
        year_of_study = user_data.get('year_of_study', 1)
        semester = user_data.get('semester', 1)
        
        missing_fields = []
        if not email:
            missing_fields.append("email")
        if not first_name:
            missing_fields.append("first name")
        if not last_name:
            missing_fields.append("last name")
        if not department:
            missing_fields.append("department")
        if not program:
            missing_fields.append("program")
        
        if missing_fields:
            return f"""⚠️ **Missing Information**

I couldn't find the following required fields: **{', '.join(missing_fields)}**

Please provide all details in one message like this:
"Add student with email jane@sies.edu.in, first name Jane, last name Smith, department CS, program MCA, year 1, semester 1"

💡 Say "list departments" to see available departments."""
        
        # Call the agent to add student
        result = agent.add_student(
            email=email,
            first_name=first_name,
            last_name=last_name,
            department_name=department,
            program=program,
            year_of_study=year_of_study or 1,
            semester=semester or 1
        )
        
        if result.get('success'):
            enrolled_courses = result.get('enrolled_courses', [])
            
            response = f"""✅ **Student Added Successfully!**

👤 **Name:** {first_name} {last_name}
📧 **Email:** {email}
🆔 **Student ID:** {result.get('student_id')}
🏢 **Department:** {result.get('department')}
📚 **Program:** {result.get('program')}
📅 **Year:** {result.get('year_of_study')} | **Semester:** {result.get('semester')}

🔐 **Temporary Password:** `{result.get('default_password')}`
"""
            
            if enrolled_courses:
                response += f"\n📖 **Auto-Enrolled in {len(enrolled_courses)} Course(s):**\n"
                for course in enrolled_courses:
                    response += f"• {course['course_name']} ({course['course_id']}) - {course['credits']} credits\n"
            else:
                response += "\nNo courses found for this department/semester. Courses can be assigned later."
            
            response += "\n⚠️ Please share the credentials securely with the new student and ask them to change their password after first login."
            
            return response
        else:
            error_msg = result.get('error', 'Unknown error')
            available_depts = result.get('available_departments', [])
            
            response = f"❌ **Failed to Add Student**\n\n{error_msg}"
            
            if available_depts:
                response += f"\n\n📋 **Available Departments:**\n"
                for dept in available_depts[:10]:
                    response += f"• {dept}\n"
            
            return response
    
    def _handle_edit_student(self, agent, user_data):
        """Handle edit student request"""
        if not user_data or not user_data.get('identifier'):
            return """📝 **Edit Student Details**

To edit a student's details, please provide the roll number and what you want to change:

**Examples:**
- "Update student MCA1001 semester to 3"
- "Change student MCA2001 year to 2 and semester to 4"
- "Edit student MCA1005 program to MMS"

**Editable fields:**
- Semester (1-8)
- Year of study (1-4)
- Program (MCA, MMS, etc.)
- Department

💡 **Tip:** Roll numbers follow the format: MCA1001 (1st year), MCA2001 (2nd year)"""

        identifier = user_data.get('identifier')
        
        # Build update fields
        update_fields = {}
        if user_data.get('semester') is not None:
            update_fields['semester'] = user_data['semester']
        if user_data.get('year_of_study') is not None:
            update_fields['year_of_study'] = user_data['year_of_study']
        if user_data.get('program') is not None:
            update_fields['program'] = user_data['program']
        if user_data.get('department') is not None:
            update_fields['department'] = user_data['department']
        
        if not update_fields:
            return f"""⚠️ **No Changes Specified**

You've identified student **{identifier}**, but I couldn't determine what to change.

Please specify what you want to update, for example:
- "Update student {identifier} semester to 3"
- "Change student {identifier} year to 2"
- "Edit student {identifier} department to MMS"
"""
        
        # Call the agent to update student
        result = agent.update_student(identifier, **update_fields)
        
        if result.get('success'):
            updates_list = result.get('updates', [])
            response = f"""✅ **Student Updated Successfully!**

👤 **Student:** {result.get('student_name')}
🆔 **Roll No:** {result.get('roll_no')}

📝 **Changes Made:**
"""
            for update in updates_list:
                response += f"• {update}\n"
            
            return response
        else:
            return f"❌ **Failed to Update Student**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_edit_teacher(self, agent, user_data):
        """Handle edit teacher request"""
        if not user_data or not user_data.get('identifier'):
            return """📝 **Edit Teacher Details**

To edit a teacher's details, please provide the teacher ID and what you want to change:

**Examples:**
- "Update teacher MCA001 designation to Professor"
- "Change teacher MMS002 department to Computer Applications"
- "Edit teacher MCA003 first name to Rahul"

**Editable fields:**
- Designation (Professor, Associate Professor, Assistant Professor)
- Department
- First name
- Last name

💡 **Tip:** Teacher IDs follow the format: MCA001, MMS002, etc."""

        identifier = user_data.get('identifier')
        
        # Build update fields
        update_fields = {}
        if user_data.get('designation') is not None:
            update_fields['designation'] = user_data['designation']
        if user_data.get('department') is not None:
            update_fields['department'] = user_data['department']
        if user_data.get('first_name') is not None:
            update_fields['first_name'] = user_data['first_name']
        if user_data.get('last_name') is not None:
            update_fields['last_name'] = user_data['last_name']
        
        if not update_fields:
            return f"""⚠️ **No Changes Specified**

You've identified teacher **{identifier}**, but I couldn't determine what to change.

Please specify what you want to update, for example:
- "Update teacher {identifier} designation to Professor"
- "Change teacher {identifier} department to MMS"
"""
        
        # Call the agent to update teacher
        result = agent.update_teacher(identifier, **update_fields)
        
        if result.get('success'):
            updates_list = result.get('updates', [])
            response = f"""✅ **Teacher Updated Successfully!**

👤 **Teacher:** {result.get('teacher_name')}
🆔 **Teacher ID:** {result.get('teacher_id')}

📝 **Changes Made:**
"""
            for update in updates_list:
                response += f"• {update}\n"
            
            return response
        else:
            return f"❌ **Failed to Update Teacher**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_delete_student(self, agent, user_data):
        """Handle delete student request"""
        if not user_data or not user_data.get('identifier'):
            return """🗑️ **Delete Student**

To delete a student, please provide the student's roll number:

**Examples:**
- "Delete student MCA1001"
- "Remove student MMS2003"

⚠️ **Warning:** This action cannot be undone. The student and all their records will be permanently deleted."""

        identifier = user_data.get('identifier')
        result = agent.delete_student(identifier)
        
        if result.get('success'):
            return f"""✅ **Student Deleted Successfully**

🗑️ **Deleted Student:** {result.get('message')}
📧 **Email:** {result.get('deleted_email')}

All associated records have been removed."""
        else:
            return f"❌ **Failed to Delete Student**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_delete_teacher(self, agent, user_data):
        """Handle delete teacher request"""
        if not user_data or not user_data.get('identifier'):
            return """🗑️ **Delete Teacher**

To delete a teacher, please provide the teacher's ID:

**Examples:**
- "Delete teacher MCA001"
- "Remove teacher MMS002"

⚠️ **Warning:** This action cannot be undone. The teacher and all their records will be permanently deleted."""

        identifier = user_data.get('identifier')
        result = agent.delete_teacher(identifier)
        
        if result.get('success'):
            return f"""✅ **Teacher Deleted Successfully**

🗑️ **Deleted Teacher:** {result.get('message')}
📧 **Email:** {result.get('deleted_email')}

All associated records have been removed."""
        else:
            return f"❌ **Failed to Delete Teacher**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_find_students(self, agent, user_data):
        """Handle find students request"""
        if not user_data:
            user_data = {}
        
        identifier = user_data.get('identifier')
        department = user_data.get('department')
        year = user_data.get('year')
        
        result = agent.find_students(
            identifier=identifier,
            department=department,
            year_of_study=year
        )
        
        if result.get('success'):
            if result.get('single_result'):
                s = result.get('student')
                return f"""🔍 **Student Found**

📋 **{s.get('name')}**
🆔 Roll: {s.get('roll_no')}
📧 Email: {s.get('email')}
🏢 Department: {s.get('department')}
📚 Program: {s.get('program')}
📅 Year {s.get('year')}, Semester {s.get('semester')}"""
            
            students = result.get('students', [])
            count = result.get('count', 0)
            
            if count == 0:
                return "🔍 **No students found** matching your criteria."
            
            response = f"🔍 **Found {count} Student(s)**\n\n"
            
            for s in students[:20]:  # Limit to 20
                response += f"📋 **{s.get('name')}**\n"
                response += f"   🆔 Roll: {s.get('roll_no')} | 📚 {s.get('program')}\n"
                response += f"   Year {s.get('year')}, Sem {s.get('semester')}\n\n"
            
            if count > 20:
                response += f"_... and {count - 20} more students_"
            
            return response
        else:
            return f"❌ **Search Failed**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_find_teachers(self, agent, user_data):
        """Handle find teachers request"""
        if not user_data:
            user_data = {}
        
        identifier = user_data.get('identifier')
        department = user_data.get('department')
        
        result = agent.find_teachers(
            identifier=identifier,
            department=department
        )
        
        if result.get('success'):
            if result.get('single_result'):
                t = result.get('teacher')
                return f"""🔍 **Teacher Found**

👤 **{t.get('name')}**
🆔 ID: {t.get('teacher_id')}
📧 Email: {t.get('email')}
🏢 Department: {t.get('department')}
📌 Designation: {t.get('designation')}"""
            
            teachers = result.get('teachers', [])
            count = result.get('count', 0)
            
            if count == 0:
                return "🔍 **No teachers found** matching your criteria."
            
            response = f"🔍 **Found {count} Teacher(s)**\n\n"
            
            for t in teachers[:20]:  # Limit to 20
                response += f"👤 **{t.get('name')}**\n"
                response += f"   🆔 ID: {t.get('teacher_id')}\n"
                response += f"   🏢 {t.get('department')} | 📌 {t.get('designation')}\n\n"
            
            if count > 20:
                response += f"_... and {count - 20} more teachers_"
            
            return response
        else:
            return f"❌ **Search Failed**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_reset_password(self, agent, user_data):
        """Handle password reset request"""
        if not user_data or not user_data.get('identifier'):
            return """🔐 **Reset Password**

To reset a user's password, please specify the user's ID:

**Examples:**
- "Reset password for student MCA1001"
- "Reset password for teacher MCA001"
- "Reset MCA1001 password"

The user will receive a new temporary password."""

        identifier = user_data.get('identifier')
        
        result = agent.reset_password(identifier)
        
        if result.get('success'):
            return f"""✅ **Password Reset Successful**

👤 **User:** {result.get('message', '').split("'")[1] if "'" in result.get('message', '') else 'User'}
📧 **Email:** {result.get('email')}
👥 **Type:** {result.get('user_type', '').title()}
🔐 **New Password:** `{result.get('new_password')}`

⚠️ Please share this password securely with the user and ask them to change it after login."""
        else:
            return f"❌ **Password Reset Failed**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_add_course(self, agent, user_data):
        """Handle add course request"""
        if not user_data:
            return """📚 **Add New Course**

To add a new course, please provide the details:

**Example:**
"Add course Database Management Systems to MCA semester 3"

**Required fields:**
- Course name
- Department/Program (MCA, MMS, etc.)
- Semester

**Optional fields:**
- Course code
- Credits

💡 Say "list departments" to see available departments."""

        name = user_data.get('name') or user_data.get('course_name')
        department = user_data.get('department') or user_data.get('program')
        semester = user_data.get('semester')
        code = user_data.get('code') or user_data.get('course_code') or user_data.get('course_id')
        credits = user_data.get('credits')
        
        missing_fields = []
        if not name:
            missing_fields.append("course name")
        if not department:
            missing_fields.append("department/program")
        if not semester:
            missing_fields.append("semester")
        
        if missing_fields:
            return f"""⚠️ **Missing Information**

I couldn't find: **{', '.join(missing_fields)}**

Please provide all details like this:
"Add course Database Systems to MCA semester 3"

💡 Say "list departments" to see available departments."""
        
        result = agent.add_course(
            course_name=name,
            program=department,
            semester=int(semester) if semester else 1,
            credits=int(credits) if credits else 4,
            course_id=code
        )
        
        if result.get('success'):
            return f"""✅ **Course Added Successfully!**

📚 **Course:** {result.get('message', '').split("'")[1] if "'" in result.get('message', '') else name}
🔢 **Code:** {result.get('course_id')}
🏢 **Department:** {result.get('department')}
📅 **Semester:** {result.get('semester')}
📊 **Credits:** {result.get('credits', 'N/A')}"""
        else:
            return f"❌ **Failed to Add Course**\n\n{result.get('error', 'Unknown error')}"
    
    def _handle_apply_leave(self, agent, user_data):
        """Handle leave application request"""
        if not user_data:
            return """🏖️ **Apply for Leave**

To apply for leave, please provide the details:

**Examples:**
- "Apply for sick leave on Feb 10"
- "Apply for personal leave from Feb 10 to Feb 12"
- "Apply for emergency leave tomorrow"

**Leave types:**
- Sick leave
- Personal leave
- Emergency leave

You can also add a reason: "Apply for sick leave on Feb 10 due to fever" """

        leave_type = user_data.get('leave_type', 'personal')
        start_date = user_data.get('start_date')
        end_date = user_data.get('end_date') or start_date
        reason = user_data.get('reason', '')
        
        if not start_date:
            return """⚠️ **Missing Date**

Please specify when you want to take leave:
- "Apply for sick leave on Feb 10"
- "Apply for leave from March 5 to March 7" """
        
        result = agent.apply_leave(
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        
        if result.get('success'):
            return f"""✅ **Leave Application Submitted**

📋 **Leave Request ID:** {result.get('leave_id')}
🏖️ **Type:** {result.get('leave_type').replace('_', ' ').title()}
📅 **From:** {result.get('start_date')}
📅 **To:** {result.get('end_date')}
📝 **Reason:** {result.get('reason') or 'Not specified'}
⏳ **Status:** Pending Approval

Your leave request has been submitted for approval."""
        else:
            return f"❌ **Leave Application Failed**\n\n{result.get('error', 'Unknown error')}"
    
    def _format_timetable_response(self, data):
        """Format timetable data for display"""
        if data.get('error'):
            return f"❌ **Error:** {data.get('error')}"
        
        slots = data.get('slots', [])
        if not slots:
            return "📅 **No classes scheduled for today.**\n\nEnjoy your day off! 🎉"
        
        day = data.get('day', 'Today')
        response = f"📅 **Schedule for {day}:**\n\n"
        
        for slot in slots:
            response += f"🕐 **{slot.get('time')}**\n"
            response += f"   📚 {slot.get('course')}\n"
            if slot.get('teacher'):
                response += f"   👤 {slot.get('teacher')}\n"
            if slot.get('room'):
                response += f"   🚪 Room: {slot.get('room')}\n"
            response += "\n"
        
        return response
    
    def _format_announcements_response(self, data):
        """Format announcements data for display"""
        if data.get('error'):
            return f"❌ **Error:** {data.get('error')}"
        
        announcements = data.get('announcements', [])
        if not announcements:
            return "📢 **No recent announcements.**\n\nCheck back later for updates!"
        
        response = "📢 **Latest Announcements:**\n\n"
        
        for ann in announcements[:10]:  # Limit to 10
            response += f"📌 **{ann.get('title')}**\n"
            response += f"   {ann.get('content', '')[:200]}"
            if len(ann.get('content', '')) > 200:
                response += "..."
            response += f"\n   📅 {ann.get('date')} | 👤 {ann.get('posted_by')}\n\n"
        
        return response
    
    def _format_calendar_response(self, data):
        """Format academic calendar data for display"""
        if data.get('error'):
            return f"❌ **Error:** {data.get('error')}"
        
        events = data.get('events', [])
        if not events:
            return "📆 **No upcoming events found.**"
        
        response = "📆 **Academic Calendar:**\n\n"
        
        # Group by event type
        exams = [e for e in events if e.get('event_type') == 'exam']
        holidays = [e for e in events if e.get('event_type') == 'holiday']
        deadlines = [e for e in events if e.get('event_type') == 'deadline']
        other_events = [e for e in events if e.get('event_type') == 'event']
        
        if exams:
            response += "📝 **Exams:**\n"
            for e in exams[:5]:
                response += f"   • {e.get('title')} - {e.get('start_date')}"
                if e.get('end_date') and e.get('end_date') != e.get('start_date'):
                    response += f" to {e.get('end_date')}"
                response += "\n"
            response += "\n"
        
        if holidays:
            response += "🎉 **Holidays:**\n"
            for e in holidays[:5]:
                response += f"   • {e.get('title')} - {e.get('start_date')}"
                if e.get('end_date') and e.get('end_date') != e.get('start_date'):
                    response += f" to {e.get('end_date')}"
                response += "\n"
            response += "\n"
        
        if deadlines:
            response += "⏰ **Deadlines:**\n"
            for e in deadlines[:5]:
                response += f"   • {e.get('title')} - {e.get('start_date')}\n"
            response += "\n"
        
        if other_events:
            response += "📅 **Events:**\n"
            for e in other_events[:5]:
                response += f"   • {e.get('title')} - {e.get('start_date')}\n"
        
        return response
    
    def _format_leave_status_response(self, data):
        """Format leave status data for display"""
        if data.get('error'):
            return f"❌ **Error:** {data.get('error')}"
        
        leaves = data.get('leaves', [])
        if not leaves:
            return "📋 **No leave requests found.**\n\nYou haven't applied for any leave yet."
        
        response = "📋 **Your Leave Requests:**\n\n"
        
        status_icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }
        
        for leave in leaves[:10]:
            icon = status_icons.get(leave.get('status'), '📋')
            response += f"{icon} **{leave.get('leave_type').replace('_', ' ').title()}**\n"
            response += f"   📅 {leave.get('start_date')} to {leave.get('end_date')}\n"
            response += f"   Status: {leave.get('status').title()}\n"
            if leave.get('reason'):
                response += f"   Reason: {leave.get('reason')}\n"
            response += "\n"
        
        return response
    
    def _format_departments_response(self, data):
        """Format departments list for display"""
        departments = data.get('departments', [])
        
        if not departments:
            return "📋 **No departments found in the system.**\n\nPlease contact the system administrator to add departments."
        
        response = "📋 **Available Departments:**\n\n"
        
        for dept in departments:
            response += f"• **{dept['name']}**"
            if dept.get('code'):
                response += f" ({dept['code']})"
            if dept.get('program_type'):
                response += f" - {dept['program_type'].upper()}"
            response += "\n"
        
        response += "\n💡 Use these department names when adding teachers or students."
        
        return response
    
    def _contains_restricted_query(self, query: str, restricted_keywords: list) -> bool:
        """
        Check if query contains restricted keywords
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in restricted_keywords)
    
    def _get_or_create_session(self, user, session_id=None):
        """
        Get existing session or create new one
        """
        if session_id:
            try:
                session = ChatSession.objects.get(
                    session_id=session_id,
                    user=user,
                    is_active=True
                )
                return session
            except ChatSession.DoesNotExist:
                pass
        
        # Create new session
        return ChatSession.objects.create(user=user)


class ChatSessionListView(APIView):
    """
    List all chat sessions for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all sessions for user"""
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')
        
        serializer = ChatSessionListSerializer(sessions, many=True)
        return Response(serializer.data)


class ChatSessionDetailView(APIView):
    """
    Get, update, or delete a specific chat session
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """Get session with all messages"""
        session = get_object_or_404(
            ChatSession,
            session_id=session_id,
            user=request.user
        )
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)
    
    def patch(self, request, session_id):
        """Update session (e.g., rename title)"""
        session = get_object_or_404(
            ChatSession,
            session_id=session_id,
            user=request.user
        )
        
        if 'title' in request.data:
            session.title = request.data['title']
        if 'is_active' in request.data:
            session.is_active = request.data['is_active']
        
        session.save()
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)
    
    def delete(self, request, session_id):
        """Soft delete session (mark as inactive)"""
        session = get_object_or_404(
            ChatSession,
            session_id=session_id,
            user=request.user
        )
        session.is_active = False
        session.save()
        return Response({"message": "Session deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ClearChatHistoryView(APIView):
    """
    Clear all chat history for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        """Mark all sessions as inactive"""
        ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)
        
        return Response({"message": "All chat history cleared"}, status=status.HTTP_204_NO_CONTENT)
