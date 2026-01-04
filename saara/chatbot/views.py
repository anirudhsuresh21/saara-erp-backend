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
    AdminAttendanceAgent, AdminFeesAgent, AdminAssignmentAgent, AdminResultsAgent
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
        
        try:
            # Route to appropriate agent based on role
            print(f"Intent: {intent}, Course: {course_id}, Exam Type: {exam_type}, Role: {user_role}")
            
            if user_role == 'student':
                response_text = self._handle_student_query(profile, intent, course_id, exam_type)
            elif user_role == 'teacher':
                response_text = self._handle_teacher_query(profile, intent, course_id, exam_type)
            elif user_role == 'admin':
                response_text = self._handle_admin_query(profile, intent, course_id, exam_type)
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
    
    def _handle_student_query(self, student, intent, course_id, exam_type):
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
            
        else:
            return """I'm not sure how to help with that. As a student, I can assist you with:

📊 **Attendance** - Check your attendance percentage and records
💰 **Fees** - View your fee status and payment details
📝 **Assignments** - See pending and submitted assignments
🎓 **Results** - Check your exam results and grades

Just ask me something like:
- "What's my attendance?"
- "Show my fees status"
- "Any pending assignments?"
- "What are my exam results?"
"""

    def _handle_teacher_query(self, teacher, intent, course_id, exam_type):
        """Handle queries for teacher users"""
        if intent == "attendance":
            agent = TeacherAttendanceAgent(teacher)
            raw_data = agent.get_attendance(course_id)
            return make_chat_response(raw_data, intent="attendance")
            
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
            
        else:
            return """I'm not sure how to help with that. As a teacher, I can assist you with:

📊 **Attendance** - View attendance statistics for your courses
📝 **Assignments** - See assignments you've created and submission status
🎓 **Results** - Check exam results and performance analytics for your courses

Just ask me something like:
- "Show attendance for my courses"
- "Assignment submissions status"
- "Results for my students"
- "How are students performing in [course name]?"
"""

    def _handle_admin_query(self, admin, intent, course_id, exam_type):
        """Handle queries for admin users"""
        if intent == "attendance":
            agent = AdminAttendanceAgent(admin)
            raw_data = agent.get_attendance(course_id)
            return make_chat_response(raw_data, intent="attendance")
            
        elif intent == "fees":
            agent = AdminFeesAgent(admin)
            raw_data = agent.get_fees()
            return make_chat_response(raw_data, intent="fees")
            
        elif intent == "assignments":
            agent = AdminAssignmentAgent(admin)
            raw_data = agent.get_assignments(course_id)
            return make_chat_response(raw_data, intent="assignments")
            
        elif intent == "results":
            agent = AdminResultsAgent(admin)
            raw_data = agent.get_results(course_id, exam_type)
            return make_chat_response(raw_data, intent="results")
            
        else:
            return """I'm not sure how to help with that. As an admin, I can assist you with:

📊 **Attendance** - View institution-wide attendance statistics
💰 **Fees** - Check fee collection status and pending dues
📝 **Assignments** - Overview of all assignments across departments
🎓 **Results** - Institution-wide performance analytics

Just ask me something like:
- "Overall attendance statistics"
- "Fee collection status"
- "Assignment overview"
- "Department-wise results"
"""
    
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
