"""
Workout Plan Generator Core Engine
Handles prompt engineering, Groq API communication, input validation, and error handling.
"""

from __future__ import annotations

import os
from typing import List, Union, Optional
from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    APIStatusError,
)

# Load environment variables from .env file if available
load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")


class WorkoutGenerationError(Exception):
    """Custom exception raised for user-facing workout generation errors."""
    pass


def validate_inputs(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment_access: Union[List[str], str],
    session_duration: int = 45,
) -> None:
    """
    Validates user inputs before sending to the LLM.
    Raises WorkoutGenerationError with a friendly message if any input is invalid.
    """
    valid_goals = [
        "Build muscle",
        "Lose fat",
        "General fitness",
        "Improve endurance",
        "Strength & Power",
    ]
    valid_levels = ["Beginner", "Intermediate", "Advanced"]

    if not fitness_goal or fitness_goal.strip() == "":
        raise WorkoutGenerationError("Please select a fitness goal before generating your plan.")

    if not experience_level or experience_level.strip() == "":
        raise WorkoutGenerationError("Please select your experience level.")

    if days_per_week < 1 or days_per_week > 7:
        raise WorkoutGenerationError(
            f"Invalid training frequency: {days_per_week} days selected. Please choose between 1 and 7 days per week."
        )

    # Normalize equipment access
    if isinstance(equipment_access, str):
        eq_list = [equipment_access.strip()] if equipment_access.strip() else []
    else:
        eq_list = [e.strip() for e in equipment_access if e.strip()]

    if not eq_list:
        raise WorkoutGenerationError(
            "Please select at least one equipment option (e.g., 'No equipment', 'Home dumbbells', or 'Full gym')."
        )

    if session_duration < 15 or session_duration > 180:
        raise WorkoutGenerationError(
            f"Session duration ({session_duration} mins) is outside recommended range (15 to 180 mins)."
        )


def build_system_prompt() -> str:
    """
    Constructs an elite personal trainer system prompt enforcing strict constraints,
    structured output, and safe scoping.
    """
    return (
        "You are an elite, certified Strength and Conditioning Specialist (CSCS) and Personal Trainer. "
        "Your mission is to craft realistic, highly customized, and safe weekly workout programs tailored to each client's unique profile.\n\n"
        "STRICT OPERATIONAL DIRECTIVES:\n"
        "1. RESPECT CONSTRAINTS ABSOLUTELY:\n"
        "   - EQUIPMENT: NEVER prescribe an exercise that requires equipment the user does not possess. "
        "If 'No equipment', stick strictly to calisthenics/bodyweight. If 'Home dumbbells', only prescribe dumbbell and bodyweight movements.\n"
        "   - INJURIES & LIMITATIONS: Zero tolerance for contraindicated movements. If injuries are listed (e.g., bad knees, shoulder impingement, lower back pain), "
        "explicitly avoid aggravating exercises and select joint-friendly alternatives. Explain why the exercise choices protect that specific joint/area.\n"
        "   - DAYS/WEEK: You must provide a structured schedule matching EXACTLY the specified number of training days (1 to 7). Never give fewer or more days.\n\n"
        "2. OUTPUT STRUCTURE (NO WALLS OF TEXT):\n"
        "   - Program Summary: Split style, philosophy, and weekly cadence.\n"
        "   - Daily Breakdown (Day 1, Day 2, etc.): Include Focus/Muscles, Warm-up (3-5 min), Exercise Table/List (Exercise Name, Target Muscle, Sets, Reps/Tempo, Rest Seconds, Key Coaching Cue), and Cool-down.\n"
        "   - Rest/Recovery Days: Clearly specify which days are active recovery or rest.\n"
        "   - Progressive Overload Strategy: 2-3 specific bullet points on how to progress safely week-to-week based on their experience level.\n\n"
        "3. SAFETY & MEDICAL SCOPING:\n"
        "   - If any injuries or limitations are provided, include a clear safety disclaimer at the very beginning: "
        "'⚠️ Disclaimer: This workout plan is designed for general fitness and modified around your noted limitations. Consult with a qualified healthcare professional or physical therapist before beginning any new training regimen.'\n"
        "   - Make no medical diagnostic claims."
    )


def build_user_prompt(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment_access: Union[List[str], str],
    limitations: str = "",
    session_duration: int = 45,
    is_regeneration: bool = False,
    focus_preference: str = "",
) -> str:
    """
    Constructs a detailed user prompt passing all structured inputs into context.
    """
    if isinstance(equipment_access, list):
        equipment_str = ", ".join(equipment_access)
    else:
        equipment_str = equipment_access

    limitations_str = limitations.strip() if limitations and limitations.strip() else "None reported (healthy & cleared for exercise)"
    focus_str = f"\n- Additional Focus Preference: {focus_preference}" if focus_preference else ""
    variation_str = (
        "\n\nNOTE: This is a REGENERATION request. Please provide an alternative variation or fresh exercise selection / split concept while strictly keeping the same goal, equipment, and safety constraints."
        if is_regeneration
        else ""
    )

    return (
        f"Please design a personalized weekly workout plan for a client with the following profile:\n\n"
        f"CLIENT PROFILE:\n"
        f"- Primary Fitness Goal: {fitness_goal}\n"
        f"- Experience Level: {experience_level}\n"
        f"- Training Frequency: {days_per_week} days per week\n"
        f"- Available Equipment: {equipment_str}\n"
        f"- Session Time Target: ~{session_duration} minutes per workout\n"
        f"- Physical Limitations / Injuries: {limitations_str}"
        f"{focus_str}\n\n"
        f"REQUIREMENTS FOR THE PLAN:\n"
        f"1. Generate exactly {days_per_week} detailed training days.\n"
        f"2. Ensure each exercise utilizes ONLY: {equipment_str}.\n"
        f"3. Strictly accommodate physical limitations: {limitations_str}.\n"
        f"4. Format each day with: Warm-up, Structured Exercises (Sets x Reps + Rest + Form Tip), and Cool-down.\n"
        f"5. Include a Progressive Overload section suited for a {experience_level} lifter."
        f"{variation_str}"
    )


def generate_workout_plan(
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment_access: Union[List[str], str],
    limitations: str = "",
    session_duration: int = 45,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    is_regeneration: bool = False,
    focus_preference: str = "",
) -> str:
    """
    Generates a personalized weekly workout plan using Groq LLM API.

    Parameters:
        fitness_goal: Target goal ('Build muscle', 'Lose fat', etc.)
        experience_level: User fitness experience ('Beginner', 'Intermediate', 'Advanced')
        days_per_week: Number of training days per week (1-7)
        equipment_access: List or string of available equipment
        limitations: Free-text descriptions of injuries or physical limitations
        session_duration: Target duration in minutes per session
        api_key: Optional Groq API key (defaults to GROQ_API_KEY environment variable)
        model: Groq model identifier
        is_regeneration: Flag indicating if this is an alternative variation request
        focus_preference: Optional specific muscle or style focus

    Returns:
        A formatted markdown string containing the personalized workout plan.

    Raises:
        WorkoutGenerationError: On invalid input, API failure, or empty LLM output.
    """
    # Step 1: Input Validation
    validate_inputs(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment_access=equipment_access,
        session_duration=session_duration,
    )

    # Step 2: Resolve API Key
    effective_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_api_key or not effective_api_key.strip():
        raise WorkoutGenerationError(
            "Groq API Key is missing. Please provide a valid Groq API key in the sidebar or in a .env file."
        )

    # Step 3: Build Prompts
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment_access=equipment_access,
        limitations=limitations,
        session_duration=session_duration,
        is_regeneration=is_regeneration,
        focus_preference=focus_preference,
    )

    # Step 4: Execute API Call wrapped in try/except
    try:
        client = Groq(api_key=effective_api_key.strip())
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7 if not is_regeneration else 0.85,
            max_tokens=3500,
        )

        # Step 5: Check and validate response
        if not response or not response.choices:
            raise WorkoutGenerationError(
                "The AI service returned an empty response. Please try again."
            )

        content = response.choices[0].message.content
        if not content or not content.strip():
            # Fallback if reasoning consumed tokens or response was blank
            raise WorkoutGenerationError(
                "Received a blank response from the AI model. Please verify your model selection or try again."
            )

        return content.strip()

    except AuthenticationError as e:
        raise WorkoutGenerationError(
            "Authentication failed: The provided Groq API key is invalid or has expired. "
            "Please check your API key and try again."
        ) from e

    except RateLimitError as e:
        raise WorkoutGenerationError(
            "Rate limit reached on Groq API. Please wait a few moments and try again, or switch models."
        ) from e

    except APIConnectionError as e:
        raise WorkoutGenerationError(
            "Network connection failed: Unable to connect to Groq API. "
            "Please check your internet connection."
        ) from e

    except APIStatusError as e:
        raise WorkoutGenerationError(
            f"Groq API returned an error (Status {e.status_code}): {e.message}"
        ) from e

    except WorkoutGenerationError:
        # Re-raise already formatted errors
        raise

    except Exception as e:
        raise WorkoutGenerationError(
            f"An unexpected error occurred while generating your plan: {str(e)}"
        ) from e


def swap_exercise(
    current_exercise: str,
    reason_for_swap: str,
    fitness_goal: str,
    equipment_access: Union[List[str], str],
    limitations: str = "",
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Generates 2-3 tailored exercise alternatives to swap out an exercise,
    adhering strictly to available equipment and physical limitations.

    Parameters:
        current_exercise: Name of exercise to replace (e.g., 'Barbell Back Squat')
        reason_for_swap: Reason for swapping (e.g., 'Knee hurts', 'No spotter', 'Dislike exercise')
        fitness_goal: Target fitness goal
        equipment_access: Available equipment
        limitations: Known physical limitations/injuries
        api_key: Optional Groq API key
        model: Model identifier

    Returns:
        Formatted markdown containing 2-3 direct replacement alternatives with coaching notes.
    """
    if not current_exercise or not current_exercise.strip():
        raise WorkoutGenerationError("Please enter the name of the exercise you want to swap.")

    effective_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not effective_api_key or not effective_api_key.strip():
        raise WorkoutGenerationError("Groq API Key is missing. Please provide a valid Groq API key.")

    if isinstance(equipment_access, list):
        equipment_str = ", ".join(equipment_access)
    else:
        equipment_str = equipment_access

    system_prompt = (
        "You are an expert biomechanics specialist and fitness coach. "
        "The client wants to substitute a specific exercise from their workout plan. "
        "Provide 2-3 optimal direct replacement alternatives that target the exact same muscle group/movement pattern, "
        "strictly respecting their available equipment and injury limitations."
    )

    user_prompt = (
        f"Please provide 2-3 replacement alternatives for the following exercise:\n\n"
        f"- Exercise to Replace: {current_exercise.strip()}\n"
        f"- Reason for Swap: {reason_for_swap.strip() if reason_for_swap.strip() else 'Client preference / discomfort'}\n"
        f"- Client Goal: {fitness_goal}\n"
        f"- Available Equipment: {equipment_str}\n"
        f"- Physical Limitations / Injuries: {limitations if limitations else 'None'}\n\n"
        f"Format each alternative clearly with:\n"
        f"1. Alternative Exercise Name\n"
        f"2. Target Muscle / Movement Pattern\n"
        f"3. Recommended Sets & Reps\n"
        f"4. Why this is an ideal replacement given their equipment and reason for swapping."
    )

    try:
        client = Groq(api_key=effective_api_key.strip())
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        content = response.choices[0].message.content
        if not content or not content.strip():
            raise WorkoutGenerationError("Received empty response when finding exercise alternatives.")

        return content.strip()

    except Exception as e:
        raise WorkoutGenerationError(f"Failed to generate exercise replacement: {str(e)}") from e
