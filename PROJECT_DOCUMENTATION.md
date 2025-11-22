# WealthPlay - Complete Project Documentation

## Table of Contents
1. [Portfolio Page (/portfolio) - AI Model Implementation](#1-portfolio-page)
2. [Django-React Integration](#2-django-react-integration)
3. [Scenario Page (/scenario) - How It Works](#3-scenario-page)
4. [Dashboard Page (/dashboard) - How It Works](#4-dashboard-page)
5. [Ollama Chatbot Integration](#5-ollama-chatbot-integration)

---

## 1. Portfolio Page (/portfolio)

### Overview
The Portfolio page is a **stock trading simulator** designed for beginner investors to practice trading without real money. It features a Groww-like interface with real-time portfolio tracking, buy/sell functionality, and AI-powered stock recommendations.

### AI Model Integration

#### What We Built
We integrated AI models for **stock recommendations and portfolio analysis**. The AI recommendation system analyzes stock data and provides buy/hold/sell suggestions.

#### How We Built It
1. **Placeholder AI Endpoint**: Currently, the AI recommendation endpoint (`/api/users/portfolio/ai-recommendation/`) uses a **random scoring system** that simulates AI recommendations.
2. **Future Integration**: The endpoint is designed to integrate with the AI models from the GitHub repository (https://github.com/Jugadveer/model) that uses:
   - **Machine Learning models** for stock price prediction
   - **Sentiment analysis** from news and market data
   - **Technical indicators** for trading signals

#### Dataset and Data Used
- **Stock Data**: We use **sample stock data** with major Indian stocks (RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, BHARTIARTL, HINDUNILVR, ITC, ASIANPAINT)
- **Price Data**: Simulated price movements with ±2% random variation to mimic real market volatility
- **Historical Data**: Generated 30-day price history for each stock using random walk algorithms
- **Portfolio Data**: User's holdings, balance, and transaction history stored in Django's `DemoPortfolio` model

#### Technical Implementation

**Backend (Django)**:
- **Model**: `DemoPortfolio` in `users/models.py`
  - Stores user balance (default: ₹50,000)
  - Holdings as JSON: `{symbol: {quantity, avg_price}}`
  - Total portfolio value calculated dynamically

- **API Endpoints** (`users/portfolio_views.py`):
  - `GET /api/users/portfolio/` - Get portfolio data
  - `GET /api/users/portfolio/stocks/` - List all stocks
  - `GET /api/users/portfolio/stocks/<symbol>/` - Get stock details
  - `POST /api/users/portfolio/buy/` - Buy stock
  - `POST /api/users/portfolio/sell/` - Sell stock
  - `GET /api/users/portfolio/history/` - Get portfolio value history (for charts)
  - `POST /api/users/portfolio/ai-recommendation/` - Get AI recommendation

**Frontend (React)**:
- **Main Component**: `Portfolio.jsx` with 4 sub-pages:
  - `PortfolioOverview.jsx` - Charts and summary
  - `PortfolioHoldings.jsx` - List of holdings
  - `PortfolioTrade.jsx` - Buy/sell interface
  - `PortfolioAnalysis.jsx` - Portfolio analysis

- **Charting**: Uses `recharts` library for:
  - Portfolio value over time (AreaChart)
  - Stock price history (LineChart)
  - Sector distribution (PieChart)

**Buy/Sell Logic**:
- **Buy**: Calculates total cost, checks balance, updates holdings with weighted average price
- **Sell**: Validates holdings, calculates sale amount, updates balance
- **Real-time Updates**: Portfolio data refreshes immediately after transactions

#### Features
1. **Portfolio Tracking**: Total value, invested amount, current value, P&L
2. **Stock Search**: Search and filter stocks
3. **Trading Interface**: Buy/sell with quantity input and order preview
4. **Price Charts**: Historical price visualization
5. **AI Recommendations**: Stock buy/hold/sell suggestions (placeholder for full AI integration)

---

## 2. Django-React Integration

### Architecture Overview
We use a **decoupled architecture** where Django serves as the **backend API** and React handles all **frontend rendering**. They communicate via REST APIs.

### How They're Linked

#### 1. **URL Routing**
- **Django** (`wealthplay/urls.py`):
  - All `/api/*` routes → Django REST API endpoints
  - All other routes → Served by React via `react_app.html` template
  
- **React Router** (`frontend/src/App.jsx`):
  - Handles client-side routing: `/dashboard`, `/course`, `/portfolio`, `/scenario`, etc.
  - Uses `BrowserRouter` for SPA (Single Page Application) navigation

#### 2. **API Communication**
- **CSRF Token**: 
  - React fetches CSRF token from `/api/csrf-token/`
  - Included in all POST/PUT/DELETE requests via `X-CSRFToken` header
  - Configured in `frontend/src/utils/api.js`

- **Axios Instance**: 
  - Base URL: `http://localhost:3000/api` (proxied to Django)
  - All API calls use `withCredentials: true` for session cookies

#### 3. **Vite Proxy Configuration**
```javascript
// frontend/vite.config.js
server: {
  proxy: {
    '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    '/course': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    '/scenario': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    '/dashboard': { target: 'http://127.0.0.1:8000', changeOrigin: true },
  }
}
```

This routes all `/api/*` requests from React (port 3000) to Django (port 8000).

#### 4. **Template Serving**
- **Django Template**: `templates/react_app.html` serves the React app
- **Catch-all Route**: Django's `path('<path:path>', ...)` catches all non-API routes and serves React
- **Static Files**: React build output goes to `static/react/` and is served by Django

#### 5. **Authentication Flow**
1. **Login/Signup**: React sends POST to `/api/courses/auth/login/` or `/signup/`
2. **Django**: Authenticates user, creates session cookie
3. **React**: Receives success response, updates `AuthContext`, redirects to `/dashboard`
4. **Protected Routes**: `PrivateRoute` component checks auth status before rendering

#### 6. **Data Flow Example**
```
User Action (React) → API Call (Axios) → Django View → Database → Response → React State Update → UI Re-render
```

**Example: Fetching Portfolio**
1. User navigates to `/portfolio`
2. `Portfolio.jsx` calls `api.getPortfolio()`
3. Axios sends GET to `/api/users/portfolio/`
4. Vite proxy forwards to Django
5. Django `get_portfolio()` view queries database
6. Returns JSON response
7. React updates state and displays portfolio

#### 7. **CORS & CSRF Configuration**
```python
# wealthplay/settings.py
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access
```

---

## 3. Scenario Page (/scenario)

### Overview
The Scenario page is an **interactive financial decision-making game** where users face real-life financial situations and make choices. It helps users practice financial decision-making in a risk-free environment.

### How It Works

#### Data Structure
**Scenarios** are stored in `scenarios.json` and `mentor_content/scenarios.json` with the following structure:
```json
{
  "id": "first_salary_50k",
  "title": "First Salary: ₹50,000",
  "story": "You just received your first salary...",
  "choices": [
    {
      "id": 1,
      "text": "Spend all on shopping",
      "type": "SPEND",
      "content": {
        "mentor": "This might feel good now but...",
        "balance_change": -50000,
        "insight": "Why this matters..."
      }
    }
  ]
}
```

#### Flow

1. **Start Quiz** (`/scenario`):
   - User clicks "Start Scenario"
   - Django's `start_quiz()` view selects 5 random scenarios
   - Creates a `QuizRun` record in database
   - Redirects to `/scenario/quiz/<run_id>`

2. **Play Scenario** (`/scenario/quiz/<run_id>`):
   - Django loads scenario data and choices
   - Renders `scenario_play.html` template
   - JavaScript handles:
     - Displaying scenario story
     - Showing choices with balance impact
     - "Explore Mode": Click choices to see "what if" without committing
     - Updating balance display
     - Recording decisions

3. **Decision Making**:
   - User clicks a choice
   - Balance updates immediately
   - Insight appears explaining why the choice matters
   - Decision history is tracked
   - "Next" button advances to next scenario

4. **Results** (`/scenario/quiz/<run_id>/result`):
   - Shows final score
   - Displays all decisions made
   - Provides feedback and learning points
   - Awards XP based on performance

#### Database Models
- **QuizRun**: Tracks a quiz session
  - `user`: Foreign key to User
  - `scenario_ids`: Comma-separated scenario IDs
  - `current_question_index`: Progress tracking
  - `total_score`: Accumulated score

#### Features
- **Explore Mode**: Try different choices before committing
- **Real-time Balance Updates**: See financial impact immediately
- **Insights**: Educational explanations for each choice
- **Score Tracking**: Points for wise decisions
- **XP Rewards**: Earn experience points for completing scenarios

---

## 4. Dashboard Page (/dashboard)

### Overview
The Dashboard is the **central hub** where users see their learning progress, XP level, achievements, and quick access to all features.

### How It Works

#### Components

1. **Header Section**:
   - Welcome message with username
   - Streak counter (days of consecutive learning)

2. **Level Card**:
   - Current level (Beginner/Intermediate/Advanced)
   - XP progress bar showing progress to next level
   - XP thresholds:
     - Beginner: 0-749 XP
     - Intermediate: 750-1199 XP
     - Advanced: 1200+ XP

3. **Action Cards** (4 cards):
   - **Learn**: Link to `/course` - Browse courses
   - **Practice**: Link to `/scenario` - Start scenarios
   - **Portfolio**: Link to `/portfolio` - Trading simulator
   - **Goals**: Link to `/goals` - Financial goals

4. **Achievements Section**:
   - Displays badges for milestones:
     - First Step
     - First Trade
     - 5 Day Streak
     - Portfolio Pro

5. **Today's Tip**:
   - Daily financial tip section

#### Data Flow

1. **Load Profile**:
   - `Dashboard.jsx` calls `api.getProfile()` on mount
   - Fetches from `/api/users/profile/`
   - Gets: `xp`, `level`, `streak`, `total_flashcards_flipped`, `total_mcqs_completed`, `total_modules_completed`

2. **XP Calculation**:
   - XP is awarded for:
     - Flipping flashcards: +5 XP per flashcard
     - Answering MCQs correctly: +10 XP per MCQ
     - Completing modules: +25 XP bonus

3. **Level Progression**:
   - Levels auto-update based on XP
   - Calculated in `users/models.py` → `UserProfile.calculate_level_from_xp()`
   - Progress bar shows: `(current_xp - level_start_xp) / (next_level_xp - level_start_xp) * 100`

4. **Real-time Updates**:
   - Dashboard refreshes when navigating back from courses/scenarios
   - XP and level updates happen automatically via API

#### Technical Implementation

**Frontend**: `frontend/src/pages/Dashboard.jsx`
- Uses `useState` for profile data
- `useEffect` to fetch on mount
- Calculates XP percentages and progress

**Backend**: `users/views.py`
- `get_profile()` endpoint aggregates data from:
  - `UserProfile` model (XP, level, streak)
  - `UserProgress` model (module completions)
  - `FlashcardProgress` model (flashcards flipped)
  - `MCQProgress` model (MCQs answered)

---

## 5. Ollama Chatbot Integration

### Overview
The Ollama chatbot is an **AI-powered financial mentor** that answers user questions about course content. It uses a **two-layer system**: fixed Q&A matching + Ollama LLM with context.

### How It Works

#### Architecture

**Two-Layer Response System**:

1. **Layer 1: Fixed Q&A Matching**
   - Each module has a `qna.json` file with pre-written Q&A pairs
   - Uses **fuzzy matching** (SequenceMatcher) to find similar questions
   - If match found (similarity > 70%), returns pre-written answer instantly

2. **Layer 2: Ollama LLM Generation**
   - If no fixed Q&A match, uses **Ollama** to generate response
   - Provides **context** from the current course/module
   - Uses **few-shot examples** from fixed Q&A to guide response style

#### Setup and Configuration

**Ollama Installation**:
1. Install Ollama from https://ollama.ai
2. Pull phi3 model: `ollama pull phi3`
3. Start Ollama service: `ollama serve` (runs on `http://localhost:11434`)

**Model Configuration** (`mentor_engine/course_mentor.py`):
```python
OLLAMA_MODEL = "phi3"  # Can be changed to llama3, llama2, mistral
OLLAMA_HOST = "http://localhost:11434"
```

#### Data Feeding

**No External Dataset Required**:
- Ollama uses the **course content itself** as context
- Each module's `summary`, `theory_text`, and `fixed_qna` are fed to Ollama
- Course metadata (title, source) provides additional context

**Context Provided to Ollama**:
1. **System Prompt**: Defines mentor persona and response style
2. **Course Context**: Course title, module title, module summary
3. **Theory Text**: Module content from database (if available)
4. **Few-shot Examples**: 3 Q&A pairs from fixed Q&A to guide response format

#### Technical Implementation

**Backend** (`mentor_engine/course_mentor.py`):

1. **`mentor_respond()` Function**:
   - Takes: `course_id`, `module_id`, `question`
   - Returns: `{type: "fixed" | "ai", answer: "...", confidence: 0-1}`

2. **Fixed Q&A Matching**:
   ```python
   def fuzzy_match_q(fixed_qna, user_q, cutoff=0.7):
       # Uses difflib.SequenceMatcher for similarity matching
       # Returns matching Q&A if similarity >= 0.7
   ```

3. **Ollama Generation**:
   ```python
   def generate_ollama_response(course, module, user_question, ollama_model="phi3"):
       # Builds context message with course/module info
       # Creates prompt with system instructions + context + few-shot examples
       # Calls Ollama API: ollama.chat(model="phi3", messages=[...])
   ```

**API Endpoint** (`chat/views.py`):
- `POST /api/chat/mentor/respond/`
- Receives: `{course_id, module_id, question}`
- Calls `mentor_respond()` from `mentor_engine.course_mentor`
- Returns JSON response

**Frontend** (`frontend/src/pages/LessonDetail.jsx`):
- User types question in chat input
- Sends POST to `/api/chat/mentor/respond/`
- Displays response in chat interface
- Shows "Fixed Answer" or "AI Answer" indicator

#### Error Handling

**Fallback Mechanisms**:
1. If Ollama is unavailable → Returns fallback message with module summary
2. If model not found → Tries common alternatives (llama3, llama2, mistral)
3. If connection fails → Uses module content to provide helpful response

**Fallback Response**:
```python
# If Ollama fails, provides:
- Module summary
- Theory text excerpt
- Relevant fixed Q&A
- Encouragement message
```

#### Features

1. **Context-Aware**: Always knows which course/module user is asking about
2. **Fast Responses**: Fixed Q&A provides instant answers for common questions
3. **Educational Tone**: System prompt ensures beginner-friendly, encouraging responses
4. **No Training Required**: Uses course content as context, no separate training dataset needed
5. **Offline Capable**: Fixed Q&A works even if Ollama is down

#### Data Sources

**Course Content Files**:
- `course_modules/<course_id>/<module_id>/qna.json` - Fixed Q&A pairs
- `course_modules/<course_id>/<module_id>/flash_cards.json` - Flashcards (can be used as context)
- Database `ModuleContent.theory_text` - Detailed module content

**No External Datasets**:
- All data comes from **course content** we created
- No scraping, no external APIs
- Self-contained and privacy-friendly

#### Example Flow

1. User asks: "What is a mutual fund?"
2. System checks `qna.json` for similar questions
3. No exact match found → Proceeds to Ollama
4. Builds context: Course title, module summary, theory text
5. Creates prompt with system instructions + context
6. Calls Ollama with phi3 model
7. Returns AI-generated answer in mentor's voice
8. Displays to user with "AI Answer" badge

---

## Summary

This project is a **comprehensive financial education platform** combining:
- **Django REST API** for backend logic and data management
- **React SPA** for modern, interactive frontend
- **Ollama LLM** for intelligent, context-aware chatbot
- **Trading Simulator** with portfolio management
- **Gamification** with XP, levels, and achievements
- **Interactive Scenarios** for practical learning

All components work together seamlessly to provide an engaging, educational experience for beginner investors.
