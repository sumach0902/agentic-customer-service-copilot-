"""Streamlit Web UI with Customer Login & Real-Time Chat.

Run: streamlit run app.py
"""
import streamlit as st

from copilot import data
from copilot.agent import Agent, mask_email
from copilot.data import init_db

init_db()
agent = Agent()

st.set_page_config(page_title="Customer Service Copilot", page_icon="💬", layout="wide")

# Manage login session state
if "customer_id" not in st.session_state:
    st.session_state.customer_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Predefined demo credentials (supports individual password or universal fallback)
USER_PASSWORDS = {
    "CUST-1001": "priya123",
    "CUST-1002": "arjun123",
    "CUST-1003": "maya123",
}

# ==============================================================================
# 1. Login Screen (Unauthenticated)
# ==============================================================================
if not st.session_state.customer_id:
    st.markdown("<h1 style='text-align: center;'>Secure Customer Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Enter your credentials to access your account and chat with the Copilot</p>", unsafe_allow_html=True)
    st.write("")

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        with st.container(border=True):
            st.subheader("Customer Sign In")
            
            user_id_input = st.text_input("Customer ID", placeholder="e.g. CUST-1001")
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            
            with st.expander("🔑 Demo Login Credentials"):
                st.markdown("""
                | Customer ID | Name | Password |
                | :--- | :--- | :--- |
                | `CUST-1001` | Priya Sharma | `priya123` |
                | `CUST-1002` | Arjun Patel | `arjun123` |
                | `CUST-1003` | Maya Chen | `maya123` |
                *(Fallback password `password123` also works for all accounts)*
                """)

            if st.button("Sign In to Copilot", type="primary", use_container_width=True):
                uid = (user_id_input or "").strip().upper()
                pwd = (password_input or "").strip()
                
                if uid in USER_PASSWORDS and (pwd == USER_PASSWORDS[uid] or pwd == "password123"):
                    cust_profile = data.get_customer(data.DB_PATH, uid)
                    st.session_state.customer_id = uid
                    st.session_state.messages = [
                        {
                            "role": "assistant",
                            "content": f"Hi {cust_profile['name']}, I am your Customer Service Copilot. How can I help you today? You can ask about your account status, recent transactions, support tickets, or product policies.",
                            "intent": "greeting",
                            "sources": [],
                            "escalated": False,
                            "handoff_note": ""
                        }
                    ]
                    st.rerun()
                else:
                    st.error("Invalid Customer ID or Password. Please check the credentials above.")

# ==============================================================================
# 2. Authenticated Real-Time Chat Screen
# ==============================================================================
else:
    customer_id = st.session_state.customer_id
    cust = data.get_customer(data.DB_PATH, customer_id)
    acct = data.get_account(data.DB_PATH, customer_id)

    # Sidebar: Authenticated User Profile & Session Controls
    with st.sidebar:
        st.subheader("Authenticated Account")
        if cust and acct:
            st.markdown(f"### 👤 {cust['name']}")
            st.markdown(f"**ID:** `{cust['customer_id']}`")
            st.markdown(f"**Tier:** {cust['segment']}")
            st.markdown(f"**Account:** {acct['account_type']} (`{acct['display_number']}`)")
            st.markdown(f"**Status:** {acct['status']}")
            st.markdown(f"**Verified Contact:** `{mask_email(cust['email'])}`")
        
        st.divider()
        st.subheader("⚙️ Model & Context")
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.05,
            help="Controls determinism. In enterprise customer service, low temperature (0.0 - 0.2) enforces strict compliance and eliminates hallucinations."
        )
        context_window = st.select_slider(
            "Context Window",
            options=[1024, 2048, 4096, 8192],
            value=2048,
            help="Maximum token budget allocated per turn, including customer record state and retrieved policy documents."
        )

        st.caption("🔒 **Tenant Isolation:** All database and ticket queries in this session are strictly scoped to `customer_id`.")
        
        if st.button("Log Out / Switch Persona", use_container_width=True):
            st.session_state.customer_id = None
            st.session_state.messages = []
            st.rerun()

    # Main Area: Real-Time Chat Stream
    st.title("Customer Service Copilot")
    st.caption(f"Logged in as **{cust['name']}** (`{cust['customer_id']}`) • Read-Only Scoped AI Copilot")

    # Render previous conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("escalated"):
                st.warning("🛡️ **Escalation Triggered:** Handed off to human agent (copilot is strictly read-only).")
            
            st.markdown(msg["content"])
            
            if msg.get("handoff_note"):
                st.info(f"📋 **Handoff Note (for human agent):**\n\n*{msg['handoff_note']}*")

            if msg.get("tokens_used"):
                st.caption(
                    f"⚙️ **Inference:** Temp `{msg.get('temperature', 0.1):.2f}` • "
                    f"Context Window `{msg.get('context_window', 2048):,} tokens` • "
                    f"Used `{msg.get('tokens_used', 0)} tokens`"
                )

    # Real-time chat input field
    if prompt := st.chat_input("Ask about your account, a ticket, or product policies..."):
        # 1. Append user turn
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. Query Copilot Agent with temperature and context window
        answer = agent.ask(customer_id, prompt, temperature=temperature, context_window=context_window)

        # 3. Append assistant turn
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer.text,
            "intent": answer.intent,
            "sources": answer.sources,
            "escalated": answer.escalated,
            "handoff_note": answer.handoff_note,
            "temperature": answer.temperature,
            "context_window": answer.context_window,
            "tokens_used": answer.tokens_used
        })
        st.rerun()
