# 🎯 WealthPlay - Financial Learning Platform

<div align="center">

![WealthPlay](https://img.shields.io/badge/WealthPlay-Financial%20Learning-orange?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.0+-green?style=for-the-badge&logo=django)
![React](https://img.shields.io/badge/React-18.2-blue?style=for-the-badge&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue?style=for-the-badge&logo=typescript)

**Empowering first-time earners to build wealth confidently through interactive financial education**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Documentation](#-api-documentation) • [Development](#-development)

</div>

---

## 📖 Overview

WealthPlay is a comprehensive financial education platform combining interactive courses, real-time portfolio simulation, AI-powered mentorship, and gamified learning experiences. Built with Django REST Framework and React, it provides an immersive environment for users to master financial concepts through hands-on practice.

### 🎓 Key Highlights

- **Interactive Financial Courses**: Structured learning paths covering investing, budgeting, retirement planning, and more
- **Demo Portfolio Trading**: Practice trading with virtual ₹50,000 using real and simulated stocks
- **AI-Powered Mentor (Nex)**: Get instant answers with Gemini 2.0 Flash
- **Scenario-Based Quizzes**: Test financial decision-making with realistic scenarios
- **Stock Prediction Challenges**: Predict stock movements and compete on leaderboards
- **Achievement System**: Unlock 20+ achievements and track progress
- **ML-Powered Insights**: AI-driven stock predictions and portfolio recommendations

---

## ✨ Features

### 📚 Learning Modules
- **20+ Financial Courses**: Basics to advanced topics
- **Interactive Lessons**: Flashcards, MCQs, and Q&A sessions
- **Progress Tracking**: XP, levels, and streak tracking
- **Course Chatbot**: Instant help with course-specific questions

### 💼 Portfolio Simulation
- **Virtual Trading**: Trade with ₹50,000 virtual balance
- **Real & Simulated Stocks**: 16+ custom stocks with real market data
- **Portfolio Analysis**: AI recommendations and performance insights
- **ML Predictions**: Stock direction, volatility, and market regime predictions

### 🎮 Gamification
- **Financial Scenarios**: Decision-making in realistic situations
- **Stock Prediction Game**: Predict movements and earn points
- **Achievements**: 20+ unlockable achievements
- **Leaderboards**: Compete with other learners
- **Daily Streaks**: Maintain learning habits

### 🤖 AI Features
- **Nex Mentor**: Course-specific AI assistant (Gemini 2.0 Flash)
- **Smart Recommendations**: Personalized portfolio suggestions
- **Dynamic Insights**: Context-aware financial advice

---

## 🛠 Tech Stack

### Backend
- **Django 5.0+**: Web framework
- **Django REST Framework**: RESTful API development
- **PostgreSQL/SQLite**: Database (SQLite for local development)
- **Gemini 2.0 Flash**: AI mentor and content generation
- **LightGBM**: Stock prediction ML models
- **yfinance**: Real-time stock market data
- **Pandas & NumPy**: Data processing
- **scikit-learn**: ML utilities

### Frontend
- **React 18.2**: UI library
- **TypeScript 5.0+**: Type safety
- **Vite**: Lightning-fast build tool
- **Tailwind CSS**: Utility-first styling
- **React Router**: Client-side routing
- **Recharts**: Interactive data visualization
- **Axios**: HTTP client

### WebSockets
- **Django Channels**: Real-time communication
- **In-Memory Layer**: Local development (no Redis required)

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- pip and npm package managers

### Backend Setup

1. **Create virtual environment**
```bash
python -m venv venv
```

2. **Activate virtual environment**
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set:
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

5. **Apply database migrations**
```bash
python manage.py migrate
```

6. **Create admin user**
```bash
python manage.py createsuperuser
```

7. **Load initial data**
```bash
# Import financial scenarios
python manage.py import_scenarios

# Create stock prediction questions
python manage.py create_stock_questions

# Create achievement definitions
python manage.py create_achievements

# Import course modules (if using folder structure)
python manage.py import_module_folders
```

8. **Start development server**
```bash
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install Node dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## 🚀 Development

### Running Both Services

**Terminal 1 - Backend:**
```bash
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access the application at `http://localhost:3000`

### Production Build

```bash
# Build frontend
cd frontend
npm run build

# Collect static files
python manage.py collectstatic --noinput

# Run production server
gunicorn wealthplay.wsgi:application --bind 0.0.0.0:8000
```

---

## 📡 API Documentation

### Core Endpoints

#### User Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/profile/` | GET | Get current user profile |
| `/api/users/onboarding/` | POST | Save onboarding data |

#### Courses
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/courses/courses/` | GET | List all courses |
| `/api/courses/courses/{id}/` | GET | Get course details |
| `/api/courses/courses/{id}/topics/` | GET | Get course topics |
| `/api/courses/json/` | GET | Get courses in JSON format |
| `/api/courses/json/{course_id}/` | GET | Get course JSON details |
| `/api/courses/json/{course_id}/{module_id}/` | GET | Get module JSON details |

#### Learning Progress
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/progress/flashcards/` | GET | Get flashcard progress |
| `/api/users/progress/flashcards/flip/` | POST | Record flashcard flip |
| `/api/users/progress/mcqs/` | GET | Get MCQ progress |
| `/api/users/progress/mcqs/answer/` | POST | Submit MCQ answer |
| `/api/users/progress/module/` | GET | Get module progress |
| `/api/users/progress/module/complete/` | POST | Mark module as complete |

#### Portfolio Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/portfolio/` | GET | Get user portfolio |
| `/api/users/stocks/` | GET | List available stocks |
| `/api/users/stocks/{stock_id}/` | GET | Get stock details |
| `/api/users/portfolio/buy/` | POST | Buy stock |
| `/api/users/portfolio/sell/` | POST | Sell stock |
| `/api/users/portfolio/analytics/` | GET | Get portfolio analytics |
| `/api/users/portfolio/history/` | GET | Get portfolio transaction history |
| `/api/simulator/api/portfolio/` | GET | Paper trading portfolio |
| `/api/simulator/api/trade/` | POST | Execute paper trade |
| `/api/simulator/api/portfolio-analytics/` | GET | Paper trading analytics |

#### Financial Goals
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/goals/api/` | GET | Get all financial goals |
| `/api/users/goals/api/create/` | POST | Create new goal |
| `/api/users/goals/api/{goal_id}/update/` | POST | Update goal |
| `/api/users/goals/api/{goal_id}/delete/` | DELETE | Delete goal |

#### Scenarios & Quizzes
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scenario/api/start/` | POST | Start new quiz session |
| `/api/scenario/api/scenarios/` | GET | List all scenarios |
| `/api/scenario/api/scenario/{scenario_id}/` | GET | Get scenario details |
| `/api/scenario/api/quiz/{run_id}/` | GET | Get current quiz question |
| `/api/scenario/api/quiz/{run_id}/next/` | POST | Move to next question |
| `/api/scenario/api/submit-answer/` | POST | Submit quiz answer |
| `/api/scenario/api/quiz/{run_id}/result/` | GET | Get quiz results |

#### Stock Predictions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/challenge/random-stock-question/` | GET | Get random stock prediction question |
| `/api/users/challenge/submit-prediction/` | POST | Submit stock prediction |
| `/api/users/challenge/leaderboard/` | GET | Get challenge leaderboard |
| `/api/users/challenge/stats/` | GET | Get user challenge stats |

#### Achievements
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/achievements/` | GET | Get user achievements |
| `/api/users/achievements/check/` | POST | Check and unlock achievements |
| `/api/users/achievements/notify/` | POST | Mark achievement as notified |

#### Chat & Mentor
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/` | GET/POST | List/create chat messages |
| `/api/chat/by_lesson/` | GET | Get messages by lesson |
| `/api/chat/mentor/` | POST | Chat with course mentor |
| `/api/cursor/explain/` | POST | Get Nex mentor explanation |
| `/api/cursor/health/` | GET | Health check endpoint |

#### Market Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/market/news/` | GET | Get market news |

---

## 🗂 Project Structure

```
wealthplay/
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable React components
│   │   ├── pages/              # Page-level components
│   │   ├── contexts/           # React context providers
│   │   ├── utils/              # Utility functions
│   │   └── App.tsx             # Root component
│   ├── package.json            # Frontend dependencies
│   └── vite.config.js          # Vite configuration
│
├── backend/
│   ├── courses/                # Course management app
│   │   ├── models.py           # Course data models
│   │   ├── views.py            # Course API views
│   │   ├── serializers.py      # Course serializers
│   │   └── urls.py             # Course URL routing
│   │
│   ├── users/                  # User management app
│   │   ├── models.py           # User profiles and progress
│   │   ├── achievement_views.py # Achievement tracking
│   │   ├── portfolio_views.py   # Portfolio management
│   │   ├── challenge_views.py   # Challenge endpoints
│   │   ├── goals_views.py       # Financial goals API
│   │   └── progress_views.py    # Learning progress tracking
│   │
│   ├── simulator/              # Scenario quiz engine
│   │   ├── models.py           # Scenario and quiz models
│   │   ├── api_views.py        # Quiz API endpoints
│   │   ├── paper_trading_views.py # Paper trading engine
│   │   └── scenario_generator.py  # AI scenario generation
│   │
│   ├── chat/                   # Chat and messaging app
│   │   ├── models.py           # Message data models
│   │   ├── views.py            # Chat API views
│   │   ├── consumers.py        # WebSocket consumers
│   │   └── routing.py          # WebSocket routing
│   │
│   ├── cursor/                 # Nex mentor API
│   │   ├── mentor_engine.py    # AI mentor logic
│   │   └── views.py            # Mentor endpoints
│   │
│   ├── mentor_engine/          # AI mentor implementation
│   │   ├── gemini_client.py    # Gemini API client
│   │   ├── course_mentor.py    # Course-specific mentor
│   │   └── mentor.py           # Mentor logic
│   │
│   ├── ml/                     # Machine learning models
│   │   ├── train.py            # Model training script
│   │   ├── data_prep.py        # Data preparation
│   │   ├── models/             # Trained model artifacts
│   │   └── artifacts/          # Model data
│   │
│   ├── market_data/            # Stock market data endpoints
│   ├── uploads/                # File upload handling
│   │
│   ├── wealthplay/             # Django project settings
│   │   ├── settings.py         # Django configuration
│   │   ├── urls.py             # Main URL routing
│   │   ├── wsgi.py             # WSGI application
│   │   ├── asgi.py             # ASGI application
│   │   └── celery.py           # Celery configuration
│   │
│   ├── templates/              # Django templates
│   ├── static/                 # Frontend build output
│   ├── course_modules/         # Course content (20+ modules)
│   ├── mentor_content/         # Mentor scenarios and content
│   │
│   ├── requirements.txt        # Python dependencies
│   ├── manage.py               # Django management
│   ├── .env.example            # Example environment variables
│   └── db.sqlite3              # Local SQLite database
```

---

## 🤖 AI Mentor (Nex)

### Gemini Configuration

1. **Get API Key**
   - Visit [Google AI Studio](https://aistudio.google.com)
   - Create a new API key
   - Copy the key

2. **Add to Environment**
   ```env
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   ```

3. **Features**
   - Course-specific Q&A
   - General financial inquiries
   - Stock prediction feedback
   - Portfolio recommendations

---

## 📊 ML Models

### Included Models

- **Direction Model**: Predicts bullish/bearish/neutral trends
- **Volatility Model**: Predicts stock price volatility
- **Regime Model**: Market regime classification

### Training

```bash
# Prepare data
python ml/data_prep.py

# Train models
python ml/train.py
```

Models are automatically used for predictions on the platform.

---

## 🧪 Testing

```bash
# Run Django tests
python manage.py test

# Run specific app tests
python manage.py test users

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## 🌱 Environment Variables

Copy `.env.example` to `.env` and customize:

```env
# Django Configuration
SECRET_KEY=django-insecure-your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (leave empty for SQLite)
DATABASE_URL=

# Frontend/Backend Communication
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Optional: Redis (for production only)
# REDIS_URL=redis://localhost:6379/0
```

---

## 🐛 Troubleshooting

### ModuleNotFoundError: No module named 'chromadb'
- Vector database is optional; the system works without it
- If needed: `pip install chromadb`

### Port 3000 or 8000 already in use
```bash
# Change frontend port
cd frontend
npm run dev -- --port 3001

# Change backend port
python manage.py runserver 8001
```

### Database migrations failed
```bash
# Reset database
rm db.sqlite3
python manage.py migrate
```

### Frontend not loading
- Ensure backend is running on http://localhost:8000
- Check CORS settings in `.env`
- Clear browser cache and hard reload

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🤝 Support

For issues, questions, or suggestions, please open an issue in the repository.

---

<div align="center">

**Built with ❤️ for financial education**

Empowering the next generation of investors

</div>

