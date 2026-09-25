<div align="center">

# 🏋️‍♂️ Personalized Fitness & Weight Management Coach

### An empathetic, agent-first AI health coach built with Google ADK, Gemini, Firestore, and A2UI.

![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Agent%20Platform-4285F4?logo=googlecloud&logoColor=white)
![Gemini](https://img.shields.io/badge/Model-Gemini%203.6%20Flash-8E75B2)
![ADK](https://img.shields.io/badge/Built%20with-ADK%20%2B%20agents--cli-34A853)
![A2UI](https://img.shields.io/badge/UI-A2UI%20Cards-EA4335)
![Firestore](https://img.shields.io/badge/Database-Cloud%20Firestore-FFCA28)

</div>

---

## 💡 What This App Does

The **Personalized Fitness & Weight Management Coach** is an interactive, compassionate AI agent designed to help users achieve and sustain their personal wellness goals without judgment or shame.

### Core Features

1. **Personalized Health Assessment & Tailored Plans**:
   - Calculates **BMI** from age, height, weight, and gender, automatically saving user profiles in **Google Cloud Firestore**.
   - **Underweight (BMI < 18.5)**: Suggests healthy, nutrient-dense weight gain options and resistance training to build lean muscle mass.
   - **Normal (BMI 18.5 – 24.9)**: Offers maintenance exercise routines focusing on mobility, core stability, and cardio endurance.
   - **Overweight (BMI 25.0 – 29.9)**: Generates structured **3-month or 6-month progressive routines** combining moderate cardio, strength training, and modest caloric deficit diets.
   - **High BMI (≥ 30.0)**: Provides compassionate, joint-friendly long-term progressions (low-impact walking, swimming) with gentle, sustainable dietary adjustments.

2. **Food Photo Calorie & Macro Tracking (`log_meal_photo`)**:
   - Users can upload or describe photos of meals they eat throughout the day.
   - The agent analyzes the meal, estimates total calories, protein, carbs, and fats, and saves each entry to Firestore under `users/{user_id}/meals`.

3. **Wearable Health Monitor Sync (`sync_health_device_data`)**:
   - Syncs daily activity metrics from fitness trackers (Apple Health, Fitbit, Garmin): active workout calories burned, daily steps, and workout duration alongside basal metabolic rate (BMR).

4. **9:00 PM Net Calorie Gain/Loss Report (`get_daily_calorie_summary`)**:
   - At the end of each day, the agent calculates the complete caloric balance:
     $$\text{Net Calories} = \text{Total Food Intake} - (\text{Resting BMR} + \text{Exercise Burn})$$
   - Renders a rich summary card displaying total intake, total burn, step count, and an encouraging verdict.

5. **A2UI Rich Card Rendering**:
   - Instead of walls of text, responses are rendered as clean, structured **A2UI Cards** with visual hierarchy (Headings, Stats, Breakdowns, and Action Plans).

---

## 🧩 Architecture

```
User (Browser / Mobile)
        │
        ▼
FastAPI Proxy (`frontend/main.py`)  <───>  A2UI Mini-Renderer (`static/index.html`)
        │ (A2A Protocol / SSE)
        ▼
Vertex AI Agent Runtime (`fitness-coach-agent`)
  ├── Model: Gemini 3.6 Flash
  ├── Callback: `a2ui_callback` (rewraps A2UI v0.8 cards)
  └── Tools:
        ├── `save_user_profile` ────────> Cloud Firestore (`users/{user_id}`)
        ├── `get_user_profile`
        ├── `log_meal_photo` ───────────> Cloud Firestore (`users/{user_id}/meals`)
        ├── `sync_health_device_data` ──> Cloud Firestore (`users/{user_id}/daily_activity`)
        └── `get_daily_calorie_summary`
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- `uv` and `agents-cli` installed
- Google Cloud project with Firestore Native enabled and authenticated via ADC (`gcloud auth application-default login`)

### 1. Run the Agent Locally (ADK Web Playground)

```bash
cd fitness-coach-agent
uv run adk web . --host 0.0.0.0 --port 8080 --allow_origins "*" --reload_agents
```

Open your browser to:
👉 `http://127.0.0.1:8080/dev-ui/?app=app`
*(Make sure **Token Streaming** is turned **OFF** in the gear settings).*

### 2. Run the Web Chat UI

```bash
cd frontend
python main.py
```

Open:
👉 `http://127.0.0.1:8081/`

---

## 🧪 Example Test Prompts

1. **Calculate BMI & Plan**:
   > *"Hi! My name is John. I am 32 years old, male, 175 cm tall, and weigh 88 kg. Can you give me a plan?"*

2. **Log Meal Photo**:
   > *"Here is a photo of my lunch: grilled chicken breast with avocado and a garden salad. Log this for user John."*

3. **Sync Wearable Data**:
   > *"Sync health monitor data for user John: 11,200 steps, 45 minutes workout, 520 exercise calories burned."*

4. **9 PM Net Calorie Digest**:
   > *"It is 9 PM now. Send user John his daily net calorie summary report."*

---

## 📄 License
Apache 2.0
