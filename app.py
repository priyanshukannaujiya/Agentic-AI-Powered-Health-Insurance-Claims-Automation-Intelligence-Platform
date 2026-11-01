"""
FitGenius - Personalized AI Workout Plan Generator
Single-page Streamlit application powered by Groq LLM.
Created for Codebasics AI Engineering Cohort.
"""

import os
import streamlit as st
from dotenv import load_dotenv

from generator import (
    generate_workout_plan,
    swap_exercise,
    WorkoutGenerationError,
    DEFAULT_MODEL,
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="FitGenius | AI Workout Plan Generator",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling and card designs
st.markdown(
    """
    <style>
    /* Global accents */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(120deg, #FF4B4B, #FF8533);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #8892B0;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .plan-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .badge-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        background-color: rgba(255, 75, 75, 0.15);
        color: #FF4B4B;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .tag-button {
        font-size: 0.8rem;
    }
    .stDownloadButton button {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 8px;
        color: #f9fafb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state variables
if "workout_plan" not in st.session_state:
    st.session_state.workout_plan = None
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = None
if "swap_result" not in st.session_state:
    st.session_state.swap_result = None
if "injuries_text" not in st.session_state:
    st.session_state.injuries_text = ""


# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ Groq API Settings")
    default_env_key = os.getenv("GROQ_API_KEY", "")
    api_key_input = st.text_input(
        "Groq API Key",
        value=default_env_key,
        type="password",
        help="Enter your Groq API key (starts with gsk_). Can also be set in .env as GROQ_API_KEY.",
    )

    available_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]
    selected_model = st.selectbox(
        "LLM Model",
        options=available_models,
        index=0,
        help="Select the Groq-hosted open-weights model for generation.",
    )

    if st.button("🔌 Test API Connection", use_container_width=True):
        if not api_key_input.strip():
            st.error("Please enter a Groq API Key first.")
        else:
            try:
                from groq import Groq

                client = Groq(api_key=api_key_input.strip())
                resp = client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": "Ping"}],
                    max_tokens=5,
                )
                st.success("✅ Connection successful!")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")



# Header Section
col_header_1, col_header_2 = st.columns([0.75, 0.25])
with col_header_1:
    st.markdown('<div class="main-title">🏋️ FitGenius: AI Workout Plan Generator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Design personalized, constraint-aware weekly workout plans engineered by an elite AI coach via the Groq API.</div>',
        unsafe_allow_html=True,
    )
with col_header_2:
    st.markdown(
        """
        <div style="text-align: right; padding-top: 10px;">
            <span class="badge-chip">⚡ Powered by Groq</span>
            <span class="badge-chip">🎯 Zero Fluff</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# Main Layout: 2 Columns (Left: User Inputs, Right: Plan & Controls)
col_input, col_output = st.columns([0.42, 0.58], gap="large")

with col_input:
    st.markdown("### 🎯 1. Your Fitness Profile")
    st.caption("Tell us about your goals, routine, and any physical considerations.")

    # Input 1: Fitness Goal (Dropdown)
    fitness_goal = st.selectbox(
        "Primary Fitness Goal *",
        options=[
            "Build muscle",
            "Lose fat",
            "General fitness",
            "Improve endurance",
            "Strength & Power",
        ],
        index=0,
        help="What is your primary training target?",
    )

    # Input 2: Experience Level (Dropdown)
    experience_level = st.selectbox(
        "Experience Level *",
        options=["Beginner", "Intermediate", "Advanced"],
        index=0,
        help="Beginner (<1 yr consistent lifting), Intermediate (1-3 yrs), Advanced (3+ yrs)",
    )

    # Input 3: Days Available Per Week (Slider)
    days_per_week = st.slider(
        "Days Available Per Week *",
        min_value=1,
        max_value=7,
        value=3,
        step=1,
        help="How many days per week can you dedicate to working out?",
    )

    # Input 4: Equipment Access (Multiselect)
    equipment_options = [
        "No equipment (bodyweight only)",
        "Home dumbbells",
        "Full gym (barbells, machines, cables)",
        "Resistance bands",
        "Kettlebells",
        "Pull-up bar",
    ]
    equipment_access = st.multiselect(
        "Available Equipment *",
        options=equipment_options,
        default=["Home dumbbells"],
        help="Select all equipment you have access to. The generator will NEVER prescribe items outside this list.",
    )

    # Input 5: Session Duration
    session_duration = st.select_slider(
        "Target Session Duration (minutes)",
        options=[20, 30, 45, 60, 75, 90],
        value=45,
        help="Approximate length of each workout session.",
    )

    # Input 6: Optional Focus Preference
    focus_preference = st.text_input(
        "Specific Focus / Style (Optional)",
        placeholder="e.g. Core focus, Glute emphasis, Athletic conditioning",
        help="Optional special focus or training style you'd like highlighted.",
    )

    # Input 7: Injuries or Limitations (Free Text with Quick Helpers)
    st.markdown("**Injuries or Physical Limitations (Optional)**")
    st.caption("e.g. 'Bad knees - avoid deep squats', 'Rotator cuff discomfort', 'Lower back pain'")

    # Quick Tag buttons to assist users
    quick_tags = ["Bad knees", "Lower back pain", "Shoulder impingement", "No jumping / low impact"]
    st.markdown("<small>Quick add common limitations:</small>", unsafe_allow_html=True)
    tag_cols = st.columns(len(quick_tags))
    for i, tag in enumerate(quick_tags):
        with tag_cols[i]:
            if st.button(f"+ {tag}", key=f"quick_tag_{i}", use_container_width=True):
                if st.session_state.injuries_text:
                    if tag not in st.session_state.injuries_text:
                        st.session_state.injuries_text += f", {tag}"
                else:
                    st.session_state.injuries_text = tag

    limitations = st.text_area(
        label="Limitations input",
        label_visibility="collapsed",
        value=st.session_state.injuries_text,
        placeholder="Describe any injuries, joint pain, or movement restrictions...",
        height=85,
    )
    # Sync back to session state
    st.session_state.injuries_text = limitations

    st.markdown("<br>", unsafe_allow_html=True)

    # Action Buttons: Generate & Regenerate
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        generate_clicked = st.button("⚡ Generate Plan", type="primary", use_container_width=True)
    with btn_col2:
        regenerate_clicked = st.button(
            "🔄 Regenerate Variation",
            use_container_width=True,
            disabled=(st.session_state.workout_plan is None),
            help="Generates an alternative workout variation with the same constraints.",
        )


# Handling Plan Generation
if generate_clicked or regenerate_clicked:
    is_regeneration = regenerate_clicked

    with st.spinner("🤖 Consulting AI Coach and formulating tailored plan via Groq..."):
        try:
            # Snapshot inputs for state persistence and swap feature
            current_inputs = {
                "fitness_goal": fitness_goal,
                "experience_level": experience_level,
                "days_per_week": days_per_week,
                "equipment_access": equipment_access,
                "limitations": limitations,
                "session_duration": session_duration,
                "focus_preference": focus_preference,
            }

            plan_result = generate_workout_plan(
                fitness_goal=fitness_goal,
                experience_level=experience_level,
                days_per_week=days_per_week,
                equipment_access=equipment_access,
                limitations=limitations,
                session_duration=session_duration,
                api_key=api_key_input.strip() if api_key_input else None,
                model=selected_model,
                is_regeneration=is_regeneration,
                focus_preference=focus_preference,
            )

            # Store in session state for persistence across reruns (Stretch Goal 2)
            st.session_state.workout_plan = plan_result
            st.session_state.last_inputs = current_inputs
            st.session_state.swap_result = None  # Reset previous swaps
            st.toast("Workout plan generated successfully!", icon="✅")

        except WorkoutGenerationError as e:
            st.error(f"⚠️ {str(e)}")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")


# Output Section
with col_output:
    st.markdown("### 📋 2. Your Personalized Program")

    if st.session_state.workout_plan:
        # Summary Header Tags
        last_inputs = st.session_state.last_inputs or {}
        st.markdown(
            f"""
            <div style="margin-bottom: 15px;">
                <span class="badge-chip">🎯 {last_inputs.get('fitness_goal', fitness_goal)}</span>
                <span class="badge-chip">📈 {last_inputs.get('experience_level', experience_level)}</span>
                <span class="badge-chip">📅 {last_inputs.get('days_per_week', days_per_week)} Days/Wk</span>
                <span class="badge-chip">⏱️ ~{last_inputs.get('session_duration', session_duration)}m/session</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Download Buttons (Stretch Goal 3)
        dl_col1, dl_col2, _ = st.columns([0.35, 0.35, 0.3])
        with dl_col1:
            st.download_button(
                label="📥 Download (.md)",
                data=st.session_state.workout_plan,
                file_name="fitgenius_workout_plan.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                label="📄 Download (.txt)",
                data=st.session_state.workout_plan,
                file_name="fitgenius_workout_plan.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Plan Display
        st.markdown(st.session_state.workout_plan)

        st.markdown("---")

        # Stretch Goal 4: "Swap this exercise" mini-feature
        st.markdown("### 🔀 Need an Alternative? Swap an Exercise")
        st.caption(
            "Dislike an exercise or feeling joint pain? Replace it with smart alternatives matching your equipment & constraints."
        )

        with st.expander("🛠️ Open Exercise Swap Assistant", expanded=False):
            swap_col1, swap_col2 = st.columns([0.5, 0.5])
            with swap_col1:
                exercise_to_replace = st.text_input(
                    "Exercise to Replace",
                    placeholder="e.g. Barbell Back Squat, Push-up, Overhead Press",
                )
            with swap_col2:
                reason_for_swap = st.text_input(
                    "Reason for Swap",
                    placeholder="e.g. Knee pain, don't have barbell, want easier variation",
                )

            if st.button("🔍 Find 2-3 Alternatives", use_container_width=True):
                if not exercise_to_replace.strip():
                    st.warning("Please type the name of the exercise you want to swap.")
                else:
                    with st.spinner("Finding biomechanically sound alternatives..."):
                        try:
                            swap_output = swap_exercise(
                                current_exercise=exercise_to_replace,
                                reason_for_swap=reason_for_swap,
                                fitness_goal=last_inputs.get("fitness_goal", fitness_goal),
                                equipment_access=last_inputs.get("equipment_access", equipment_access),
                                limitations=last_inputs.get("limitations", limitations),
                                api_key=api_key_input.strip() if api_key_input else None,
                                model=selected_model,
                            )
                            st.session_state.swap_result = swap_output
                        except WorkoutGenerationError as err:
                            st.error(f"⚠️ {str(err)}")

            if st.session_state.swap_result:
                st.markdown("#### 💡 Recommended Substitutes:")
                st.markdown(st.session_state.swap_result)

    else:
        # Placeholder state before user generates
        st.info("👋 Welcome! Fill in your fitness parameters on the left and click **⚡ Generate Plan** to get your custom weekly workout schedule.")
        
        # Display sample feature preview
        st.markdown(
            """
            #### 🌟 What you'll receive:
            - **Custom Weekly Split**: Designed around your exact available days (1 to 7).
            - **Strict Equipment Matching**: Only uses the gear you own (No gym required if bodyweight or home dumbbells).
            - **Joint-Safe Programming**: Specific exercise substitutions and safety disclaimers for any injury or limitation.
            - **Structured Breakdown**: Exercises, target muscles, sets, reps, rest periods, and coaching cues.
            - **Progressive Overload Blueprint**: Systematic guide on how to progress week-over-week.
            """
        )
