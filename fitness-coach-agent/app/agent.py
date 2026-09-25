# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

import datetime
import os
from typing import Any
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.cloud import firestore
from google.genai import types

from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.6-flash"

# Lazy-loaded Firestore client
_db = None


def get_firestore_client() -> firestore.Client:
    global _db
    if _db is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-04-650a22785259")
        _db = firestore.Client(project=project_id)
    return _db


def save_user_profile(
    user_id: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    gender: str,
) -> dict[str, Any]:
    """Saves or updates user fitness information in Firestore and calculates BMI.

    Args:
        user_id: Unique identifier for the user (e.g. name or username).
        age: Age of the user in years.
        height_cm: Height of the user in centimeters.
        weight_kg: Weight of the user in kilograms.
        gender: Gender of the user (e.g., male, female, non-binary).

    Returns:
        A dictionary containing the saved profile, calculated BMI, and category.
    """
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m * height_m), 1)

    if bmi < 18.5:
        category = "underweight"
    elif 18.5 <= bmi < 25.0:
        category = "normal"
    elif 25.0 <= bmi < 30.0:
        category = "overweight"
    else:
        category = "high_overweight"

    profile_data = {
        "user_id": user_id,
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "gender": gender,
        "bmi": bmi,
        "category": category,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    try:
        db = get_firestore_client()
        db.collection("users").document(user_id).set(profile_data)
        profile_data["status"] = "saved_to_firestore"
    except Exception as e:
        profile_data["status"] = f"calculated_locally (firestore error: {e})"

    return profile_data


def get_user_profile(user_id: str) -> dict[str, Any]:
    """Retrieves user profile information from Firestore.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        The stored user profile or a message if not found.
    """
    try:
        db = get_firestore_client()
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict()
        return {"status": "not_found", "message": f"No profile found for user {user_id}."}
    except Exception as e:
        return {"status": "error", "message": f"Error accessing Firestore: {e}"}


def log_meal_photo(
    user_id: str,
    meal_description_or_image_url: str,
    estimated_calories: int,
    meal_type: str = "meal",
    protein_g: float = 0.0,
    carbs_g: float = 0.0,
    fats_g: float = 0.0,
) -> dict[str, Any]:
    """Logs a food photo/meal intake for a user into Firestore.

    Args:
        user_id: Unique identifier for the user.
        meal_description_or_image_url: Description of the food or image URL from the photo.
        estimated_calories: Estimated total calories contained in the meal.
        meal_type: Type of meal, e.g., 'breakfast', 'lunch', 'dinner', 'snack'.
        protein_g: Estimated protein in grams.
        carbs_g: Estimated carbohydrates in grams.
        fats_g: Estimated fats in grams.

    Returns:
        Confirmation dictionary with the logged meal data and Firestore status.
    """
    today_str = datetime.date.today().isoformat()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    meal_id = f"meal_{int(datetime.datetime.now().timestamp())}"

    meal_entry = {
        "meal_id": meal_id,
        "date": today_str,
        "timestamp": now_iso,
        "meal_type": meal_type,
        "description_or_url": meal_description_or_image_url,
        "calories": estimated_calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fats_g": fats_g,
    }

    try:
        db = get_firestore_client()
        db.collection("users").document(user_id).collection("meals").document(meal_id).set(meal_entry)
        meal_entry["status"] = "saved_to_firestore"
    except Exception as e:
        meal_entry["status"] = f"logged_locally (firestore error: {e})"

    return meal_entry


def sync_health_device_data(
    user_id: str,
    exercise_calories_burned: int,
    steps: int = 0,
    active_minutes: int = 0,
    resting_calories: int = 1800,
) -> dict[str, Any]:
    """Syncs health monitor wearable device data (e.g., Apple Watch, Fitbit, Garmin) for today.

    Args:
        user_id: Unique identifier for the user.
        exercise_calories_burned: Active calories burned from workouts and activity today.
        steps: Total steps recorded today.
        active_minutes: Total minutes of active physical exercise.
        resting_calories: Basal metabolic rate (BMR) resting calories burned today (default ~1800).

    Returns:
        The synced health activity record and status.
    """
    today_str = datetime.date.today().isoformat()
    activity_data = {
        "date": today_str,
        "exercise_calories_burned": exercise_calories_burned,
        "resting_calories": resting_calories,
        "total_calories_burned": exercise_calories_burned + resting_calories,
        "steps": steps,
        "active_minutes": active_minutes,
        "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    try:
        db = get_firestore_client()
        db.collection("users").document(user_id).collection("daily_activity").document(today_str).set(activity_data)
        activity_data["status"] = "saved_to_firestore"
    except Exception as e:
        activity_data["status"] = f"synced_locally (firestore error: {e})"

    return activity_data


def get_daily_calorie_summary(
    user_id: str,
    date_str: str = "",
) -> dict[str, Any]:
    """Calculates the end-of-day net calorie gain or loss (e.g. for 9 PM daily report).

    Formula: Net Calories = Total Calorie Intake - (Resting Calories + Exercise Burned Calories).

    Args:
        user_id: Unique identifier for the user.
        date_str: Target date formatted as YYYY-MM-DD. Defaults to today's date if empty.

    Returns:
        Dictionary summarizing total food intake, exercise burn, resting burn, and net caloric balance.
    """
    if not date_str:
        date_str = datetime.date.today().isoformat()

    total_intake = 0
    meals_list = []
    exercise_burned = 0
    resting_burned = 1800  # standard fallback BMR
    steps = 0
    active_minutes = 0

    try:
        db = get_firestore_client()
        # Query meals for the date
        meals_ref = db.collection("users").document(user_id).collection("meals").where("date", "==", date_str).stream()
        for m in meals_ref:
            data = m.to_dict()
            total_intake += data.get("calories", 0)
            meals_list.append(data)

        # Query activity for the date
        activity_doc = db.collection("users").document(user_id).collection("daily_activity").document(date_str).get()
        if activity_doc.exists:
            act_data = activity_doc.to_dict()
            exercise_burned = act_data.get("exercise_calories_burned", 0)
            resting_burned = act_data.get("resting_calories", 1800)
            steps = act_data.get("steps", 0)
            active_minutes = act_data.get("active_minutes", 0)
    except Exception as e:
        pass

    total_burned = resting_burned + exercise_burned
    net_calories = total_intake - total_burned

    if net_calories < -200:
        balance_verdict = f"Net Calorie Deficit of {abs(net_calories)} kcal (promotes healthy weight reduction)"
    elif net_calories > 200:
        balance_verdict = f"Net Calorie Surplus of {net_calories} kcal (promotes weight gain)"
    else:
        balance_verdict = f"Maintenance Balance (Net {net_calories:+d} kcal, stable weight maintenance)"

    return {
        "user_id": user_id,
        "date": date_str,
        "report_time": "9:00 PM Daily Digest",
        "total_food_intake_kcal": total_intake,
        "meals_logged_count": len(meals_list),
        "exercise_calories_burned_kcal": exercise_burned,
        "resting_calories_burned_kcal": resting_burned,
        "total_calories_burned_kcal": total_burned,
        "net_calorie_balance_kcal": net_calories,
        "steps": steps,
        "active_minutes": active_minutes,
        "verdict": balance_verdict,
    }


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

role_description = (
    "You are an encouraging, polite, and empathetic Personal Fitness and Weight Management Coach. "
    "Your mission is to help users reach their health goals respectfully and safely. "
    "Always maintain a positive, supportive, and respectful tone. Never shame, judge, or be rude about a user's weight or body size."
)

workflow_description = (
    "Workflow:\n"
    "1. When the user provides their details (age, height, weight, gender, and optionally a user identifier), "
    "call `save_user_profile` to store their profile in Firestore and calculate their BMI.\n"
    "2. If the user asks for their previous plan or profile, use `get_user_profile`.\n"
    "3. Tailor recommendations according to their BMI:\n"
    "   - BMI < 18.5 (Underweight): Politely encourage healthy weight gain. Suggest nutrient-dense foods (healthy fats, complex carbs, lean protein) and strength training to build lean muscle mass.\n"
    "   - BMI 18.5 - 24.9 (Normal): Congratulate them. Provide exercise routines to maintain current weight, improve cardiovascular health, mobility, and core strength, paired with a balanced maintenance diet.\n"
    "   - BMI 25.0 - 29.9 (Overweight): Provide a structured 3-month or 6-month exercise routine with progressive moderate-intensity cardio, strength training, and a sustainable modest caloric deficit diet plan.\n"
    "   - BMI >= 30.0 (High): Provide a compassionate, safe 6-month to 12-month long-term progression focusing on low-impact exercise (walking, swimming, resistance bands) to protect joints.\n"
    "4. When the user shares or uploads photos of food/meals: analyze the items, estimate portions and calories, and call `log_meal_photo`.\n"
    "5. When the user shares wearable health device data (steps, exercise calories burned, active minutes): call `sync_health_device_data`.\n"
    "6. At the end of the day or when asked for the 9 PM summary: call `get_daily_calorie_summary` to compute Net Calories = Total Food Intake - (Resting + Exercise Burn) and present a clear, polite summary.\n"
    "7. Format outputs in clean, structured A2UI cards (Card > Column > Text rows) highlighting stats, advice, and encouraging insights."
)

ui_description = (
    "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
    "Never nest a Card inside a Card. "
    "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
    "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
    "nothing in adk web). "
    "You may include one Image component, but only when you have a public https "
    "URL for the image. Otherwise, use Text rows. "
    "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
    "headings and emphasis. "
    "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
    "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
)

instruction = schema_manager.generate_system_prompt(
    role_description=role_description,
    workflow_description=workflow_description,
    ui_description=ui_description,
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        save_user_profile,
        get_user_profile,
        log_meal_photo,
        sync_health_device_data,
        get_daily_calorie_summary,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
