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
    elif intent == "low_attendance_students":
        if is_admin_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for administrators.

Convert the following low attendance report into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Clearly state the threshold being used
- Show the total count of affected students prominently
- Summarize by department
- List students with lowest attendance first
- Suggest follow-up actions (counseling, notifications)
- Keep it informative but actionable
- Use emojis sparingly (1-2 max)
"""
        else:  # Teacher
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for teachers.

Convert the following low attendance report into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Clearly state the threshold being used
- Show the count of students per course
- List students with their attendance percentages
- Suggest reaching out to affected students
- If all students are above threshold, celebrate!
- Keep it informative and actionable
- Use emojis sparingly (1-2 max)
"""
    elif intent == "pending_submissions":
        if is_admin_data:
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for administrators.

Convert the following pending submission report into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Highlight overdue assignments with urgency
- Show assignment details with counts
- List students who haven't submitted
- Summarize by course if multiple
- Suggest follow-up actions
- If all submitted, celebrate!
- Use emojis sparingly (1-2 max)
"""
        else:  # Teacher
            prompt = f"""
You are SARAA, a friendly college ERP chatbot assistant for teachers.

Convert the following pending submission report into a natural, conversational response:

{data}

Guidelines:
- Be professional yet friendly
- Highlight overdue assignments with urgency
- Show each assignment with pending count
- List students who haven't submitted clearly
- Include roll numbers for easy identification
- Suggest sending reminders
- If all students submitted, congratulate yourself and them!
- Keep it actionable
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
            response = f"""📝 **Your Assignments**

Teacher: {data.get('teacher_name', 'Teacher')}
Total Assignments: {data.get('total_assignments', 0)}

"""
            for a in assignments[:5]:
                response += f"📌 **{a['title']}** ({a['course_name']})\n"
                response += f"   Due: {a['due_date']}\n"
                response += f"   Enrolled: {a.get('total_enrolled', 0)} | Submitted: {a['total_submissions']} | Graded: {a.get('graded', 0)}\n"
                
                # Show pending students
                pending_students = a.get('pending_students', [])
                pending_count = a.get('pending_submission_count', 0)
                
                if pending_count > 0:
                    response += f"   ⚠️ **{pending_count} student(s) yet to submit:**\n"
                    for student in pending_students[:5]:
                        response += f"      • {student['name']}\n"
                    if pending_count > 5:
                        response += f"      ... and {pending_count - 5} more\n"
                else:
                    response += f"   ✅ All students have submitted!\n"
                
                response += "\n"
            
            if len(assignments) > 5:
                response += f"... and {len(assignments) - 5} more assignments"
            
            return response.strip() if assignments else "No assignments found."

        else:
            assignments = data.get('assignments', [])
            pending_assignments = [a for a in assignments if a.get('status') == 'Pending']
            overdue_assignments = [a for a in assignments if a.get('status') == 'Overdue']
            submitted_assignments = [a for a in assignments if a.get('status') == 'Submitted']
            
            response = f"""📝 **Assignment Summary**

- Total Assignments: {data.get('total_assignments', 0)}
- Submitted: {data.get('submitted_assignments', 0)}
- Pending: {data.get('pending_assignments', 0)}
- Overdue: {data.get('overdue_assignments', 0)}
"""
            
            # Show overdue assignments first (urgent)
            if overdue_assignments:
                response += "\n🚨 **Overdue Assignments (Urgent!):**\n"
                for a in overdue_assignments[:5]:
                    response += f"  • **{a['title']}** ({a['course_name']})\n"
                    response += f"    Due: {a['due_date']} | By: {a.get('created_by', 'N/A')}\n"
            
            # Show pending assignments
            if pending_assignments:
                response += "\n⏳ **Pending Assignments:**\n"
                for a in pending_assignments[:5]:
                    response += f"  • **{a['title']}** ({a['course_name']})\n"
                    response += f"    Due: {a['due_date']} | By: {a.get('created_by', 'N/A')}\n"
            
            # Show submitted assignments (brief)
            if submitted_assignments:
                response += "\n✅ **Submitted Assignments:**\n"
                for a in submitted_assignments[:5]:
                    score_text = f" | Score: {a.get('score')}" if a.get('score') else ""
                    response += f"  • {a['title']} ({a['course_name']}){score_text}\n"
                if len(submitted_assignments) > 5:
                    response += f"  ... and {len(submitted_assignments) - 5} more\n"
            
            if data.get('pending_assignments', 0) == 0:
                response += "\n🌟 All assignments submitted! Great work!"
            elif overdue_assignments:
                response += "\n⚠️ Please submit your overdue assignments immediately!"
            else:
                response += "\n💡 Don't forget to complete your pending assignments before the deadline!"
            
            return response

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

    elif intent == "low_attendance_students":
        if is_admin:
            threshold = data.get('threshold', 75)
            total = data.get('total_students_below_threshold', 0)
            students = data.get('students', [])
            dept_summary = data.get('department_summary', [])
            
            if total == 0:
                return f"""✅ **Attendance Report**

Administrator: {data.get('admin_name', 'Admin')}

Great news! No students have attendance below {threshold}% across the institution. 🎉"""
            
            response = f"""⚠️ **Low Attendance Report**

Administrator: {data.get('admin_name', 'Admin')}
Threshold: Below {threshold}%
Total Students: **{total}**

**Department-wise:**
"""
            for dept in dept_summary[:5]:
                response += f"  • {dept['department']}: {dept['count']} student(s)\n"
            
            response += f"\n**Students with Lowest Attendance:**\n"
            for s in students[:10]:
                response += f"  • {s['name']} ({s['roll_no']}): **{s['attendance_percentage']}%** - {s['department']}\n"
            
            if total > 10:
                response += f"\n... and {total - 10} more students"
            
            return response

        else:  # Teacher
            threshold = data.get('threshold', 75)
            courses = data.get('courses_summary', [])
            total = data.get('total_students_below_threshold', 0)
            
            if total == 0:
                return f"""✅ **Attendance Report**

Teacher: {data.get('teacher_name', 'Teacher')}

Great news! No students have attendance below {threshold}% in your courses. 🎉"""
            
            response = f"""⚠️ **Low Attendance Report**

Teacher: {data.get('teacher_name', 'Teacher')}
Threshold: Below {threshold}%
Total Students: **{total}**

"""
            for course in courses:
                response += f"📚 **{course['course_name']}** ({course['students_count']} students below {threshold}%)\n"
                for s in course['students'][:5]:
                    response += f"  • {s['name']} ({s['roll_no']}): **{s['attendance_percentage']}%** (Absent: {s['absent']}/{s['total']})\n"
                if course['students_count'] > 5:
                    response += f"  ... and {course['students_count'] - 5} more\n"
                response += "\n"
            
            return response.strip()

    elif intent == "pending_submissions":
        if is_admin:
            total_assignments = data.get('total_assignments_with_pending', 0)
            total_students = data.get('total_pending_students', 0)
            assignments = data.get('assignments_summary', [])
            
            if total_assignments == 0:
                return f"""✅ **Assignment Submission Report**

Administrator: {data.get('admin_name', 'Admin')}

All students have submitted their assignments! 🎉"""
            
            response = f"""📝 **Pending Submissions Report**

Administrator: {data.get('admin_name', 'Admin')}
Assignments with Pending: **{total_assignments}**
Total Students Yet to Submit: **{total_students}**

"""
            for a in assignments[:5]:
                overdue_tag = " 🚨 OVERDUE" if a.get('is_overdue') else ""
                response += f"📌 **{a['assignment_title']}**{overdue_tag}\n"
                response += f"   Course: {a['course_name']} | Due: {a['due_date']}\n"
                response += f"   {a['submitted_count']}/{a['total_enrolled']} submitted | **{a['pending_count']} pending**\n"
                response += f"   Students remaining:\n"
                for s in a['pending_students'][:5]:
                    response += f"     • {s['name']} ({s['roll_no']})\n"
                if a['pending_count'] > 5:
                    response += f"     ... and {a['pending_count'] - 5} more\n"
                response += "\n"
            
            return response.strip()

        else:  # Teacher
            total_assignments = data.get('total_assignments_with_pending', 0)
            total_students = data.get('total_pending_students', 0)
            assignments = data.get('assignments_summary', [])
            
            if total_assignments == 0:
                return f"""✅ **Assignment Submission Report**

Teacher: {data.get('teacher_name', 'Teacher')}

All students have submitted their assignments! Great work! 🎉"""
            
            response = f"""📝 **Pending Submissions Report**

Teacher: {data.get('teacher_name', 'Teacher')}
Assignments with Pending: **{total_assignments}**
Total Students Yet to Submit: **{total_students}**

"""
            for a in assignments:
                overdue_tag = " 🚨 OVERDUE" if a.get('is_overdue') else ""
                response += f"📌 **{a['assignment_title']}**{overdue_tag}\n"
                response += f"   Course: {a['course_name']} | Due: {a['due_date']}\n"
                response += f"   {a['submitted_count']}/{a['total_enrolled']} submitted | **{a['pending_count']} pending**\n"
                response += f"   Students remaining:\n"
                for s in a['pending_students'][:10]:
                    response += f"     • {s['name']} ({s['roll_no']})\n"
                if a['pending_count'] > 10:
                    response += f"     ... and {a['pending_count'] - 10} more\n"
                response += "\n"
            
            return response.strip()

    else:
        return f"Here's what I found: {data}"
