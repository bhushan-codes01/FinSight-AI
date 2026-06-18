<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=220&section=header&text=FinSight%20AI&fontSize=90&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Your%20Intelligent%20Personal%20Finance%20OS%20%E2%9C%A6&descAlignY=58&descSize=20" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![Google Gemini](https://img.shields.io/badge/Gemini-1.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payments-02042B?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com)
[![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com)

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Live-brightgreen?style=flat-square)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blueviolet?style=flat-square)](CONTRIBUTING.md)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️%20by%20Bhushan-red?style=flat-square)](https://github.com/bhushan-codes01)

<br/>

> **FinSight AI** is a Gen-Z styled, AI-powered personal finance platform.  
> Track money. Understand habits. Grow wealth — with Google Gemini as your financial coach.

<br/>

**[🚀 Live Demo](https://finsight-ai-7nhd.onrender.com)** · **[✨ Features](#-features)** · **[⚙️ Setup](#-local-development-setup)** · **[🚢 Deploy](#-render-deployment)** · **[🤝 Contribute](#-contributing)**

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Screenshots](#-screenshots)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Local Development Setup](#-local-development-setup)
- [Environment Variables](#-environment-variables)
- [Render Deployment](#-render-deployment)
- [API Endpoints](#-api-endpoints)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🌟 Overview

**FinSight AI** is a full-stack personal finance management platform built with **Python Flask** and powered by **Google Gemini 1.5 Flash**. It combines intelligent financial coaching, real-time budget tracking, savings goal management, and Razorpay-powered subscription payments — all wrapped in a stunning Gen-Z dark glassmorphism UI.

```
💡 Built for: Placement Portfolios · Hackathons · Real-World Use · Internship Showcases
```

### Why FinSight AI?

Most young Indians have no idea where their money goes. Existing apps are either too complex, too generic, or not built for Indian users. FinSight AI solves this with:

- 🤖 **AI that knows YOUR data** — Gemini reads your actual transactions, not generic advice
- 📊 **Visual clarity** — Charts, progress rings, and color-coded budgets at a glance
- 💳 **Real payments** — Razorpay-powered Pro subscriptions
- 🔐 **Enterprise-grade auth** — Firebase + Google OAuth + email verification

---

## 🚀 Live Demo

> 🔗 **[https://finsight-ai-7nhd.onrender.com](https://finsight-ai-7nhd.onrender.com)**

| Field | Value |
|:------|:------|
| Demo Email | `demo@finsight.ai` |
| Demo Password | `demo1234` |
| Pro Test Card | `4111 1111 1111 1111` · Expiry: `12/30` · CVV: `123` |

> ⚠️ Hosted on Render free tier — first load may take 30–60 seconds to wake up.

---

## 📸 Screenshots

<div align="center">

### 🏠 Landing Page
```
[ Add screenshot: screenshots/landing.png ]
```

### 📊 Dashboard
```
[ Add screenshot: screenshots/dashboard.png ]
```

### 🤖 AI Financial Assistant
```
[ Add screenshot: screenshots/chatbot.png ]
```

### 💰 Budget Manager
```
[ Add screenshot: screenshots/budgets.png ]
```

### 📄 PDF Report
```
[ Add screenshot: screenshots/report.png ]
```

</div>

> 📁 Add a `screenshots/` folder and replace placeholders with:
> ```md
> ![Dashboard](screenshots/dashboard.png)
> ```

---

## ✨ Features

### 🔐 Authentication
- [x] Email + Password registration with Werkzeug password hashing
- [x] Google OAuth 2.0 Sign-In via Firebase
- [x] Email verification with 24-hour token expiry
- [x] Forgot Password + Reset Password flow
- [x] Secure session management with `login_required` protection
- [x] Account linking (Google login with existing email account)

### 📊 Dashboard
- [x] Real-time Total Income, Expenses, Net Balance, Savings Rate cards
- [x] Monthly Spending Trend chart (Chart.js area chart)
- [x] Expense by Category doughnut chart
- [x] AI Coach widget with personalized Gemini insights
- [x] Quick action pills (Add Transaction, Add Budget, New Goal, Ask AI)
- [x] Recent transactions overview (last 10)
- [x] Budget status with color-coded progress bars

### 💳 Transaction Management
- [x] Add / Edit / Delete transactions
- [x] Income & Expense type toggle
- [x] 10+ categories with emoji icons
- [x] Weekly & Monthly recurring transactions
- [x] Filter by category, date range, type
- [x] Full-text search by description / category
- [x] CSV bank statement upload with AI parsing

### 🎯 Budget Management
- [x] Monthly budgets per category
- [x] Real-time used / remaining tracking
- [x] 🟢 On Track → 🟡 Warning (80%) → 🔴 Over Budget (100%+)
- [x] Instant visual progress bars

### 🏆 Savings Goals
- [x] Create goals with title, target amount, and deadline
- [x] Animated SVG circular progress rings
- [x] Deadline countdown display
- [x] AI-powered goal advice via Google Gemini
- [x] Add money to goals with progress updates

### 🤖 AI Financial Assistant
- [x] ChatGPT-style interface powered by **Google Gemini 1.5 Flash**
- [x] Context-aware responses using your real transaction data
- [x] Spending pattern analysis
- [x] Personalized savings recommendations
- [x] Budget plan generation for any income
- [x] Monthly financial summaries
- [x] Financial literacy Q&A (SIPs, EMIs, emergency funds)
- [x] CSV bank statement analysis
- [x] Chat history saved to database

### 💳 Subscription & Payments
- [x] Free plan (10 AI messages/day, basic features)
- [x] Pro plan (₹199/month · ₹1999/year)
- [x] Razorpay Checkout integration with signature verification
- [x] Plan badge in sidebar (FREE · PRO ✦)
- [x] Feature gating (PDF export = Pro only)
- [x] Subscription tracking with expiry management

### 🌍 Multi-Currency Support
- [x] 9 currencies — INR ₹ · USD $ · EUR € · GBP £ · JPY ¥ · AUD A$ · CAD C$ · AED د.إ · SGD S$
- [x] Preference saved per user
- [x] Applied across all pages, charts, and AI responses

### 📄 PDF Reports *(Pro Feature)*
- [x] Warm Premium themed monthly report (gold/charcoal)
- [x] Income, expenses, savings summary
- [x] Category breakdown with progress bars
- [x] SVG savings goal progress rings
- [x] Full transaction history table
- [x] Gemini AI-generated insights paragraph
- [x] Generated via WeasyPrint

### 📧 Email Notifications
- [x] Email verification on registration
- [x] Password reset email
- [x] Budget warning at 80% usage
- [x] Budget exceeded alert at 100%+
- [x] Styled HTML email templates via Flask-Mail + Gmail SMTP

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| **Language** | Python 3.10+ | Core backend language |
| **Framework** | Flask 3.0 | Web framework, routing, blueprints |
| **Database** | SQLite (dev) · PostgreSQL (prod) | Data persistence |
| **Auth** | Firebase Auth + Google OAuth 2.0 | User authentication |
| **Password Security** | Werkzeug | Password hashing |
| **AI / LLM** | Google Gemini 1.5 Flash | Financial intelligence & chat |
| **Payments** | Razorpay Checkout | Subscription payments |
| **PDF Generation** | WeasyPrint | HTML → PDF conversion |
| **Email** | Flask-Mail + Gmail SMTP | Notifications & verification |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JS | UI structure & interactivity |
| **Charts** | Chart.js | Data visualization |
| **Icons** | Font Awesome 6 | UI icons |
| **Fonts** | Space Grotesk + Plus Jakarta Sans | Typography |
| **Deployment** | Render.com + Gunicorn | Production hosting |
| **Version Control** | Git + GitHub | Source control |

---

## 📁 Project Structure

```
FinSight-AI/
│
├── 📄 app.py                        # Flask app entry point, DB init
├── 📄 requirements.txt              # Python dependencies
├── 📄 Procfile                      # Render: web: gunicorn app:app
├── 📄 render.yaml                   # Render deployment config
├── 📄 .env                          # Environment variables (not committed)
├── 📄 .env.example                  # Environment template
├── 📄 .gitignore
│
├── 📂 models/
│   ├── user.py
│   ├── transaction.py
│   ├── budget.py
│   └── goal.py
│
├── 📂 routes/
│   ├── auth.py                      # /register /login /logout /verify
│   ├── billing.py                   # /upgrade /billing/create-order /verify-payment
│   ├── budget.py                    # Budget CRUD
│   ├── chatbot.py                   # POST /chat (Gemini AI)
│   ├── goals.py                     # Goals CRUD + /goals/advice
│   ├── profile.py                   # User profile + settings
│   ├── reports.py                   # GET /reports/pdf
│   └── transactions.py              # Transactions CRUD
│
├── 📂 services/
│   ├── analytics.py                 # Spending analytics calculations
│   ├── csv_processor.py             # Bank CSV upload + parse
│   ├── currency.py                  # Currency config + helpers
│   ├── db.py                        # Database connection helpers
│   ├── email_service.py             # Flask-Mail email functions
│   ├── gemini_service.py            # Google Gemini API wrapper
│   ├── pdf_service.py               # PDF generation helpers
│   ├── plan_gate.py                 # Feature gating (free vs pro)
│   └── report_generator.py         # WeasyPrint PDF generator
│
├── 📂 static/
│   ├── css/
│   │   └── style.css                # Global dark glassmorphism theme
│   ├── js/
│   │   ├── chat.js                  # AI chat interface
│   │   ├── dashboard.js             # Charts + dashboard logic
│   │   └── floating-chat.js        # Floating AI chat button
│   └── images/
│
├── 📂 templates/
│   ├── index.html                   # Landing page
│   ├── login.html                   # Sign in
│   ├── register.html                # Sign up
│   ├── dashboard.html               # Main dashboard
│   ├── transactions.html            # Transaction manager
│   ├── budgets.html                 # Budget planner
│   ├── goals.html                   # Savings goals
│   ├── chatbot.html                 # AI assistant
│   ├── settings.html                # User settings + currency
│   ├── upgrade.html                 # Pricing + Razorpay
│   └── report_template.html        # PDF report template
│
└── 📂 database/
    └── finance.db                   # SQLite database (auto-created)
```

---

## ⚙️ Local Development Setup

### Prerequisites
- [Python 3.10+](https://python.org/downloads/)
- [Git](https://git-scm.com/)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- [Firebase Project](https://console.firebase.google.com/)
- [Razorpay Account](https://razorpay.com/) *(optional for payments)*

### Step 1 — Clone the Repository

```bash
git clone https://github.com/bhushan-codes01/FinSight-AI.git
cd FinSight-AI
```

### Step 2 — Create Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS/Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values (see [Environment Variables](#-environment-variables) below).

### Step 5 — Initialize Database

```bash
python app.py
# Database tables are created automatically on first run
```

### Step 6 — Start Development Server

```bash
flask run
# OR
python app.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# ──────────────────────────────────────────────
#   FinSight AI — Environment Variables
# ──────────────────────────────────────────────

# Flask
FLASK_SECRET_KEY=your_super_secret_key_here_change_this
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///database/finance.db
# For production PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google OAuth 2.0 (Firebase / Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Firebase
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Razorpay Payments
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret

# Flask-Mail (Gmail SMTP)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password_16_chars
MAIL_DEFAULT_SENDER=your_email@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True

# App Settings
APP_NAME=FinSight AI
DEFAULT_CURRENCY=INR
```

> ⚠️ **Never commit `.env` to GitHub.** It is already listed in `.gitignore`.

### Getting API Keys

| Service | Where to Get |
|:--------|:-------------|
| **Gemini API Key** | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Google OAuth** | [console.cloud.google.com](https://console.cloud.google.com) → Credentials |
| **Firebase Config** | [console.firebase.google.com](https://console.firebase.google.com) → Project Settings |
| **Razorpay Keys** | [dashboard.razorpay.com](https://dashboard.razorpay.com) → Settings → API Keys |
| **Gmail App Password** | [myaccount.google.com](https://myaccount.google.com) → Security → App Passwords |

---

## 🚢 Render Deployment

### One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deployment Steps

**1. Push to GitHub**
```bash
git add .
git commit -m "ready for deployment"
git push origin main
```

**2. Create Render Web Service**
- Go to [dashboard.render.com](https://dashboard.render.com)
- Click **New** → **Web Service**
- Connect your `FinSight-AI` GitHub repository
- Configure:

| Setting | Value |
|:--------|:------|
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

**3. Add Environment Variables**

In Render Dashboard → your service → **Environment** tab, add all variables from `.env.example`.

**4. Deploy**

Click **Create Web Service** — Render auto-deploys on every `git push` to main.

### Files Required for Render

```
Procfile        →  web: gunicorn app:app
render.yaml     →  service configuration
requirements.txt → must include gunicorn
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description | Auth |
|:-------|:---------|:------------|:----:|
| `POST` | `/register` | Register new user | ❌ |
| `POST` | `/login` | User login | ❌ |
| `GET` | `/auth/google` | Google OAuth redirect | ❌ |
| `GET` | `/logout` | Logout session | ✅ |
| `GET` | `/dashboard` | Dashboard data | ✅ |
| `GET` | `/transactions` | List transactions | ✅ |
| `POST` | `/transactions` | Add transaction | ✅ |
| `PUT` | `/transactions/<id>` | Edit transaction | ✅ |
| `DELETE` | `/transactions/<id>` | Delete transaction | ✅ |
| `GET` | `/budgets` | List budgets | ✅ |
| `POST` | `/budgets` | Create budget | ✅ |
| `GET` | `/goals` | List savings goals | ✅ |
| `POST` | `/goals` | Create goal | ✅ |
| `POST` | `/goals/advice` | AI goal advice | ✅ |
| `POST` | `/chat` | AI financial chat | ✅ |
| `POST` | `/upload-csv` | Upload bank CSV | ✅ |
| `GET` | `/reports/pdf` | Download PDF report | ✅ Pro |
| `GET` | `/upgrade` | Pricing page | ✅ |
| `POST` | `/billing/create-order` | Create Razorpay order | ✅ |
| `POST` | `/billing/verify-payment` | Verify payment | ✅ |
| `GET` | `/settings` | User settings | ✅ |

---

## 🗺️ Roadmap

| Status | Feature |
|:------:|:--------|
| ✅ | Firebase Authentication (Google OAuth + Email) |
| ✅ | Dashboard with real-time charts |
| ✅ | Full transaction CRUD with recurring support |
| ✅ | Budget management with alerts |
| ✅ | Savings goals with SVG progress rings |
| ✅ | Google Gemini AI financial assistant |
| ✅ | Razorpay subscription payments |
| ✅ | WeasyPrint PDF monthly reports |
| ✅ | Multi-currency support (9 currencies) |
| ✅ | Email notifications (Flask-Mail) |
| ✅ | CSV bank statement upload & AI analysis |
| ✅ | Live deployment on Render |
| 🔄 | Razorpay Live Mode (KYC pending) |
| 🔄 | PostgreSQL migration for production |
| 📋 | Mobile app (Flutter) |
| 📋 | Bank API integration (Setu/Finvu) |
| 📋 | OCR receipt scanner |
| 📋 | Investment & SIP tracker |
| 📋 | AI spending forecast |
| 📋 | Dark/Light mode toggle |

> ✅ Completed · 🔄 In Progress · 📋 Planned

---

## 🤝 Contributing

Contributions are welcome!

```bash
# 1. Fork the repo
# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and commit
git commit -m "feat: add your feature description"

# 4. Push and open PR
git push origin feature/your-feature-name
```

### Commit Convention
```
feat:      New feature
fix:       Bug fix
style:     UI/CSS changes
refactor:  Code restructuring
docs:      Documentation update
```

---

## 📄 License

```
MIT License — Copyright (c) 2026 Bhushan Wanere

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software to use, copy, modify, merge, publish, and
distribute, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
```

See the full [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

<div align="center">

<img src="https://avatars.githubusercontent.com/bhushan-codes01" width="100" style="border-radius:50%" alt="Bhushan Wanere"/>

### Bhushan Wanere
*Full Stack Developer · AI Enthusiast · Finance Tech Builder*

[![GitHub](https://img.shields.io/badge/GitHub-bhushan--codes01-181717?style=for-the-badge&logo=github)](https://github.com/bhushan-codes01)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/YOUR_LINKEDIN_HERE)
[![Live Demo](https://img.shields.io/badge/Live-finsight--ai-46E3B7?style=for-the-badge&logo=render)](https://finsight-ai-7nhd.onrender.com)

</div>

---

## 🙏 Acknowledgements

- [Google Gemini](https://ai.google.dev) — AI financial intelligence
- [Firebase](https://firebase.google.com) — Authentication platform
- [Razorpay](https://razorpay.com) — Payment gateway
- [Flask](https://flask.palletsprojects.com) — Python web framework
- [WeasyPrint](https://weasyprint.org) — PDF generation
- [Chart.js](https://chartjs.org) — Data visualization
- [Shields.io](https://shields.io) — Badges
- [Capsule Render](https://github.com/kyechan99/capsule-render) — README header

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer" width="100%"/>

**⭐ Star this repo if you found it helpful!**

*Built with ❤️ by [Bhushan Wanere](https://github.com/bhushan-codes01)*

</div>
