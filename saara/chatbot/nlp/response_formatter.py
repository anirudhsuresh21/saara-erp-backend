import os
import google.generativeai as genai

# Configure GEMINI API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def make_chat_response(data, intent: str = "general"):
    """
    Converts raw data into a friendly, conversational ChatGPT-style response.
    Handles data from students, teachers, and admins.
    """
    
    # Handle errors
    if isinstance(data, dict) and "error" in data:
        return f"Sorry, {data['error']} 😊"
    
    # Detect if this is teacher/admin data based on keys
    is_teacher_data = 'teacher_name' in data if isinstance(data, dict) else False
    is_admin_data = 'admin_name' in data if isinstance(data, dict) else False
    
    # Create intent-specific prompts
    if intent == "attendance":
        if is_admin_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for administrators.

Convert the following institution-wide attendance data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Highlight overall attendance percentage
- Summarize department-wise breakdown if available
- Point out departments that need attention (low attendance)
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        elif is_teacher_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for teachers.

Convert the following course attendance data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Show attendance statistics for their courses
- Mention number of students and average attendance
- Highlight any courses that need attention
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        else:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant.

Convert the following attendance data into a natural, conversational response:

{data}

Guidelines:
- Be warm and conversational like ChatGPT
- Include attendance percentage prominently
- Mention present/total classes
- If attendance is low (<75%), gently encourage improvement
- If attendance is good (>=75%), appreciate the student
- If there's a course breakdown, summarize it nicely
- Keep it brief but friendly
- Use emojis sparingly (1-2 max)
"""
    elif intent == "fees":
        if is_admin_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for administrators.

Convert the following fee collection data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Highlight total collected vs pending
- Show collection rate percentage
- Summarize department-wise breakdown
- Point out areas needing follow-up
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        else:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant.

Convert the following fee data into a natural, conversational response:

{data}

Guidelines:
- Be warm and conversational like ChatGPT
- Clearly mention total paid, total due, and status
- If dues are pending, politely remind to clear them
- If all clear, congratulate the student
- Break down semester-wise if needed
- Keep it brief but friendly
- Use emojis sparingly (1-2 max)
"""
    elif intent == "assignments":
        if is_admin_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for administrators.

Convert the following assignment overview data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Show total assignments and submissions
- Summarize course-wise breakdown
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        elif is_teacher_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for teachers.

Convert the following assignment data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Show assignments created and submission status
- Highlight pending grading work
- Mention due dates
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        else:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant.

Convert the following assignment data into a natural, conversational response:

{data}

Guidelines:
- Be warm and conversational like ChatGPT
- Highlight pending assignments with deadlines
- Mention if any are overdue (urgent tone)
- Include file URLs if available
- If all submitted, appreciate the student
- Keep it brief but friendly
- Use emojis sparingly (1-2 max)
"""
    elif intent == "results":
        if is_admin_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for administrators.

Convert the following institution results data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Show overall performance statistics
- Include grade distribution
- Summarize department-wise performance
- Highlight areas of concern or excellence
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        elif is_teacher_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for teachers.

Convert the following course results data into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Show exam-wise performance for their courses
- Include average marks and pass percentage
- Highlight any concerns
- Keep it informative but concise
- Use emojis sparingly (1-2 max)
"""
        else:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant.

Convert the following exam results into a natural, conversational response:

{data}

Guidelines:
- Be warm and conversational like ChatGPT
- Show marks, grades, and percentage clearly
- Mention GPA if available
- Appreciate good performance
- Encourage if performance can improve
- Break down by exam type if needed
- Keep it brief but friendly
- Use emojis sparingly (1-2 max)
"""
    else:
        prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant.

Convert the following data into a natural, conversational response:

{data}

Be warm, helpful, and conversational like ChatGPT.
"""

    try:
        if not GEMINI_API_KEY:
            # Fallback to simple formatting if no API key
            return _format_fallback(data, intent)
            
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error in make_chat_response: {e}")
        # Return fallback response
        return _format_fallback(data, intent)


def _format_fallback(data, intent: str):
    """
    Fallback formatting when Gemini API is unavailable
    """
    # Detect user type
    is_teacher = 'teacher_name' in data if isinstance(data, dict) else False
    is_admin = 'admin_name' in data if isinstance(data, dict) else False
    
    if intent == "attendance":
        if is_admin:
            return f"""📊 **Institution Attendance Overview**

Administrator: {data.get('admin_name', 'Admin')}

- Total Records: {data.get('total_records', 0)}
- Overall Attendance: **{data.get('overall_attendance', 0)}%**
- Present: {data.get('present', 0)}
- Absent: {data.get('absent', 0)}

Department Breakdown available in detailed view."""

        elif is_teacher:
            courses = data.get('course_summary', [])
            course_text = "\n".join([f"  • {c['course_name']}: {c['average_attendance']}% ({c['total_students']} students)" for c in courses[:5]])
            return f"""📊 **Course Attendance Summary**

Teacher: {data.get('teacher_name', 'Teacher')}
Courses Taught: {data.get('courses_taught', 0)}

{course_text if course_text else 'No course data available.'}"""

        else:
            return f"""📊 **Attendance Summary**

Your overall attendance is **{data.get('attendance_percentage', 0)}%**

- Total Classes: {data.get('total_classes', 0)}
- Present: {data.get('present', 0)}
- Late: {data.get('late', 0)}
- Absent: {data.get('absent', 0)}

{"Keep it up! 👍" if data.get('attendance_percentage', 0) >= 75 else "Try to improve your attendance! 📈"}"""

    elif intent == "fees":
        if is_admin:
            return f"""💰 **Fee Collection Overview**

Administrator: {data.get('admin_name', 'Admin')}

- Total Collected: ₹{data.get('total_collected', 0):,.2f}
- Total Pending: ₹{data.get('total_pending', 0):,.2f}
- Collection Rate: **{data.get('collection_rate', 0)}%**

Status: Paid({data.get('status_breakdown', {}).get('paid', 0)}) | Partial({data.get('status_breakdown', {}).get('partial', 0)}) | Pending({data.get('status_breakdown', {}).get('pending', 0)})"""

        else:
            status_emoji = "✅" if data.get('overall_status') == "All Clear" else "⚠️"
            return f"""💰 **Fee Status** {status_emoji}

- Total Paid: ₹{data.get('total_paid', 0):,.2f}
- Total Due: ₹{data.get('total_due', 0):,.2f}
- Status: **{data.get('overall_status', 'Unknown')}**

{"Great! All fees are cleared! 🎉" if data.get('total_due', 0) == 0 else "Please clear your pending dues soon."}"""

    elif intent == "assignments":
        if is_admin:
            return f"""📝 **Assignment Overview**

Administrator: {data.get('admin_name', 'Admin')}

- Total Assignments: {data.get('total_assignments', 0)}
- Total Submissions: {data.get('total_submissions', 0)}

Course-wise breakdown available in detailed view."""

        elif is_teacher:
            assignments = data.get('assignments', [])
            assignment_text = "\n".join([f"  • {a['title']} ({a['course_name']}): {a['total_submissions']} submitted, {a['pending_grading']} pending grading" for a in assignments[:5]])
            return f"""📝 **Your Assignments**

Teacher: {data.get('teacher_name', 'Teacher')}
Total Assignments: {data.get('total_assignments', 0)}

{assignment_text if assignment_text else 'No assignments found.'}"""

        else:
            return f"""📝 **Assignment Summary**

- Total Assignments: {data.get('total_assignments', 0)}
- Submitted: {data.get('submitted_assignments', 0)}
- Pending: {data.get('pending_assignments', 0)}
- Overdue: {data.get('overdue_assignments', 0)}

{"All assignments submitted! Great work! 🌟" if data.get('pending_assignments', 0) == 0 else "Don't forget to complete your pending assignments!"}"""

    elif intent == "results":
        if is_admin:
            return f"""🎓 **Institution Results Overview**

Administrator: {data.get('admin_name', 'Admin')}

- Total Results: {data.get('total_results', 0)}
- Students: {data.get('total_students', 0)}
- Overall Average: **{data.get('overall_average', 0)}%**

Grade Distribution: {data.get('grade_distribution', {})}"""

        elif is_teacher:
            exams = data.get('exam_results', [])
            exam_text = "\n".join([f"  • {e['course_name']} ({e['exam_type']}): Avg {e['average_marks']}, Pass Rate {e['pass_percentage']}%" for e in exams[:5]])
            return f"""🎓 **Course Results Summary**

Teacher: {data.get('teacher_name', 'Teacher')}
Total Exams: {data.get('total_exams', 0)}

{exam_text if exam_text else 'No exam results found.'}"""

        else:
            return f"""🎓 **Results Summary**

- Total Exams: {data.get('total_exams', 0)}
- Overall Percentage: **{data.get('overall_percentage', 0)}%**
- GPA: **{data.get('gpa', 0)}**

{"Excellent performance! Keep it up! 🏆" if data.get('overall_percentage', 0) >= 60 else "You can do better! Keep studying! 📚"}"""

    else:
        return f"Here's what I found: {data}"
        return f"Here's what I found: {data}"
