"""AI Assistant Page.

Conversational multi-agent interface powered by Llama 3.3 70B via Groq.
Supports portfolio intelligence, claim explanations, and multi-agent attribution.
"""

from __future__ import annotations

import uuid
import streamlit as st

from api_client import send_chat_message

st.title("🤖 AI Claims Assistant")
st.caption("Interactive multi-agent Copilot for claims intelligence, anomaly detection, and portfolio synthesis.")

# ── Session State Initialization ──────────────────────────────
if "chat_thread_id" not in st.session_state:
    st.session_state["chat_thread_id"] = str(uuid.uuid4())

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I am your Claims Intelligence Assistant. "
                "I can help you analyze batch-processed claims data, investigate risk signals, summarize portfolio trends, "
                "or inspect specific providers.\n\n"
                "*Data Source: Ingested via scheduled Azure Data Factory batch pipelines into Databricks Gold tables.*"
            ),
            "agents_used": ["Claims Analyst Agent"],
        }
    ]

# ── Sidebar Quick Prompts & Controls ──────────────────────────
with st.sidebar:
    st.markdown("#### 💡 Suggested Questions")
    examples = [
        "Give a short executive summary of the claims portfolio",
        "Summarize Claim #18874",
        "What are the top 5 states by claim volume?",
        "Explain the high-risk signals in claim anomalies",
        "How does provider type influence average claim amount?",
    ]

    for ex in examples:
        if st.button(ex, key=f"btn_ex_{ex[:20]}", use_container_width=True):
            st.session_state["queued_prompt"] = ex

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state["chat_messages"] = []
        st.session_state["chat_thread_id"] = str(uuid.uuid4())
        st.rerun()

# ── Render Message History ────────────────────────────────────
for msg in st.session_state["chat_messages"]:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    with st.chat_message(role):
        st.markdown(content)
        agents = msg.get("agents_used", [])
        if role == "assistant" and agents:
            st.caption(f"🧠 Agents used: {', '.join(agents)}")

# ── Chat Input & Dispatcher ───────────────────────────────────
queued = st.session_state.pop("queued_prompt", None)
user_prompt = st.chat_input("Ask a question about claims, fraud risk, or portfolio trends...") or queued

if user_prompt:
    # 1. Display User Message
    st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 2. Call Multi-Agent Backend
    with st.chat_message("assistant"):
        with st.spinner("Consulting multi-agent claims intelligence..."):
            # Format history for LLM context
            history_payload = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["chat_messages"][:-1]
                if m.get("content")
            ]
            response_data = send_chat_message(
                message=user_prompt,
                thread_id=st.session_state["chat_thread_id"],
                history=history_payload,
            )

        if response_data and "response" in response_data:
            answer = response_data.get("response", "")
            agents = response_data.get("agents_used", ["Claims Analyst Agent"])
            st.markdown(answer)
            st.caption(f"🧠 Agents used: {', '.join(agents)}")

            st.session_state["chat_messages"].append({
                "role": "assistant",
                "content": answer,
                "agents_used": agents,
            })
        else:
            fallback = "Unable to process your request at this time. Please check your backend connection."
            st.warning(fallback)
            st.session_state["chat_messages"].append({
                "role": "assistant",
                "content": fallback,
                "agents_used": [],
            })
