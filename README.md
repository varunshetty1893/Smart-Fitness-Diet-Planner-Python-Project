<div align="center">

# 🥗💪 Smart Fitness & Diet Planner

### A Rule-Based Personalized Health Recommendation System

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![HTML5](https://img.shields.io/badge/HTML5-Frontend-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-Styling-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)

<br/>

> A smart, rule-based web application that delivers **personalized diet and exercise recommendations** based on individual health parameters including BMI, hydration levels, and lifestyle habits.

</div>

---


## About the Project

The **Smart Fitness & Diet Planner** is a Python-based web application designed to help users make better health decisions. By analyzing user-provided health parameters — such as age, weight, height, activity level, and hydration — the system generates customized diet plans and exercise routines using an intelligent rule-based engine.

Whether you're looking to lose weight, gain muscle, or simply maintain a healthy lifestyle, this planner gives you actionable, data-driven recommendations tailored specifically to you.

---

## Features

| Feature | Description |
|---|---|
| 🧮 **BMI Calculator** | Automatically calculates Body Mass Index from user inputs |
| 🥗 **Diet Recommendations** | Personalized meal plans based on health profile |
| 🏃 **Exercise Suggestions** | Custom workout routines matched to fitness level |
| 💧 **Hydration Tracking** | Hydration-aware recommendations |
| 👤 **User Profiles** | Secure registration and login system |
| 🔐 **Admin Dashboard** | Admin panel to manage users and data |
| 📊 **Rule-Based Engine** | Intelligent logic for accurate, consistent recommendations |
| 📱 **Responsive UI** | Clean, accessible interface built with HTML & CSS |

---

## Tech Stack

```
Frontend   →  HTML5, CSS3
Backend    →  Python, Flask
Database   →  SQLite (diet.db)
Logic      →  Rule-Based Recommendation Engine
```

---

## Project Structure

```
Smart-Fitness-Diet-Planner-Python-Project/
│
├── app.py                  # Main Flask application & route handlers
├── database.py             # Database models and helper functions
├── diet.db                 # SQLite database file
├── diet.sqbpro             # DB Browser project file
├── Admin credential.txt    # Default admin login credentials
├── SDFP.pdf                # Project documentation / report
│
├── templates/              # HTML templates (Jinja2)
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── results.html
│   └── admin.html
│
└── static/                 # Static assets
    ├── css/
    └── images/
```

---

## How It Works

```
User Input
    │
    ▼
┌─────────────────────────┐
│  Health Parameters      │
│  • Age, Gender          │
│  • Weight, Height       │
│  • Activity Level       │
│  • Hydration Level      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Rule-Based Engine     │
│  • BMI Classification   │
│  • Caloric Needs Calc   │
│  • Lifestyle Analysis   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Personalized Output   │
│  ✅ Diet Plan           │
│  ✅ Exercise Routine    │
│  ✅ Hydration Goals     │
└─────────────────────────┘
```

---

## Getting Started

### Prerequisites

Make sure you have **Python 3.8+** installed on your system.

```bash
python --version
```

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/varunshetty1893/Smart-Fitness-Diet-Planner-Python-Project.git
cd Smart-Fitness-Diet-Planner-Python-Project
```

**2. Create and activate a virtual environment** *(recommended)*
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install flask
```

**4. Initialize the database**
```bash
python database.py
```

**5. Run the application**
```bash
python app.py
```

**6. Open in your browser**
```
http://127.0.0.1:5000
```

---

## Admin Access

Default admin credentials are provided in `Admin credential.txt` in the project root.

> ⚠️ **Security Note:** Change the default admin password before deploying to production.

---

## Screenshots

> *(Add screenshots of your app here by uploading images to the repo and referencing them below)*

```markdown
![Home Page](static/screenshots/home.png)
![Dashboard](static/screenshots/dashboard.png)
![Results](static/screenshots/results.png)
```

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes and **commit**: `git commit -m "Add: your feature description"`
4. **Push** to your fork: `git push origin feature/your-feature-name`
5. Open a **Pull Request**

---

## License

This project is open-source and available for educational and personal use. See the project for more details.

---

<div align="center">

Made with ❤️ by [Varun Shetty](https://github.com/varunshetty1893)

⭐ **Star this repo if you found it helpful!** ⭐

</div>
