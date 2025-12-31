# Saara Backend

A Django REST API backend with Supabase authentication.

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd saara-backend
```

### 2. Create Virtual Environment

**Windows:**

```bash
python -m venv env
```

**macOS/Linux:**

```bash
python3 -m venv env
```

### 3. Activate Virtual Environment

**Windows (Command Prompt):**

```bash
env\Scripts\activate
```

**Windows (PowerShell):**

```bash
.\env\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source env/bin/activate
```

> You should see `(env)` at the beginning of your terminal prompt when activated.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

1. Copy the example environment file:

   ```bash
   copy .env.example .env   # Windows
   cp .env.example .env     # macOS/Linux
   ```

2. Edit `.env` and fill in your actual values:

   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   SUPABASE_DB_NAME=postgres
   SUPABASE_DB_USER=postgres.your-project-ref
   SUPABASE_DB_PASSWORD=your-db-password
   SUPABASE_DB_HOST=aws-0-region.pooler.supabase.com
   SUPABASE_DB_PORT=6543
   SUPABASE_JWT_SECRET=your-jwt-secret

   # Django Configuration
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   ```

   > Get Supabase credentials from: **Supabase Dashboard → Settings → API**

### 6. Run Database Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/`

## Deactivating Virtual Environment

When you're done working on the project:

```bash
deactivate
```

## Project Structure

```
saara-backend/
├── env/                 # Virtual environment (not committed to git)
├── saara/               # Main Django project
│   ├── settings.py      # Project settings
│   ├── urls.py          # URL routing
│   └── authapp/         # Authentication app
│       ├── views.py     # API views
│       ├── models.py    # Database models
│       ├── middleware.py # Supabase auth middleware
│       └── urls.py      # Auth URL routes
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (not committed to git)
```

## Common Commands

| Command                            | Description               |
| ---------------------------------- | ------------------------- |
| `python manage.py runserver`       | Start development server  |
| `python manage.py migrate`         | Apply database migrations |
| `python manage.py makemigrations`  | Create new migrations     |
| `python manage.py createsuperuser` | Create admin user         |
| `python manage.py shell`           | Open Django shell         |
| `pip freeze > requirements.txt`    | Update requirements file  |

## Troubleshooting

### Virtual environment not activating (PowerShell)

Run this command first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Module not found errors

Make sure your virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

### Database connection issues

- Verify your Supabase credentials in `.env`
- Check if your IP is allowed in Supabase network settings
