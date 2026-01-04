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
    Parses user query and extracts intent, course_id, and exam_type
    Returns JSON with intent classification
    """
    prompt = f"""
You are an intent classifier for SARAA-ERP Assistant, a college ERP chatbot.
Analyze the user query and classify it into one of these intents:

"{query}"

Return ONLY valid JSON in this exact format:
{{
  "intent": "attendance" | "fees" | "assignments" | "results" | "unknown",
  "course_id": "<course_id or null>",
  "exam_type": "<exam_type or null>"
}}

Rules:
- intent "attendance": queries about attendance, classes attended, absent, percentage
- intent "fees": queries about fees, payments, dues, pending amount, money
- intent "assignments": queries about assignments, homework, submissions, deadlines, pending work, due dates
- intent "results": queries about marks, grades, exam scores, performance, test results
- intent "unknown": anything else not related to above

- course_id: Extract course names or codes like CSE301, DBMS, CSE302, Data Structures, etc. Set to null if not mentioned
- exam_type: Extract "midterm", "final", "quiz", "practical", etc. Set to null if not mentioned

Examples:
"What's my attendance in CSE301?" → {{"intent": "attendance", "course_id": "CSE301", "exam_type": null}}
"Show my fees status" → {{"intent": "fees", "course_id": null, "exam_type": null}}
"Pending assignments in DBMS" → {{"intent": "assignments", "course_id": "DBMS", "exam_type": null}}
"Assignments due this week" → {{"intent": "assignments", "course_id": null, "exam_type": null}}
"Show my assignments" → {{"intent": "assignments", "course_id": null, "exam_type": null}}
"My marks in final exam" → {{"intent": "results", "course_id": null, "exam_type": "final"}}
"My exam results" → {{"intent": "results", "course_id": null, "exam_type": null}}
"How much fees do I owe?" → {{"intent": "fees", "course_id": null, "exam_type": null}}
"My quiz scores in Data Structures" → {{"intent": "results", "course_id": "Data Structures", "exam_type": "quiz"}}
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
                "exam_type": parsed.get("exam_type")
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


def _keyword_based_intent(query: str):
    """
    Fallback keyword-based intent detection when Gemini API is unavailable
    """
    query_lower = query.lower()
    
    # Attendance keywords
    attendance_keywords = ['attendance', 'attended', 'absent', 'present', 'classes attended', 'attendance percentage']
    
    # Fees keywords
    fees_keywords = ['fees', 'fee', 'payment', 'dues', 'pending amount', 'money', 'paid', 'owe']
    
    # Assignment keywords
    assignment_keywords = ['assignment', 'homework', 'submission', 'deadline', 'due date', 'pending work', 'submitted']
    
    # Results keywords
    results_keywords = ['result', 'marks', 'grade', 'score', 'exam', 'test', 'performance', 'gpa', 'cgpa']
    
    intent = "unknown"
    
    if any(kw in query_lower for kw in attendance_keywords):
        intent = "attendance"
    elif any(kw in query_lower for kw in fees_keywords):
        intent = "fees"
    elif any(kw in query_lower for kw in assignment_keywords):
        intent = "assignments"
    elif any(kw in query_lower for kw in results_keywords):
        intent = "results"
    
    # Extract exam type
    exam_type = None
    exam_types = ['midterm', 'final', 'quiz', 'practical']
    for et in exam_types:
        if et in query_lower:
            exam_type = et
            break
    
    return {
        "intent": intent,
        "course_id": None,  # Keyword-based can't reliably extract course
        "exam_type": exam_type
    }
