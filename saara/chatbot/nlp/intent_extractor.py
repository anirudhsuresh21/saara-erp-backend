import os
import json
import re
import google.generativeai as genai
from django.conf import settings

# Configure GEMINI API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def parse_intent(query: str):
    """
    Parses user query and extracts intent, course_id, exam_type, and user details for add operations
    Returns JSON with intent classification
    """
    prompt = f"""
You are an intent classifier for SARAA-ERP Assistant, a college ERP chatbot.
Analyze the user query and classify it into one of these intents:

"{query}"

Return ONLY valid JSON in this exact format:
{{
  "intent": "<intent_type>",
  "course_id": "<course_id or null>",
  "exam_type": "<exam_type or null>",
  "user_data": {{
    "identifier": "<roll_no, teacher_id, or email to identify user>",
    "email": "<email or null>",
    "first_name": "<first_name or null>",
    "last_name": "<last_name or null>",
    "department": "<department or null>",
    "designation": "<designation or null>",
    "program": "<program or null>",
    "year_of_study": <year or null>,
    "semester": <semester or null>,
    "leave_type": "<sick|personal|emergency|other or null>",
    "start_date": "<YYYY-MM-DD or null>",
    "end_date": "<YYYY-MM-DD or null>",
    "reason": "<reason text or null>",
    "course_name": "<course name or null>",
    "credits": <credits or null>
  }}
}}

Valid intents:
- "attendance": queries about attendance, classes attended, absent, percentage
- "low_attendance_students": teacher/admin asking about students with low attendance (below threshold like 50%, 75%)
- "fees": queries about fees, payments, dues, pending amount, money
- "assignments": queries about assignments, homework, submissions, deadlines
- "pending_submissions": teacher asking which students haven't submitted or are remaining to submit an assignment
- "results": queries about marks, grades, exam scores, performance (including "my marks in [subject]")
- "add_teacher": adding/creating a new teacher/faculty
- "add_student": adding/creating a new student
- "edit_teacher": updating/editing existing teacher details
- "edit_student": updating/editing existing student details
- "delete_teacher": removing/deleting a teacher
- "delete_student": removing/deleting a student
- "find_student": searching for students or showing student details
- "find_teacher": searching for teachers or showing teacher details
- "reset_password": resetting password for a user
- "add_course": adding a new course to the system
- "list_departments": listing available departments
- "timetable": queries about schedule, classes today, weekly schedule
- "announcements": queries about announcements, notices, news
- "academic_calendar": queries about exams, holidays, academic events
- "apply_leave": applying for leave, time off requests
- "leave_status": checking leave request status
- "unknown": anything else

Examples:
"Delete student MCA1001" → {{"intent": "delete_student", "user_data": {{"identifier": "MCA1001"}}}}
"Find all MCA students" → {{"intent": "find_student", "user_data": {{"program": "MCA"}}}}
"Show student MCA1001 details" → {{"intent": "find_student", "user_data": {{"identifier": "MCA1001"}}}}
"Reset password for student MCA1001" → {{"intent": "reset_password", "user_data": {{"identifier": "MCA1001"}}}}
"Add course Database Systems to MCA semester 3" → {{"intent": "add_course", "user_data": {{"course_name": "Database Systems", "program": "MCA", "semester": 3}}}}
"What's my schedule today?" → {{"intent": "timetable", "user_data": null}}
"Show latest announcements" → {{"intent": "announcements", "user_data": null}}
"When are the exams?" → {{"intent": "academic_calendar", "user_data": null}}
"Apply for leave on Feb 10" → {{"intent": "apply_leave", "user_data": {{"start_date": "2026-02-10", "end_date": "2026-02-10"}}}}
"Apply sick leave from Feb 10 to Feb 12" → {{"intent": "apply_leave", "user_data": {{"leave_type": "sick", "start_date": "2026-02-10", "end_date": "2026-02-12"}}}}
"Give me my marks in Computer Networks" → {{"intent": "results", "course_id": "Computer Networks", "user_data": null}}
"What's my score in Java" → {{"intent": "results", "course_id": "Java", "user_data": null}}
"How many students have below 50% attendance" → {{"intent": "low_attendance_students", "user_data": {{"threshold": 50}}}}
"Students with less than 75% attendance" → {{"intent": "low_attendance_students", "user_data": {{"threshold": 75}}}}
"Which students haven't submitted assignment" → {{"intent": "pending_submissions", "user_data": null}}
"Who is remaining to submit assignment" → {{"intent": "pending_submissions", "user_data": null}}
"""

    try:
        if not GEMINI_API_KEY:
            # Fallback to keyword-based intent detection if no API key
            return _keyword_based_intent(query)
            
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        # Clean response text (remove markdown code blocks if present)
        text = response.text.strip()
        
        # Remove ```json and ``` markers if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        
        try:
            parsed = json.loads(text)
            # Ensure all required keys exist
            return {
                "intent": parsed.get("intent", "unknown"),
                "course_id": parsed.get("course_id"),
                "exam_type": parsed.get("exam_type"),
                "user_data": parsed.get("user_data")
            }
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {text}")
            print(f"Error: {e}")
            # Fallback to keyword-based detection
            return _keyword_based_intent(query)
    except Exception as e:
        print(f"Gemini API Error in parse_intent: {e}")
        # Fallback to keyword-based detection
        return _keyword_based_intent(query)


def _extract_user_data(query: str):
    """
    Extract user data from query using regex patterns
    """
    import re
    
    user_data = {
        "email": None,
        "first_name": None,
        "last_name": None,
        "department": None,
        "designation": None,
        "program": None,
        "year_of_study": None,
        "semester": None
    }
    
    query_lower = query.lower()
    
    # Extract email - look for email pattern
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email_match = re.search(email_pattern, query)
    if email_match:
        user_data["email"] = email_match.group()
    
    # Extract first name - patterns like "first name John" or "firstname John"
    first_name_patterns = [
        r'first\s*name\s+([a-zA-Z]+)',
        r'name\s+([a-zA-Z]+)\s+([a-zA-Z]+)',  # "name John Doe"
    ]
    for pattern in first_name_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            user_data["first_name"] = match.group(1).title()
            if len(match.groups()) > 1 and match.group(2):
                user_data["last_name"] = match.group(2).title()
            break
    
    # Extract last name if not already found
    if not user_data["last_name"]:
        last_name_pattern = r'last\s*name\s+([a-zA-Z]+)'
        match = re.search(last_name_pattern, query, re.IGNORECASE)
        if match:
            user_data["last_name"] = match.group(1).title()
    
    # Extract department - patterns like "department Computer Science" or "department CS" or "dept MCA"
    dept_patterns = [
        r'department\s+([a-zA-Z\s]+?)(?:,|\s+designation|\s+program|\s+year|\s+semester|$)',
        r'dept\s+([a-zA-Z\s]+?)(?:,|\s+designation|\s+program|\s+year|\s+semester|$)',
    ]
    for pattern in dept_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            user_data["department"] = match.group(1).strip().title()
            break
    
    # Extract designation - patterns like "designation Professor"
    designation_patterns = [
        r'designation\s+([a-zA-Z\s]+?)(?:,|\s+department|\s+program|\s+year|\s+semester|$)',
    ]
    for pattern in designation_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            user_data["designation"] = match.group(1).strip().title()
            break
    
    # Extract program - patterns like "program MCA" or "program MBA"
    program_patterns = [
        r'program\s+([a-zA-Z]+)',
    ]
    for pattern in program_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            user_data["program"] = match.group(1).upper()
            break
    
    # Extract year - patterns like "year 1" or "year of study 2"
    year_patterns = [
        r'year\s*(?:of\s*study)?\s*(\d+)',
    ]
    for pattern in year_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            user_data["year_of_study"] = int(match.group(1))
            break
    
    # Extract semester - patterns like "semester 1" or "sem 2"
    semester_patterns = [
        r'semester\s*(\d+)',
        r'sem\s*(\d+)',
    ]
    for pattern in semester_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            user_data["semester"] = int(match.group(1))
            break
    
    # Check if we have any meaningful data
    has_data = any(v is not None for v in user_data.values())
    
    return user_data if has_data else None


def _extract_edit_data(query: str):
    """
    Extract edit data from query including identifier (roll_no or teacher_id) and fields to update
    """
    edit_data = {
        "identifier": None,
        "email": None,
        "first_name": None,
        "last_name": None,
        "department": None,
        "designation": None,
        "program": None,
        "year_of_study": None,
        "semester": None
    }
    
    # Extract identifier (roll_no like MCA1001, MMS2001 or teacher_id like MCA001)
    identifier_pattern = r'\b((?:MCA|MMS)\d{3,4})\b'
    identifier_match = re.search(identifier_pattern, query, re.IGNORECASE)
    if identifier_match:
        edit_data["identifier"] = identifier_match.group(1).upper()
    
    # Extract semester - patterns like "semester to 3", "semester 3", "sem 3"
    semester_patterns = [
        r'semester\s+(?:to\s+)?(\d+)',
        r'sem\s+(?:to\s+)?(\d+)',
        r'semester\s*[=:]\s*(\d+)'
    ]
    for pattern in semester_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            edit_data["semester"] = int(match.group(1))
            break
    
    # Extract year_of_study - patterns like "year to 2", "year 2"
    year_patterns = [
        r'year\s+(?:to\s+)?(\d+)',
        r'year\s+of\s+study\s+(?:to\s+)?(\d+)',
        r'year\s*[=:]\s*(\d+)'
    ]
    for pattern in year_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            edit_data["year_of_study"] = int(match.group(1))
            break
    
    # Extract designation - patterns like "designation to Professor", "designation Professor"
    designation_patterns = [
        r'designation\s+(?:to\s+)?([a-zA-Z\s]+?)(?:,|\s+department|\s+email|$)',
        r'designation\s*[=:]\s*([a-zA-Z\s]+?)(?:,|\s+department|\s+email|$)'
    ]
    for pattern in designation_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            edit_data["designation"] = match.group(1).strip().title()
            break
    
    # Extract department
    dept_patterns = [
        r'department\s+(?:to\s+)?([a-zA-Z\s]+?)(?:,|\s+designation|\s+email|$)',
        r'dept\s+(?:to\s+)?([a-zA-Z\s]+?)(?:,|\s+designation|\s+email|$)'
    ]
    for pattern in dept_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            edit_data["department"] = match.group(1).strip()
            break
    
    # Extract email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    email_match = re.search(email_pattern, query)
    if email_match:
        edit_data["email"] = email_match.group()
    
    # Extract program
    program_patterns = [
        r'program\s+(?:to\s+)?([a-zA-Z]+)',
        r'program\s*[=:]\s*([a-zA-Z]+)'
    ]
    for pattern in program_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            edit_data["program"] = match.group(1).upper()
            break
    
    # Check if we have any meaningful data
    has_data = any(v is not None for v in edit_data.values())
    
    return edit_data if has_data else None


def _extract_find_data(query: str):
    """
    Extract search/find data from query
    """
    find_data = {
        "identifier": None,
        "program": None,
        "department": None,
        "year": None,
        "semester": None
    }
    
    query_lower = query.lower()
    
    # Extract identifier (roll_no like MCA1001)
    identifier_pattern = r'\b((?:MCA|MMS)\d{3,4})\b'
    identifier_match = re.search(identifier_pattern, query, re.IGNORECASE)
    if identifier_match:
        find_data["identifier"] = identifier_match.group(1).upper()
    
    # Extract program/department (MCA, MMS, etc.)
    if 'mca' in query_lower:
        find_data["program"] = "MCA"
        find_data["department"] = "MCA"
    elif 'mms' in query_lower:
        find_data["program"] = "MMS"
        find_data["department"] = "MMS"
    
    # Extract year
    year_patterns = [r'year\s*(\d+)', r'(\d+)(?:st|nd|rd|th)\s+year']
    for pattern in year_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            find_data["year"] = int(match.group(1))
            break
    
    # Extract semester
    semester_patterns = [r'semester\s*(\d+)', r'sem\s*(\d+)']
    for pattern in semester_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            find_data["semester"] = int(match.group(1))
            break
    
    has_data = any(v is not None for v in find_data.values())
    return find_data if has_data else None


def _extract_course_data(query: str):
    """
    Extract course creation data from query
    """
    course_data = {
        "course_name": None,
        "course_id": None,
        "program": None,
        "department": None,
        "semester": None,
        "credits": None
    }
    
    query_lower = query.lower()
    
    # Extract course name - "add course Database Systems"
    course_name_patterns = [
        r'add\s+course\s+([a-zA-Z\s&]+?)(?:\s+to|\s+for|\s+in|\s+semester|$)',
        r'create\s+course\s+([a-zA-Z\s&]+?)(?:\s+to|\s+for|\s+in|\s+semester|$)',
        r'new\s+course\s+([a-zA-Z\s&]+?)(?:\s+to|\s+for|\s+in|\s+semester|$)'
    ]
    for pattern in course_name_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            course_data["course_name"] = match.group(1).strip().title()
            break
    
    # Extract program
    if 'mca' in query_lower:
        course_data["program"] = "MCA"
    elif 'mms' in query_lower:
        course_data["program"] = "MMS"
    
    # Extract semester
    semester_patterns = [r'semester\s*(\d+)', r'sem\s*(\d+)']
    for pattern in semester_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            course_data["semester"] = int(match.group(1))
            break
    
    # Extract credits
    credits_patterns = [r'(\d+)\s*credits?', r'credits?\s*(\d+)']
    for pattern in credits_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            course_data["credits"] = int(match.group(1))
            break
    
    has_data = any(v is not None for v in course_data.values())
    return course_data if has_data else None


def _extract_leave_data(query: str):
    """
    Extract leave request data from query
    """
    from datetime import datetime, timedelta
    
    leave_data = {
        "leave_type": None,
        "start_date": None,
        "end_date": None,
        "reason": None
    }
    
    query_lower = query.lower()
    
    # Extract leave type
    if 'sick' in query_lower:
        leave_data["leave_type"] = "sick"
    elif 'personal' in query_lower:
        leave_data["leave_type"] = "personal"
    elif 'emergency' in query_lower:
        leave_data["leave_type"] = "emergency"
    else:
        leave_data["leave_type"] = "other"
    
    # Extract dates - patterns like "Feb 10", "February 10", "10 Feb", "2026-02-10"
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # ISO format
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s*\d{4})?)',  # Feb 10, 2026
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s*,?\s*\d{4})?)'  # 10 Feb 2026
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        dates_found.extend(matches)
    
    # Parse dates
    current_year = datetime.now().year
    for i, date_str in enumerate(dates_found[:2]):  # Max 2 dates
        try:
            # Try ISO format first
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                # Try various formats
                for fmt in ['%B %d %Y', '%B %d, %Y', '%B %d', '%b %d %Y', '%b %d, %Y', '%b %d',
                           '%d %B %Y', '%d %B', '%d %b %Y', '%d %b']:
                    try:
                        parsed_date = datetime.strptime(date_str.strip(), fmt)
                        if parsed_date.year == 1900:  # No year in format
                            parsed_date = parsed_date.replace(year=current_year)
                        break
                    except ValueError:
                        continue
                else:
                    continue
            
            date_formatted = parsed_date.strftime('%Y-%m-%d')
            if i == 0:
                leave_data["start_date"] = date_formatted
                leave_data["end_date"] = date_formatted  # Default end = start
            else:
                leave_data["end_date"] = date_formatted
        except Exception:
            continue
    
    # Extract reason if present
    reason_patterns = [
        r'(?:reason|because|for|due to)[:\s]+(.+?)(?:$|from|on)',
    ]
    for pattern in reason_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            leave_data["reason"] = match.group(1).strip()
            break
    
    has_data = any(v is not None for v in leave_data.values())
    return leave_data if has_data else None


def _extract_attendance_threshold(query: str):
    """
    Extract attendance threshold percentage from query.
    Returns default of 75 if no specific threshold found.
    """
    query_lower = query.lower()
    
    # Patterns to extract percentage threshold
    patterns = [
        r'below\s*(\d+)\s*%',        # "below 50%"
        r'less\s*than\s*(\d+)\s*%',  # "less than 75%"
        r'under\s*(\d+)\s*%',        # "under 50%"
        r'(\d+)\s*%\s*attendance',   # "50% attendance"
        r'attendance\s*(?:below|less than|under)?\s*(\d+)',  # "attendance below 50"
        r'(\d+)\s*percent',          # "50 percent"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            return int(match.group(1))
    
    # Default threshold
    return 75


def _extract_course_id(query: str):
    """
    Extract course name or ID from query
    """
    query_lower = query.lower()
    
    # Phrases to ignore (not course names)
    ignore_phrases = [
        'my students', 'my student', 'my courses', 'my course', 'my class', 'my classes',
        'my assignments', 'my assignment', 'my results', 'my result', 'my attendance',
        'my fees', 'my fee', 'my marks', 'my grades', 'my exams', 'my exam',
        'all students', 'all courses', 'the students', 'the student', 
        'each student', 'every student', 'this course', 'that course',
        'pending assignments', 'pending assignment', 'submitted assignments',
        'me', 'my', 'the', 'this', 'that', 'a', 'an', 'all', 'each', 'every'
    ]
    
    # Common course patterns - course codes like MCA201, CSE301, etc.
    code_pattern = r'\b([A-Z]{2,4}\d{2,4})\b'
    code_match = re.search(code_pattern, query, re.IGNORECASE)
    if code_match:
        return code_match.group(1).upper()
    
    # Extract course name after "in" keyword
    # e.g., "attendance in Computer Networks" -> "Computer Networks"
    in_pattern = r'\bin\s+([A-Za-z][A-Za-z\s&]+?)(?:\s*$|\s*\?|\s+for|\s+of)'
    in_match = re.search(in_pattern, query, re.IGNORECASE)
    if in_match:
        course_name = in_match.group(1).strip()
        # Filter out common phrases that aren't course names
        if course_name.lower() not in ignore_phrases and len(course_name) > 2:
            return course_name
    
    # Extract course name after "for" keyword
    for_pattern = r'\bfor\s+([A-Za-z][A-Za-z\s&]+?)(?:\s*$|\s*\?|\s+in)'
    for_match = re.search(for_pattern, query, re.IGNORECASE)
    if for_match:
        course_name = for_match.group(1).strip()
        # Filter out common phrases that aren't course names
        if course_name.lower() not in ignore_phrases and len(course_name) > 2:
            return course_name
    
    # Known course names (partial matching)
    known_courses = [
        'computer networks', 'data structures', 'database', 'dbms', 'algorithms',
        'web technologies', 'java', 'python', 'machine learning', 'cloud computing',
        'operating systems', 'os', 'software engineering', 'computer architecture',
        'discrete mathematics', 'calculus', 'linear algebra', 'statistics',
        'object oriented programming', 'oop', 'mobile application', 'information security',
        'big data', 'artificial intelligence', 'ai', 'deep learning', 'data mining',
        'e commerce', 'ecommerce', 'financial management', 'marketing', 'hr', 'human resource'
    ]
    
    for course in known_courses:
        if course in query_lower:
            return course.title()
    
    return None


def _keyword_based_intent(query: str):
    """
    Fallback keyword-based intent detection when Gemini API is unavailable
    """
    query_lower = query.lower()
    
    # Delete keywords (most specific - check first)
    delete_teacher_keywords = ['delete teacher', 'remove teacher', 'delete faculty', 'remove faculty']
    delete_student_keywords = ['delete student', 'remove student']
    
    # Find/Search keywords
    find_teacher_keywords = ['find teacher', 'search teacher', 'show teacher', 'teacher details', 'find faculty']
    find_student_keywords = ['find student', 'search student', 'show student', 'student details', 'find all mca', 'find all mms', 'list students', 'show all students']
    
    # Password reset keywords
    reset_password_keywords = ['reset password', 'change password', 'forgot password', 'new password']
    
    # Course management keywords
    add_course_keywords = ['add course', 'create course', 'new course']
    
    # Timetable keywords
    timetable_keywords = ['timetable', 'schedule', 'my schedule', 'classes today', 'today class', 'weekly schedule', "what's my schedule", 'when is my class']
    
    # Announcement keywords
    announcement_keywords = ['announcement', 'announcements', 'notice', 'notices', 'latest news', 'what\'s new', 'any news']
    
    # Academic calendar keywords
    calendar_keywords = ['academic calendar', 'when are exams', 'exam schedule', 'holiday', 'holidays', 'semester dates', 'when is exam', 'exam dates']
    
    # Leave keywords
    apply_leave_keywords = ['apply leave', 'apply for leave', 'take leave', 'request leave', 'sick leave', 'personal leave']
    leave_status_keywords = ['leave status', 'my leave', 'leave request status', 'leave approved']
    
    # Edit teacher/student keywords
    edit_teacher_keywords = ['edit teacher', 'update teacher', 'change teacher', 'modify teacher', 'edit faculty', 'update faculty']
    edit_student_keywords = ['edit student', 'update student', 'change student', 'modify student']
    
    # Add teacher/student keywords
    add_teacher_keywords = ['add teacher', 'create teacher', 'new teacher', 'register teacher', 'add faculty', 'create faculty', 'new faculty']
    add_student_keywords = ['add student', 'create student', 'new student', 'register student', 'enroll student']
    list_dept_keywords = ['list departments', 'show departments', 'available departments', 'all departments', 'what departments']
    
    # Attendance keywords (including common typos)
    attendance_keywords = ['attendance', 'attendence', 'attendances', 'attended', 'absent', 'present', 'classes attended', 'attendance percentage', 'my attendance', 'my attendence']
    
    # Low attendance keywords (for teachers/admins)
    low_attendance_keywords = ['below 50%', 'below 75%', 'less than 50%', 'less than 75%', 'low attendance', 
                               'students with attendance below', 'attendance less than', 'under 50%', 'under 75%',
                               'how many students below', 'students below', 'defaulters', 'shortage']
    
    # Pending submission keywords (for teachers)
    pending_submission_keywords = ['remaining to submit', 'haven\'t submitted', 'havent submitted', 'not submitted',
                                   'who hasn\'t submitted', 'who hasnt submitted', 'pending submission', 
                                   'yet to submit', 'students remaining', 'students who haven\'t', 'still to submit',
                                   'left to submit']
    
    # Fees keywords
    fees_keywords = ['fees', 'fee', 'payment', 'dues', 'pending amount', 'money', 'paid', 'owe', 'tuition', 'fee status']
    
    # Assignment keywords
    assignment_keywords = ['assignment', 'assignments', 'homework', 'submission', 'submissions', 'deadline', 'deadlines', 'due date', 'pending work', 'submitted', 'pending assignment', 'my assignment']
    
    # Results keywords  
    results_keywords = ['result', 'results', 'marks', 'grade', 'grades', 'score', 'scores', 'exam', 'exams', 'test', 'performance', 'gpa', 'cgpa', 'my result', 'my marks', 'my score']
    
    intent = "unknown"
    user_data = None
    course_id = None
    
    # Pattern for roll numbers like MCA1001, MMS2001 or teacher IDs like MCA001
    identifier_pattern = r'\b(MCA|MMS)\d{3,4}\b'
    identifier_match = re.search(identifier_pattern, query, re.IGNORECASE)
    
    # Check delete operations first (most destructive, most specific)
    if any(kw in query_lower for kw in delete_teacher_keywords):
        intent = "delete_teacher"
        user_data = _extract_edit_data(query)
    elif any(kw in query_lower for kw in delete_student_keywords):
        intent = "delete_student"
        user_data = _extract_edit_data(query)
    # Check find/search operations
    elif any(kw in query_lower for kw in find_teacher_keywords):
        intent = "find_teacher"
        user_data = _extract_edit_data(query)
    elif any(kw in query_lower for kw in find_student_keywords):
        intent = "find_student"
        user_data = _extract_find_data(query)
    # Password reset
    elif any(kw in query_lower for kw in reset_password_keywords):
        intent = "reset_password"
        user_data = _extract_edit_data(query)
    # Course management
    elif any(kw in query_lower for kw in add_course_keywords):
        intent = "add_course"
        user_data = _extract_course_data(query)
    # Timetable
    elif any(kw in query_lower for kw in timetable_keywords):
        intent = "timetable"
    # Announcements
    elif any(kw in query_lower for kw in announcement_keywords):
        intent = "announcements"
    # Academic calendar
    elif any(kw in query_lower for kw in calendar_keywords):
        intent = "academic_calendar"
    # Leave requests
    elif any(kw in query_lower for kw in apply_leave_keywords):
        intent = "apply_leave"
        user_data = _extract_leave_data(query)
    elif any(kw in query_lower for kw in leave_status_keywords):
        intent = "leave_status"
    # Check edit operations
    elif any(kw in query_lower for kw in edit_teacher_keywords) or \
         (identifier_match and ('teacher' in query_lower or 'faculty' in query_lower)):
        intent = "edit_teacher"
        user_data = _extract_edit_data(query)
    elif any(kw in query_lower for kw in edit_student_keywords) or \
         (identifier_match and 'student' in query_lower):
        intent = "edit_student"
        user_data = _extract_edit_data(query)
    # Check add operations
    elif any(kw in query_lower for kw in add_teacher_keywords):
        intent = "add_teacher"
        user_data = _extract_user_data(query)
    elif any(kw in query_lower for kw in add_student_keywords):
        intent = "add_student"
        user_data = _extract_user_data(query)
    elif any(kw in query_lower for kw in list_dept_keywords):
        intent = "list_departments"
    # Check low attendance queries BEFORE regular attendance (more specific first)
    elif any(kw in query_lower for kw in low_attendance_keywords):
        intent = "low_attendance_students"
        threshold = _extract_attendance_threshold(query)
        user_data = {"threshold": threshold}
        course_id = _extract_course_id(query)
    # Check pending submission queries BEFORE regular assignment (more specific first)
    elif any(kw in query_lower for kw in pending_submission_keywords):
        intent = "pending_submissions"
        course_id = _extract_course_id(query)
    elif any(kw in query_lower for kw in attendance_keywords):
        intent = "attendance"
        course_id = _extract_course_id(query)
    elif any(kw in query_lower for kw in fees_keywords):
        intent = "fees"
    elif any(kw in query_lower for kw in assignment_keywords):
        intent = "assignments"
        course_id = _extract_course_id(query)
    elif any(kw in query_lower for kw in results_keywords):
        intent = "results"
        course_id = _extract_course_id(query)
    
    # Extract exam type
    exam_type = None
    exam_types = ['midterm', 'final', 'quiz', 'practical', 'internal', 'external', 'sessional']
    for et in exam_types:
        if et in query_lower:
            exam_type = et
            break
    
    return {
        "intent": intent,
        "course_id": course_id,
        "exam_type": exam_type,
        "user_data": user_data
    }
