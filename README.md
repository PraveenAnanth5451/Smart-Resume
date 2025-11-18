# 🚀 Smart Resume Analyzer

An AI-powered resume analysis and interview preparation platform built using **Flask**, **Gemini AI**, and a custom rule-based evaluation engine.
Upload your resume → Get instant ATS scoring, insights, interview questions, and a personalized career roadmap.

---
## 🎥 Demo Video
🔗 Watch the full demo here:  
https://drive.google.com/file/d/1hcna8PehQjGJalaHGC7mTi8FMlhzffdt/view?usp=sharing

## 📌 Key Features

### ✅ **1. Resume Upload & Text Extraction**

* Supports **PDF, DOCX, TXT** (based on your parser).
* Auto-cleans, extracts text, and validates quality.

### ✅ **2. AI-Powered Resume Analysis (Gemini)**

* ATS Score
* Keyword Match
* Format Quality
* Grammar & Clarity
* Content Strength
* Detailed strengths, weaknesses & improvement suggestions

### ✅ **3. Interview Question Generator**

Includes:

* 🔹 **Dynamic Technical Questions** (from Gemini AI)
* 🔹 **Behavioral Questions** (static curated list)
* 🔹 **Situational Questions** (static curated list)

Each question includes:

* Difficulty level
* Sample answers
* Type (technical / behavioral / situational)

### ✅ **4. Personalized Career Roadmap**

Generated using Gemini:

* Skill gaps
* Recommended certifications
* Technical growth path
* Suggested projects
* Resources

### ✅ **5. Dashboard**

Tracks:

* Resume uploads
* Analysis history
* Career roadmap
* Progress score (calculated from overall resume score)

---

## 🏗️ Project Structure

```
smart-resume/
│
├── app.py
├── services/
│   ├── parser.py          # Extract text from resumes
│   ├── ai.py              # Gemini AI service
│
├── storage.py             # In-memory database
│
├── templates/
│   ├── home.html
│   ├── upload.html
│   ├── analysis.html
│   ├── interview.html
│   ├── roadmap.html
│
└── uploads/               # Temporary upload directory
```

---

## 🧠 How the System Works

### 🔹 Step 1: User uploads a resume

Backend:

* Saves file temporarily
* Extracts text using `extract_text_from_file()`
* Deletes uploaded file to keep environment clean

### 🔹 Step 2: Resume is stored

Stored with:

* filename
* extracted text
* userId

### 🔹 Step 3: AI Analysis via Gemini

Your `generate_all_content_parallel()` returns:

```json
{
  "analysis": { ... },
  "technical_questions": [ ... ],
  "roadmap": { ... }
}
```

### 🔹 Step 4: Storage

* `analysis` → stored in `storage.analyses`
* `questions` → merged (technical + behavioral + situational)
* `roadmap` → stored in `storage.roadmaps`
* progress updated via `storage.bump_progress()`

---

## 🔥 API Endpoints

### **Upload Resume**

```
POST /api/resumes/upload
```

Response includes:

* ATS analysis
* Interview questions
* Roadmap
* Resume record

---

### **Get Dashboard**

```
GET /api/dashboard
```

### **Get Analysis**

```
GET /api/analysis/<resume_id>
```

### **Get Interview Questions**

```
GET /api/interview/<resume_id>
```

### **Get Roadmap**

```
GET /api/roadmap/<resume_id>
```

### **Get All Resumes**

```
GET /api/resumes
```

---

## 🧰 Tech Stack

| Component      | Technology                                   |
| -------------- | -------------------------------------------- |
| Backend        | **Flask**, Python                            |
| AI Model       | **Gemini API** (parallel content generation) |
| Resume Parsing | PyPDF2 / docx / custom parser                |
| Storage        | In-memory database (`Storage.py`)            |
| Frontend       | HTML, CSS, JS (Jinja templates)              |

---

## 🛠️ Installation

### Clone the repo

```bash
git clone https://github.com/yourusername/smart-resume.git
cd smart-resume
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set your environment variables

```
GEMINI_API_KEY=your_api_key_here
```

### Run the server

```bash
python app.py
```

Server runs at:

```
http://localhost:5000
```

---

## 👨‍💻 Folder: `services/ai.py`

This should contain functions like:

* `get_client()`
* `generate_all_content_parallel(text)`

Make sure the function returns:

* `analysis`
* `technical_questions`
* `roadmap`

---

## 📦 Storage System

The `Storage` class acts as a simple in-memory database for:

* Resumes
* Analyses
* Interview Questions
* Roadmaps
* Progress Tracking

---

## 🧪 Example Output (Simplified)

### ATS Summary

```
ATS Score: 82  
Keyword Match: 74  
Format Quality: 88  
Grammar & Style: 85  
Content Strength: 79  
```

### Interview Questions

* What is the time complexity of binary search?
* Describe a time you handled conflict in a team.
* How would you handle a production-level security vulnerability?

---

## 📌 Future Enhancements

* Chat-based resume improvement suggestions (LLM)
* Multi-user authentication
* PDF resume export with improvements
* Voice-based interview simulation
* Storage migration → PostgreSQL/MongoDB
