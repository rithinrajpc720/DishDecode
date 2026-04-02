# 🔥 DishDecode — AI Food Video Analyzer

A full-stack Django web application that decodes food videos into structured recipes using AI.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install django

# 2. Navigate to project
cd dishdecode_project

# 3. Run migrations
python manage.py migrate

# 4. Start the server
python manage.py runserver
```

Open: http://127.0.0.1:8000

## 👤 Demo Accounts

| Role  | Username | Password   |
|-------|----------|------------|
| Demo  | demo     | demo1234   |
| Admin | admin    | admin1234  |

Admin panel: http://127.0.0.1:8000/admin/

## 📁 Project Structure

```
dishdecode_project/
├── core/               # Landing page & home
├── users/              # Auth: register, login, profile
├── videos/             # Video submission & analysis flow
├── recipes/            # Result, history, save features
├── ai_engine/          # AI service layer
│   └── services/
│       └── recipe_generator.py   # Core AI logic
├── templates/          # All HTML templates
├── static/
│   ├── css/main.css    # Full custom design system
│   └── js/main.js      # Interactions & animations
└── db.sqlite3          # SQLite database
```

## 🎨 Tech Stack
- **Backend:** Django (Python)
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Fonts:** Syne + DM Sans (Google Fonts)
- **Design:** Dark premium SaaS, glassmorphism, warm orange/amber gradients

## ✨ Features
- 🔐 User authentication (register, login, profile)
- 🎬 YouTube video URL submission
- 🤖 AI-powered recipe generation (8 dish types)
- 📊 Confidence score display
- 💾 Save recipes to personal collection
- 📂 Searchable, filterable history
- ✦ Extracted vs ~ Estimated recipe labeling
- 📱 Fully responsive design

## 🤖 AI Engine
The `ai_engine` app uses rule-based Python logic (`recipe_generator.py`) to generate structured recipe data from video URLs. It supports 8 dish categories (pasta, pizza, burger, steak, curry, sushi, ramen, tacos) with realistic ingredient lists, steps, tools, and AI notes. The architecture is ready for integration with real AI/ML models.
