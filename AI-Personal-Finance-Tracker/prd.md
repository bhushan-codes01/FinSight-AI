# 📄 Product Requirements Document (PRD)
# FinSight AI — Intelligent Personal Finance Tracker

**Version:** 1.0  
**Author:** Bhushan Wanere  
**GitHub:** https://github.com/bhushan-codes01/FinSight-AI  
**Live URL:** https://finsight-ai-7nhd.onrender.com  
**Last Updated:** June 2026  
**Status:** Active Development

---

## 1. 🎯 Target Users

### Primary User — The Young Professional (18–28 years)
- College students, fresh graduates, early-career professionals
- Earns a monthly salary or stipend (₹10,000 – ₹80,000/month)
- Has little to no financial education or budgeting discipline
- Uses UPI, credit cards, and digital wallets daily
- Overwhelmed by scattered spending — no single place to track it all
- Wants to save money but doesn't know where to start

### Secondary User — The Freelancer / Side Hustler
- Has irregular income from multiple sources
- Needs to track expenses across personal and work categories
- Wants AI guidance on how to manage unpredictable cash flow

### Secondary User — The Finance-Aware Student
- Learning about personal finance, SIPs, emergency funds
- Wants a tool that teaches while tracking
- Looking for AI explanations of financial concepts in simple language

### What They All Have in Common
- Comfortable with mobile/web apps
- Prefer dark-themed, modern UI (not spreadsheets)
- Want answers fast — no manual calculations
- Trust AI recommendations over generic financial advice

---

## 2. ✅ Success Criteria

### User Success
| Metric | Target |
|--------|--------|
| User can register and log in (email + Google) | < 60 seconds |
| User can add their first transaction | < 2 minutes |
| AI gives a meaningful spending insight | Within 1 API call |
| User understands their budget status at a glance | Zero learning curve |
| User can set and track a savings goal | < 3 minutes |

### Product Success
| Metric | Target |
|--------|--------|
| App loads on Render (cold start) | < 60 seconds |
| Dashboard renders with real data | < 2 seconds |
| AI chat response time | < 5 seconds |
| Mobile responsiveness | Works on 375px+ screens |
| Zero data loss on page refresh | Session + DB persistent |

### Portfolio/Placement Success
- Live deployed URL accessible to recruiters
- Clean GitHub repo with professional README
- Demonstrates: full-stack, AI integration, auth, payments, deployment
- Recruiter can register + test all core features in < 5 minutes

---

## 3. 🔥 Problem I Am Solving

### The Core Problem
**Most young Indians have no idea where their money goes.**

They earn every month, spend throughout the month, and reach the end with nothing saved — and no idea why. Existing solutions are either:
- Too complex (CA-grade software, Excel sheets)
- Too generic (basic expense apps with no intelligence)
- Too expensive (premium finance tools built for businesses)
- Not built for Indian users (INR, UPI, Indian spending categories)

### Specific Pain Points FinSight AI Solves

**Pain Point 1 — No visibility into spending habits**  
Most people can't answer "How much did I spend on food this month?" without manually checking bank statements. FinSight AI shows this instantly on the dashboard with visual charts.

**Pain Point 2 — No personalized financial advice**  
Generic finance blogs give the same advice to everyone. FinSight AI reads YOUR actual transaction data and gives advice specific to your situation — powered by Google Gemini.

**Pain Point 3 — Budget tracking is painful**  
People set budgets mentally but never track them. FinSight AI tracks in real-time, warns when you're at 80%, and alerts when you've gone over.

**Pain Point 4 — Savings goals have no accountability**  
"I want to save ₹50,000 for a laptop" stays a wish because there's no tracking. FinSight AI tracks goal progress and lets AI suggest how to hit targets faster.

**Pain Point 5 — No single place for everything**  
Users juggle bank apps, spreadsheets, notes, and memory. FinSight AI is one platform for income, expenses, budgets, goals, and AI advice.

---

## 4. ✨ Features Built

### 🔐 Authentication
- [x] Email + Password registration with password hashing (Werkzeug)
- [x] Secure login with Flask session management
- [x] Google OAuth 2.0 Sign-In (via Authlib)
- [x] Email verification flow (token-based, 24hr expiry)
- [x] Forgot Password + Reset Password flow
- [x] login_required decorator protecting all authenticated routes
- [x] Session persistence across page navigation
- [x] Account linking (Google login with existing email account)

### 📊 Dashboard
- [x] Total Income, Total Expenses, Net Balance, Savings Rate cards
- [x] Month-over-Month trend indicators on each card
- [x] Monthly Spending Trend bar/line chart (Chart.js)
- [x] Expense by Category doughnut chart (Chart.js)
- [x] Recent transactions list (last 10)
- [x] Budget status overview with progress bars
- [x] FinSight AI Coach widget with personalized message
- [x] Quick action pills (Add Transaction, Add Budget, New Goal, Ask AI)
- [x] Email verification banner for unverified users

### 💳 Transaction Management
- [x] Add transactions (amount, category, description, date, type)
- [x] Edit existing transactions
- [x] Delete transactions
- [x] Income / Expense type toggle
- [x] Category-wise organization (Food, Travel, Shopping, Housing, etc.)
- [x] Filter by category, date range, transaction type
- [x] Search by description / category
- [x] Recurring transactions (weekly/monthly flag)
- [x] CSV bank statement upload + AI analysis

### 🎯 Budget Management
- [x] Create monthly budgets per category
- [x] Real-time used / remaining tracking
- [x] Progress bars (green → yellow → red based on usage)
- [x] Over-budget warning badge
- [x] Budget status cards on dashboard

### 🏆 Savings Goals
- [x] Create savings goals with title, target amount, deadline
- [x] Add money to goals (progress tracking)
- [x] SVG circular progress rings (animated)
- [x] AI advice per goal (Gemini-powered)
- [x] Deadline countdown display
- [x] Empty state with CTA for new users

### 🤖 AI Financial Assistant (Google Gemini)
- [x] ChatGPT-style chat interface
- [x] Context-aware responses using user's real transaction data
- [x] Spending analysis ("Analyze my expenses this month")
- [x] Budget plan generation ("Create a budget for ₹30,000 income")
- [x] Savings recommendations ("How can I save more?")
- [x] Monthly summaries ("Summarize my June spending")
- [x] Financial literacy Q&A (SIPs, EMIs, emergency funds)
- [x] Suggestion chips on empty state
- [x] Chat history saved to database
- [x] CSV upload + AI analysis

### 📈 Analytics
- [x] Expense breakdown by category
- [x] Monthly spending trend (6-month view)
- [x] Savings rate calculation

### 💳 Membership & Payments
- [x] Free plan (10 AI messages/day, basic features)
- [x] Pro plan UI (₹199/month, ₹1999/year)
- [x] Razorpay Checkout integration (test mode)
- [x] Payment verification (signature validation)
- [x] Subscription tracking in database
- [x] Plan badge in sidebar (FREE / PRO ✦)
- [x] Pro upgrade card in sidebar for free users
- [x] Feature gating (PDF export, CSV analysis = Pro only)

### 🌍 Multi-Currency
- [x] 9 supported currencies (INR, USD, EUR, GBP, JPY, AUD, CAD, AED, SGD)
- [x] User currency preference saved in profile
- [x] Currency symbol applied across all pages
- [x] Gemini prompts updated with user's currency

### 📄 PDF Export (Pro Feature)
- [x] Monthly financial report as downloadable PDF
- [x] Includes: income, expenses, category breakdown, AI summary
- [x] Print-friendly styling (white background)
- [x] Generated via WeasyPrint

### 📧 Email Notifications
- [x] Email verification on registration
- [x] Password reset email
- [x] Budget warning alert (80% usage)
- [x] Budget exceeded alert (100%+ usage)
- [x] Styled HTML email templates
- [x] Gmail SMTP via Flask-Mail

### 🎨 UI/UX
- [x] Gen-Z dark theme (#0d0d0d base)
- [x] Glassmorphism cards (backdrop-filter blur)
- [x] Purple-pink gradient accent system
- [x] Space Grotesk + Plus Jakarta Sans typography
- [x] Smooth animations (fadeInUp, float, pulse-glow, shimmer)
- [x] Responsive design (mobile + desktop)
- [x] Custom scrollbar
- [x] Toast notifications for actions
- [x] Loading states and skeleton loaders
- [x] Category emoji icons on transactions

### 🚀 Deployment
- [x] Deployed on Render.com (free tier)
- [x] Gunicorn WSGI server
- [x] Environment variables secured (not committed)
- [x] GitHub repository with professional README

---

## 5. 🔧 What I Have NOT Built Yet

### High Priority (Should Build Next)
| Feature | Why It Matters | Effort |
|---------|---------------|--------|
| **Razorpay Live Mode** | KYC pending — needed for real revenue | Medium |
| **Mobile App (Flutter/React Native)** | Most users are on mobile | High |
| **Push Notifications** | Real-time budget alerts on mobile | Medium |
| **Advanced Analytics Page** | Year-over-year comparison, trend forecasting | Medium |
| **Recurring Transaction Auto-Entry** | Currently flagged but not auto-created | Low |

### Medium Priority (V2 Features)
| Feature | Why It Matters | Effort |
|---------|---------------|--------|
| **Bank API Integration (Setu/Finvu)** | Auto-import transactions from bank | High |
| **OCR Receipt Scanner** | Upload receipt photo → auto-fill transaction | High |
| **Investment Tracking (SIP, Stocks)** | High demand from target users | High |
| **AI Goal Planning** | Multi-step AI plan to achieve financial goals | Medium |
| **Dark/Light Mode Toggle** | User preference — accessibility | Low |
| **Spending Forecast** | AI predicts next month's expenses | Medium |
| **Multi-Account Support** | Track multiple bank accounts separately | High |
| **Export to Excel/CSV** | Users want data portability | Low |

### Low Priority (V3 / Future)
| Feature | Why It Matters | Effort |
|---------|---------------|--------|
| **Voice-Based AI Assistant** | Hands-free finance tracking | High |
| **Tax Report Generation** | ITR filing assistance | High |
| **Family/Group Finance Tracking** | Shared budgets for families | High |
| **AI Financial Coach (Scheduled)** | Weekly AI emails with insights | Medium |
| **Gamification** | Streaks, badges for saving habits | Medium |
| **EMI Calculator + Tracker** | Very common Indian use case | Low |
| **Insurance Tracker** | Track premium due dates | Low |
| **Localization (Hindi + Regional)** | Wider Indian market penetration | Medium |

### Technical Debt / Known Issues
- SQLite on Render free tier resets on idle restart (needs PostgreSQL migration for production)
- No automated tests (unit/integration tests not written)
- No rate limiting on API endpoints
- No CSRF protection on forms
- Error handling could be more comprehensive
- No admin panel / user management dashboard

---

## 📌 Summary

FinSight AI is a **portfolio-grade, production-ready personal finance platform** that combines full-stack web development with generative AI to solve a real problem faced by millions of young Indians. 

The core product is complete and deployed. The immediate next steps for a production-ready V2 are:
1. PostgreSQL migration (database persistence)
2. Razorpay live mode (after KYC)
3. Mobile app
4. Bank API integration

---

*Built by Bhushan Wanere · github.com/bhushan-codes01*
