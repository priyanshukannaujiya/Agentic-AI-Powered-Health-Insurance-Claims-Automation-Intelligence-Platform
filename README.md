# 🏋️‍♂️ FitGenius: AI Workout Plan Generator

> **Codebasics AI Engineering Cohort — Assignment 1**  
> An intelligent, single-page Streamlit application that collects structured fitness inputs and generates personalized, constraint-aware workout routines using open-weights LLMs via the **Groq API**.

---

## 🌟 Overview & Key Highlights

This application moves far beyond generic "do some pushups" responses by acting like an **elite CSCS-certified personal trainer**. It enforces strict biomechanical constraints, accommodates injuries, respects equipment boundaries, and formats workouts cleanly into structured day-by-day routines with progressive overload guidelines.

### 🎯 Rubric Coverage

| Criteria | Assignment Requirement | Implementation Details |
| :--- | :--- | :--- |
| **Crash-Proof Input Validation** (20%) | App runs without crashing on empty or invalid input | Input validation for 0 days, >7 days, missing goal/experience, empty equipment, with user-friendly alerts. |
| **Structured Inputs** (25%) | Inputs are structured (not just free text) and correctly passed | Dropdowns (Goal, Level), Slider (1–7 days), Multiselect (Equipment), Duration slider, Quick-add limitation pills, Focus style. |
| **Prompt Design & Constraints** (30%) | Respects constraints, well-structured, genuinely usable | Strict persona instructions, joint-friendly substitutions, explicit days mapping, markdown tables with sets/reps/tempo/cues, and safety disclaimers. |
| **Error Handling** (15%) | API failure, network issue, bad key, rate limit, empty output | Wrapped in comprehensive `try/except` catching `AuthenticationError`, `RateLimitError`, `APIConnectionError`, and blank responses. |
| **Code Quality** (10%) | Type hints, function separation, readability | Clean modular separation (`generator.py` and `app.py`), full PEP 484 type annotations, unit tests (`test_generator.py`). |

---

## 🚀 Stretch Goals Implemented

- [x] **🔄 Regenerate Variation**: Instantly generate an alternative routine variation matching the same constraints.
- [x] **💾 Session State Persistence**: Generated workouts persist across UI reruns using `st.session_state`.
- [x] **📥 Plan Export / Download**: One-click download as either Markdown (`.md`) or plain text (`.txt`).
- [x] **🔀 "Swap this exercise" Assistant**: Interactive tool to swap any exercise from your plan with 2–3 biomechanically sound substitutes tailored to your gear and limitations.

---

## 🧠 The Core Learning Goal: Prompt Design Philosophy

Rather than blindly concatenating user inputs into a prompt, our prompt engineering architecture utilizes a two-tier system:

1. **System Prompt Directives (`build_system_prompt`)**:
   - **Constraint Enforcement**: Absolute boundary on equipment. If "Home dumbbells" is selected, the model is strictly forbidden from prescribing barbells or cable pulleys.
   - **Joint & Injury Contraindications**: Prohibits contraindicated movements (e.g., knee pain eliminates high-impact jumping and deep back squats; substitutes bodyweight step-ups or glute bridges).
   - **Structured Markdown Tables**: Mandates Day-by-Day schedule with Warm-up, Exercise, Target Muscle, Sets, Reps, Rest, and Form Coaching Cues.
   - **Safety Scoping**: Automatically prepends a non-medical disclaimer when injuries or physical limitations are supplied.

2. **User Context Injection (`build_user_prompt`)**:
   - Structured mapping of all parameters into clear sections.
   - Linear/Double progressive overload strategies tailored to the user's experience level (`Beginner` vs `Intermediate` vs `Advanced`).

---

## 📦 Project Architecture

```
CodebasicsAssign 1/
│
├── app.py                 # Streamlit UI, interaction state, reactive layout
├── generator.py           # Core logic: Prompt design, validation, Groq API call, type hints
├── test_generator.py      # Unit & integration test suite (9 test cases)
├── requirements.txt       # Project dependencies (streamlit, groq, python-dotenv)
├── .env.example           # Configuration template
├── .gitignore             # Git ignore rules protecting API keys
└── README.md              # Project documentation
```

---

## 🛠️ Quickstart Guide

### 1. Clone the Repository
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd "CodebasicsAssign 1"
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your Groq API Key
Copy `.env.example` to `.env` and add your Groq API key:
```env
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```
*(You can also input your API key directly inside the app's sidebar).*

### 5. Run the Application
```bash
streamlit run app.py
```
The app will open automatically at `http://localhost:8501`.

### 6. Run Unit Tests
```bash
python -m unittest test_generator.py
```

---

## 📋 Example Plan Output

```markdown
⚠️ Disclaimer: This workout plan is designed for general fitness and modified around your noted limitations. Consult with a qualified healthcare professional or physical therapist before beginning any new training regimen.

### Program Overview: 3-Day Home Dumbbell Hypertrophy
- Frequency: 3 Days / Week (Full Body Split)
- Equipment: Home Dumbbells & Bodyweight
- Safety Focus: Knee-sparing quad & posterior chain selection

#### Day 1: Full Body A (Joint-Friendly Emphasis)
Warm-up: 5 mins dynamic mobility (arm circles, cat-cow, bodyweight hinges)

| Exercise | Target Muscles | Sets | Reps | Rest | Form Cue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Dumbbell Romanian Deadlift | Hamstrings, Glutes | 3 | 10-12 | 90s | Hinge at hips, soft knees, keep dumbbells close to shins |
| Dumbbell Floor Press | Chest, Triceps | 3 | 8-10 | 90s | Elbows at 45 degrees, pause lightly on floor |
| Supported Dumbbell Row | Lats, Upper Back | 3 | 10-12 | 60s | Pull elbows toward hip crease |
| Glute Bridges (Bodyweight) | Glutes, Lower Back | 3 | 15 | 60s | Drive through heels, squeeze glutes at apex |
...
```

---

## 🧪 Submission Checklist

- [x] Public GitHub repository with clean history
- [x] Zero hardcoded secrets in source code (`.gitignore` configured)
- [x] Streamlit app with single-page layout
- [x] Groq API integration with friendly error handling
- [x] All 4 stretch goals implemented & verified
