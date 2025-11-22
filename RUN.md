# WealthPlay - Setup and Run Instructions

This document provides step-by-step instructions to set up and run the WealthPlay project on any machine (Windows, macOS, or Linux).

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
2. **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
3. **Git** - [Download Git](https://git-scm.com/downloads)
4. **Ollama** - [Download Ollama](https://ollama.ai/download) (for AI mentor chatbot)

## Project Structure

```
Bios/
├── frontend/          # React frontend (Vite)
├── course_modules/    # Course content (JSON files)
├── users/             # Django app for user management
├── courses/           # Django app for course management
├── mentor_engine/     # AI mentor chatbot logic
├── wealthplay/        # Django project settings
└── manage.py          # Django management script
```

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Bios
```

## Step 2: Set Up Python Backend (Django)

### 2.1 Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Set Up Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2.4 Create Superuser (Optional - for admin access)

```bash
python manage.py createsuperuser
```

## Step 3: Set Up React Frontend

### 3.1 Navigate to Frontend Directory

```bash
cd frontend
```

### 3.2 Install Node Dependencies

```bash
npm install
```

### 3.3 Return to Project Root

```bash
cd ..
```

## Step 4: Set Up Ollama (AI Mentor Chatbot)

### 4.1 Install Ollama

Download and install Ollama from [https://ollama.ai/download](https://ollama.ai/download)

### 4.2 Pull Required Model

**Windows:**
```bash
ollama pull phi3
```

**macOS/Linux:**
```bash
ollama pull phi3
```

**Note:** The model only needs to be pulled once. It will be stored locally and won't need to be downloaded again.

### 4.3 Verify Ollama is Running

**Windows:**
```bash
ollama list
```

**macOS/Linux:**
```bash
ollama list
```

You should see `phi3` in the list.

## Step 5: Run the Application

You need to run **two servers** simultaneously:

### 5.1 Terminal 1: Django Backend Server

**Make sure you're in the project root directory (Bios/) and virtual environment is activated:**

```bash
python manage.py runserver 8000
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### 5.2 Terminal 2: React Frontend Server

**Open a new terminal/command prompt, navigate to the project root, and activate virtual environment (if needed), then:**

```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 6: Access the Application

1. Open your browser and go to: `http://localhost:3000`
2. You should see the WealthPlay landing page
3. Click "Sign Up" to create a new account or "Login" if you already have one

## How Features Work Across Different Machines

### Scenario Page
- **Location:** `/scenario` route
- **Data:** Quiz scenarios are served from Django backend via API endpoints
- **Storage:** User progress and quiz results are stored in Django database
- **Cross-machine:** All data is stored in the local SQLite database (`db.sqlite3`), so each machine will have its own data. To share data, you would need to set up a shared database (PostgreSQL, MySQL) or deploy to a server.

### AI Models (Portfolio Page)
- **Location:** `/portfolio` route
- **AI Models:** The portfolio uses local AI models for stock recommendations
- **Data:** Stock data is generated/simulated in the backend
- **Storage:** Portfolio holdings and transactions are stored in Django database (`DemoPortfolio` model)
- **Cross-machine:** Each user's portfolio is stored locally in SQLite. To share data, use a shared database.

### Courses
- **Location:** `/course` route
- **Data:** Course content is loaded from `course_modules/` folder (JSON files)
- **Storage:** User progress, XP, completed modules are stored in Django database
- **Cross-machine:** 
  - Course content (JSON files) is shared via Git repository
  - User progress is stored in local SQLite database
  - To share progress across machines, use a shared database

### Ollama Chatbot
- **Location:** Used in course modules (AI mentor)
- **Setup:** Requires Ollama to be installed and `phi3` model to be pulled
- **Cross-machine:** 
  - Each machine needs Ollama installed locally
  - Each machine needs to pull the `phi3` model once
  - The model runs locally on each machine

## Troubleshooting

### Issue: Port 8000 already in use

**Solution:**
```bash
# Find and kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Or use a different port:
python manage.py runserver 8001
# Then update frontend/vite.config.js proxy target to port 8001
```

### Issue: Port 3000 already in use

**Solution:**
```bash
# Find and kill the process using port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:3000 | xargs kill -9

# Or use a different port (Vite will prompt automatically)
```

### Issue: Module not found errors

**Solution:**
```bash
# Make sure virtual environment is activated
# Reinstall dependencies:
pip install -r requirements.txt

# For frontend:
cd frontend
npm install
cd ..
```

### Issue: Ollama model not found

**Solution:**
```bash
# Make sure Ollama is running
ollama list

# If phi3 is not listed, pull it:
ollama pull phi3

# Verify:
ollama run phi3
```

### Issue: CSRF token errors

**Solution:**
- Make sure Django server is running on port 8000
- Make sure React dev server is running on port 3000
- Clear browser cookies and try again
- Check that `CSRF_TRUSTED_ORIGINS` in `wealthplay/settings.py` includes `http://localhost:3000`

### Issue: Database errors

**Solution:**
```bash
# Delete existing database (WARNING: This deletes all data)
rm db.sqlite3  # macOS/Linux
del db.sqlite3  # Windows

# Recreate database:
python manage.py migrate
```

### Issue: Cannot connect to Django backend

**Solution:**
- Verify Django server is running: `http://127.0.0.1:8000/api/csrf-token/`
- Check `frontend/vite.config.js` proxy configuration
- Make sure both servers are running simultaneously

## Production Deployment Notes

For production deployment, you would need to:

1. **Set up a production database** (PostgreSQL recommended)
2. **Configure environment variables** for secret keys, database URLs, etc.
3. **Build React frontend**: `cd frontend && npm run build`
4. **Configure Django to serve static files**
5. **Set up a reverse proxy** (Nginx recommended)
6. **Use a production WSGI server** (Gunicorn recommended)
7. **Set up SSL/HTTPS certificates**
8. **Configure proper CORS and CSRF settings for production domain**

## Development Workflow

1. **Start Django backend:** `python manage.py runserver 8000` (Terminal 1)
2. **Start React frontend:** `cd frontend && npm run dev` (Terminal 2)
3. **Make changes** to either frontend or backend
4. **Frontend changes** will hot-reload automatically
5. **Backend changes** may require restarting Django server
6. **Test changes** in browser at `http://localhost:3000`

## Team Collaboration

When working with a team:

1. **Share Git repository** - All code is version controlled
2. **Share `course_modules/` folder** - Course content is in Git
3. **Individual databases** - Each developer has their own `db.sqlite3`
4. **Ollama setup** - Each developer needs to install Ollama and pull `phi3` model
5. **Environment variables** - If any are added, document them in `.env.example`

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- React Documentation: https://react.dev/
- Vite Documentation: https://vitejs.dev/
- Ollama Documentation: https://ollama.ai/docs

---

**Note:** If you encounter any issues not covered here, check the console logs in both the browser (F12) and the terminal running Django for error messages.

