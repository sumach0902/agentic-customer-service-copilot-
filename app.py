"""Streamlit UI with Live Demo & Architecture Presentation tabs.

Run: streamlit run app.py
"""
from pathlib import Path
import streamlit as st

from copilot.agent import Agent
from copilot.data import init_db

init_db()
agent = Agent()
ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "docs" / "images"

st.set_page_config(page_title="Customer Service Copilot", layout="wide")
st.title("Customer Service Copilot")
st.caption("Enterprise Agentic AI: Scoped Read-Only Truth, Versioned Policy Governance & Guardrails")

tab_demo, tab_arch, tab_flow, tab_schema = st.tabs([
    "💬 Interactive Demo",
    "🏛️ System Architecture",
    "🔄 Code Execution Flow",
    "🗄️ Database Schema"
])

with tab_demo:
    st.subheader("Live Copilot Interaction")
    col1, col2 = st.columns([1, 2])
    with col1:
        customer = st.selectbox("Select Customer Context", ["CUST-1001", "CUST-1002", "CUST-1003"])
        st.markdown("""
        **Quick Prompts to Test:**
        - `What is my account status and recent activity?`
        - `What is the status of my ticket TKT-5001?`
        - `What are the fees for my savings account?`
        - `I want to cancel my account and transfer all my money out.`
        """)
    with col2:
        question = st.text_input("Ask about your account, a ticket, or a product",
                                 placeholder="e.g., What is my account status and recent activity?")
        if st.button("Submit Question", type="primary") and question:
            answer = agent.ask(customer, question)
            if answer.escalated:
                st.warning("Handed off to a human agent (no action taken by the copilot).")
            else:
                st.success("Response generated with verified sources.")
            st.markdown(f"**Intent:** `{answer.intent}`")
            st.write(answer.text)
            if answer.sources:
                st.markdown("**Sources & Citations:**")
                for source in answer.sources:
                    st.markdown(f"- *{source}*")
            if answer.handoff_note:
                st.info(f"**Handoff note (for human agent):** {answer.handoff_note}")

with tab_arch:
    st.subheader("System Architecture")
    st.write("End-to-end design connecting client interfaces, guardrails, dual-path execution (RDBMS & RAG), and automated evaluation.")
    arch_img = IMG_DIR / "system_architecture.jpg"
    if arch_img.exists():
        st.image(str(arch_img), use_container_width=True)

with tab_flow:
    st.subheader("Code Execution Flow & Calling Sequence")
    st.write("Step-by-step numbered execution path showing how incoming requests are guarded, classified, and routed to tools.")
    flow_img = IMG_DIR / "code_execution_flow.jpg"
    if flow_img.exists():
        st.image(str(flow_img), use_container_width=True)

with tab_schema:
    st.subheader("Database Schema Design (RDBMS)")
    st.write("Hub-and-Spoke relational design with strict customer tenant scoping (`WHERE customer_id = ?`) to eliminate data leaks.")
    schema_img = IMG_DIR / "schema_design.jpg"
    if schema_img.exists():
        st.image(str(schema_img), use_container_width=True)

