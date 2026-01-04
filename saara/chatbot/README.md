# SARAA ERP Chatbot

A Django-based chatbot for the SARAA ERP system that allows students to query their academic information using natural language.

## Features

- 📊 **Attendance Queries** - Check attendance percentage and records
- 💰 **Fees Status** - View fee payments and pending dues
- 📝 **Assignment Tracking** - See pending and submitted assignments
- 🎓 **Results/Grades** - Check exam results and GPA

## Security Features

- **Role-based Access Control**: Only students can use the chatbot
- **Session Management**: Conversations are tracked per user with proper isolation
- **Restricted Queries**: Students cannot access information about teachers, admins, or other students
- **JWT Authentication**: Secure token-based authentication via Supabase

## API Endpoints

### Chat Endpoint

```
POST /api/chatbot/chat/
```

**Request Body:**

```json
{
  "query": "What is my attendance?",
  "session_id": "optional-uuid-for-continuing-conversation"
}
```

**Response:**

```json
{
  "response": "Your attendance is 85%. Great job!",
  "intent": "attendance",
  "parsed": {
    "intent": "attendance",
    "course_id": null,
    "exam_type": null
  },
  "session_id": "uuid-of-session"
}
```

### Session Management

**List Sessions:**

```
GET /api/chatbot/sessions/
```

**Get Session Details:**

```
GET /api/chatbot/sessions/<session_id>/
```

**Update Session:**

```
PATCH /api/chatbot/sessions/<session_id>/
```

**Delete Session:**

```
DELETE /api/chatbot/sessions/<session_id>/
```

**Clear All History:**

```
DELETE /api/chatbot/sessions/clear/
```

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables in `.env`:**

   ```
   GEMINI_API_KEY=your-gemini-api-key
   ```

3. **Run migrations:**

   ```bash
   python manage.py makemigrations chatbot
   python manage.py migrate
   ```

4. **Test the chatbot:**
   - Open `static/chat.html` in a browser
   - Enter your API URL and JWT token
   - Start chatting!

## Example Queries

- "What's my attendance?"
- "Show my attendance in Data Structures"
- "What fees do I owe?"
- "Any pending assignments?"
- "Show assignments for DBMS"
- "What are my exam results?"
- "My quiz scores"
- "My final exam marks in Computer Networks"

## Unauthorized Queries

The following queries will be blocked:

- "Show me all students' attendance"
- "What is teacher's salary?"
- "Show admin details"
- "Other student's results"
- "Faculty information"

## Architecture

```
chatbot/
├── agents/
│   ├── __init__.py
│   ├── attendance_agent.py    # Handles attendance queries
│   ├── fees_agent.py          # Handles fees queries
│   ├── assignment_agent.py    # Handles assignment queries
│   └── results_agent.py       # Handles results queries
├── nlp/
│   ├── __init__.py
│   ├── intent_extractor.py    # Uses Gemini AI for intent classification
│   └── response_formatter.py  # Formats responses using Gemini AI
├── models.py                  # ChatSession, ChatMessage models
├── views.py                   # API views
├── serializers.py             # DRF serializers
├── urls.py                    # URL routing
└── admin.py                   # Admin panel configuration
```

## NLP Processing

1. **Intent Extraction**: Uses Google's Gemini AI to classify user queries into intents (attendance, fees, assignments, results)
2. **Parameter Extraction**: Extracts course names and exam types from queries
3. **Response Generation**: Uses Gemini AI to convert raw data into friendly, conversational responses
4. **Fallback**: Keyword-based detection when Gemini API is unavailable
