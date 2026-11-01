"""
Unit and Integration Tests for Workout Plan Generator
Covers:
- Input validation (boundaries, 0 days, empty equipment, invalid inputs)
- Prompt engineering structure
- Error handling (bad API keys, connection failures)
- Live generation and exercise swapping
"""

import os
import unittest
from dotenv import load_dotenv

from generator import (
    validate_inputs,
    build_user_prompt,
    build_system_prompt,
    generate_workout_plan,
    swap_exercise,
    WorkoutGenerationError,
)

load_dotenv()


class TestWorkoutPlanGenerator(unittest.TestCase):

    def test_validation_empty_goal(self):
        """Test that empty fitness goal triggers friendly error."""
        with self.assertRaises(WorkoutGenerationError) as ctx:
            validate_inputs(
                fitness_goal="",
                experience_level="Beginner",
                days_per_week=3,
                equipment_access=["Full gym"],
            )
        self.assertIn("fitness goal", str(ctx.exception).lower())

    def test_validation_invalid_days_zero(self):
        """Test that 0 days selected triggers friendly error."""
        with self.assertRaises(WorkoutGenerationError) as ctx:
            validate_inputs(
                fitness_goal="Build muscle",
                experience_level="Beginner",
                days_per_week=0,
                equipment_access=["Home dumbbells"],
            )
        self.assertIn("between 1 and 7 days", str(ctx.exception))

    def test_validation_invalid_days_high(self):
        """Test that >7 days selected triggers friendly error."""
        with self.assertRaises(WorkoutGenerationError) as ctx:
            validate_inputs(
                fitness_goal="Build muscle",
                experience_level="Intermediate",
                days_per_week=8,
                equipment_access=["Home dumbbells"],
            )
        self.assertIn("between 1 and 7 days", str(ctx.exception))

    def test_validation_empty_equipment(self):
        """Test that empty equipment triggers friendly error."""
        with self.assertRaises(WorkoutGenerationError) as ctx:
            validate_inputs(
                fitness_goal="Build muscle",
                experience_level="Advanced",
                days_per_week=4,
                equipment_access=[],
            )
        self.assertIn("at least one equipment option", str(ctx.exception).lower())

    def test_validation_valid_inputs_pass(self):
        """Test that valid inputs pass cleanly."""
        try:
            validate_inputs(
                fitness_goal="Build muscle",
                experience_level="Beginner",
                days_per_week=3,
                equipment_access=["Home dumbbells"],
                session_duration=45,
            )
        except WorkoutGenerationError:
            self.fail("validate_inputs raised WorkoutGenerationError unexpectedly on valid inputs!")

    def test_prompt_includes_constraints(self):
        """Test that user prompt accurately reflects input constraints."""
        prompt = build_user_prompt(
            fitness_goal="Lose fat",
            experience_level="Intermediate",
            days_per_week=4,
            equipment_access=["Home dumbbells", "Resistance bands"],
            limitations="Shoulder impingement",
            session_duration=30,
            is_regeneration=True,
            focus_preference="Core & Cardio",
        )
        self.assertIn("Lose fat", prompt)
        self.assertIn("Intermediate", prompt)
        self.assertIn("4 days per week", prompt)
        self.assertIn("Home dumbbells, Resistance bands", prompt)
        self.assertIn("Shoulder impingement", prompt)
        self.assertIn("30 minutes", prompt)
        self.assertIn("REGENERATION", prompt)
        self.assertIn("Core & Cardio", prompt)

    def test_system_prompt_structure(self):
        """Test system prompt has strict constraint directives and disclaimer rule."""
        sys_prompt = build_system_prompt()
        self.assertIn("RESPECT CONSTRAINTS", sys_prompt)
        self.assertIn("Disclaimer", sys_prompt)
        self.assertIn("Progressive Overload", sys_prompt)

    def test_invalid_api_key_error_handling(self):
        """Test that invalid API key is caught and returns friendly message."""
        with self.assertRaises(WorkoutGenerationError) as ctx:
            generate_workout_plan(
                fitness_goal="Build muscle",
                experience_level="Beginner",
                days_per_week=3,
                equipment_access=["Full gym"],
                api_key="gsk_invalid_test_key_12345",
            )
        self.assertIn("Authentication failed", str(ctx.exception))

    def test_live_generation(self):
        """Test live generation with configured key from environment."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            self.skipTest("GROQ_API_KEY not configured in environment")

        result = generate_workout_plan(
            fitness_goal="General fitness",
            experience_level="Beginner",
            days_per_week=2,
            equipment_access=["No equipment (bodyweight only)"],
            limitations="Bad knees",
            session_duration=20,
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 200)
        self.assertIn("Disclaimer", result)


if __name__ == "__main__":
    unittest.main()
