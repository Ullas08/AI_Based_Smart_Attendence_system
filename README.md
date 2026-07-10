# AI-Based Smart Attendance System

> **Production-ready AI-powered attendance system using real-time facial recognition**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16-orange.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-red.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue.svg)

---

## 📋 Features

- **Real-time Facial Recognition** — OpenCV Haar Cascade + TensorFlow CNN
- **Admin Dashboard** — Stats, charts, quick actions
- **Student Management** — Add/Edit/Delete with face dataset capture
- **Webcam Face Capture** — 30–100 images with live auto-capture
- **CNN Model Training** — 3-block ConvNet with data augmentation, early stopping
- **Attendance Tracking** — Once per day, duplicate prevention
- **Search & Filter** — By date, student, department
- **Export Reports** — Excel (.xlsx), CSV, PDF
- **Dark/Light Mode** — Persistent theme preference
- **Responsive UI** — Desktop, tablet, mobile friendly
- **Security** — bcrypt password hashing, session auth, parameterized SQL queries

---

## 🏗️ Project Structure

```
AI-Based Smart Attendence/
├── app.py                    # Flask application entry point
├── config.py                 # Configuration & environment
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── README.md
│
├── models/
│   └── train_model.py        # CNN training pipeline
│
├── utils/
│   ├── db.py                 # Database utilities
│   ├── face_capture.py       # Webcam face capture
│   ├── face_recognition_engine.py  # Recognition logic
│   └── export_utils.py       # Excel/CSV/PDF export
│
├── routes/
│   ├── auth.py               # Login/logout
│   ├── dashboard.py          # Dashboard
│   ├── students.py           # Student CRUD
│   ├── attendance.py         # Attendance records
│   ├── recognition.py        # Live recognition + training
│   └── reports.py            # Export reports
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html
│   ├── student_add.html
│   ├── student_edit.html
│   ├── capture.html
│   ├── recognition.html
│   ├── attendance.html
│   ├── reports.html
│   ├── 404.html
│   └── 500.html
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
├── dataset/                  # Auto-created: student face images
│   └── {student_id}/         # Per-student folder
│       ├── 0001.jpg
│       └── ...
│
└── trained_models/           # Auto-created: saved models
    ├── face_model.h5
    ├── label_map.npy
    └── training_history.json
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Webcam
- Windows 10/11 or Linux

### Windows Installation

```powershell
# 1. Navigate to project folder
cd "AI-Based Smart Attendence"

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional — defaults work out of the box)
copy .env.example .env
# Edit .env to change admin password, camera index, etc.

# 5. Run the application
python app.py
```

### Linux / macOS Installation

```bash
cd "AI-Based Smart Attendence"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Access the App

Open browser at: **http://127.0.0.1:5000**

Default login:
- **Username:** `admin`
- **Password:** `Admin@123`

> ⚠️ Change the admin password in `.env` for production use!

---

## 📖 Usage Guide

### 1. Add Students
1. Go to **Students → Add Student**
2. Fill in Student ID, Name, Department, Semester, Email, Phone
3. Click **Add & Capture Face**

### 2. Capture Face Images
1. On the capture page, click **Start Camera**
2. Click **Start Capturing** — auto-captures every 400ms
3. Capture at least **30 images** (100 recommended)
4. Vary your head angle and expressions for best accuracy

### 3. Train the Model
1. After capturing faces, click **Start Training**
2. Training runs in background (may take 2–10 minutes)
3. Model is automatically saved to `trained_models/`

### 4. Start Attendance
1. Go to **Live Recognition**
2. Click **Start** to begin MJPEG video stream
3. System auto-detects and recognizes faces
4. Attendance is marked once per student per day

### 5. View & Export Reports
1. Go to **Attendance** to view/filter records
2. Go to **Reports** to download Excel, CSV, or PDF

---

## 🤖 AI Architecture

### Face Detection
- **OpenCV Haar Cascade** (`haarcascade_frontalface_default.xml`)
- Parameters: scaleFactor=1.1, minNeighbors=5, minSize=(60,60)

### CNN Model Architecture
```
Input (128×128×3)
  ↓ Conv2D(32) + BatchNorm + MaxPool + Dropout(0.25)
  ↓ Conv2D(64) + BatchNorm + MaxPool + Dropout(0.25)
  ↓ Conv2D(128) + BatchNorm + MaxPool + Dropout(0.25)
  ↓ GlobalAveragePooling2D
  ↓ Dense(256) + BatchNorm + Dropout(0.5)
  ↓ Softmax(num_students)
```

### Training Settings
- **Optimizer:** Adam (lr=1e-3)
- **Loss:** Categorical Crossentropy
- **Augmentation:** rotation ±20°, zoom 15%, flip, brightness
- **Callbacks:** EarlyStopping (patience=8), ReduceLROnPlateau, ModelCheckpoint
- **Validation split:** 20%

### Recognition
- Confidence threshold: **75%** (configurable in `.env`)
- Faces below threshold → labeled "Unknown"
- Multi-face support per frame

---

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| Password Hashing | bcrypt |
| Session Auth | Flask sessions |
| SQL Injection | Parameterized queries only |
| Input Validation | Server-side validation on all forms |
| XSS Protection | Jinja2 auto-escaping |
| File Upload | Type checking, size limits |

---

## ⚙️ Configuration

Edit `.env` file:

```env
SECRET_KEY=your-production-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123
CONFIDENCE_THRESHOLD=0.75
MIN_FACE_IMAGES=30
MAX_FACE_IMAGES=100
IMAGE_SIZE=128
CAMERA_INDEX=0
```

---

## 📊 Database Schema

### Students Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| student_id | TEXT UNIQUE | e.g., CS2024001 |
| name | TEXT | Full name |
| department | TEXT | Department name |
| semester | TEXT | 1–8 |
| email | TEXT | Optional |
| phone | TEXT | Optional |
| face_trained | INTEGER | 0/1 flag |
| created_at | DATETIME | Registration time |

### Attendance Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| student_id | TEXT | FK → students |
| student_name | TEXT | Cached name |
| department | TEXT | Cached dept |
| date | TEXT | YYYY-MM-DD |
| time | TEXT | HH:MM:SS |
| confidence | REAL | CNN confidence 0–1 |
| status | TEXT | Present |

### Admins Table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| username | TEXT UNIQUE | Admin username |
| password_hash | TEXT | bcrypt hash |
| role | TEXT | admin |

---

## 🐛 Troubleshooting

**Camera not working?**
- Check `CAMERA_INDEX` in `.env` (try 0, 1, 2)
- Ensure no other application is using the camera
- Windows: Check Camera privacy settings

**Model not training?**
- Ensure at least 1 student has ≥30 captured images
- Check `dataset/` folder structure
- TensorFlow GPU: Install `tensorflow-gpu` for faster training

**Poor recognition accuracy?**
- Capture more images (aim for 80–100)
- Ensure good lighting during capture
- Capture at same location as recognition
- Retrain after adding new students

**ImportError on startup?**
```powershell
pip install -r requirements.txt --upgrade
```

---

## 📦 Deployment (Production)

### Windows (with Waitress)
```powershell
pip install waitress
waitress-serve --port=5000 app:app
```

### Linux (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📄 License

MIT License — Free for educational and commercial use.

---

## 🙏 Acknowledgments

- TensorFlow / Keras — Deep learning framework
- OpenCV — Computer vision library
- Flask — Web framework
- Bootstrap 5 — UI components
- Chart.js — Analytics charts
