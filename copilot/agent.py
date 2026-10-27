"""The agent: intent, tools, guardrails, and handoff.

Core governance rules enforced by the agent:
1. Structured facts come only from this customer's records.
2. Policy facts come only from current retrieved documents, with citations.
3. If a claim has no source, it does not go out.
4. Irreversible actions, complaints, vulnerable-customer cases, and
   low-confidence answers go to a human, with full context, and the
   agent never claims the action is done.
"""
import re
from dataclasses import dataclass, field

from . import data
from .retrieval import Retriever, citation, load_chunks


def mask_email(email):
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"


def mask_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    return f"***-***-{digits[-4:]}" if len(digits) >= 4 else "***"


COMPLAINT_WORDS = ["complaint", "complain", "unhappy", "angry", "frustrated",
                   "terrible service", "speak to a manager", "speak to a human",
                   "manager", "supervisor", "escalate"]
VULNERABLE_WORDS = ["hardship", "vulnerable", "bereavement", "cannot afford",
                    "can't afford", "financial difficulty"]
ACTION_WORDS = ["cancel my account", "close my account", "transfer money",
                "transfer all", "refund me", "give me a refund", "make a payment",
                "pay my bill now", "send money", "change my address",
                "replace my card", "order a new card"]


@dataclass
class Answer:
    text: str
    intent: str
    sources: list = field(default_factory=list)
    escalated: bool = False
    handoff_note: str = ""


class Agent:
    def __init__(self, db_path=None):
        self.db_path = db_path or data.DB_PATH
        self.retriever = Retriever(load_chunks())

    # -- intent and guardrails -------------------------------------------
    def _escalation_reason(self, question):
        q = question.lower()
        if any(word in q for word in COMPLAINT_WORDS):
            return "complaint or request for a human manager"
        if any(word in q for word in VULNERABLE_WORDS):
            return "vulnerable-customer case, needs trained human handling"
        if any(word in q for word in ACTION_WORDS):
            return "irreversible or money-moving action, out of MVP scope (read-only)"
        return None

    def _intent(self, question):
        q = question.lower()
        if re.search(r"tkt-\d+", q):
            return "ticket_status"
        # "What does X mean?" is a guidance question, not a status lookup,
        # even when it mentions a ticket.
        if "mean" in q:
            return "product_guidance"
        # A status lookup ("where is my...?", "status of my...?") is a ticket
        # question even when it mentions a product like card delivery.
        if "ticket" in q or "request status" in q \
                or "where is my" in q or "status of my" in q or "my case" in q:
            return "ticket_status"
        # Product-specific questions take precedence over the generic word
        # "account": "fees for my savings account" is guidance, not a balance lookup.
        if any(phrase in q for phrase in
               ["fee", "interest rate", "withdrawal", "payment due", "due date",
                "how does", "how long", "card delivery", "mobile app", "login"]):
            return "product_guidance"
        if "account" in q or "balance" in q or "activity" in q \
                or "transaction" in q or "recent" in q:
            return "account_question"
        if "payment due" in q or "due date" in q or "when do i pay" in q:
            return "product_guidance"
        if any(word in q for word in
               ["product", "plan", "feature", "fee", "fees", "how does",
                "what is", "coverage", "limit", "interest rate", "sla",
                "how long", "delivery", "replacement", "policy"]):
            return "product_guidance"
        return "unknown"

    # -- tools (read-only) ------------------------------------------------
    def _account_answer(self, customer_id):
        customer = data.get_customer(self.db_path, customer_id)
        account = data.get_account(self.db_path, customer_id)
        activity = data.get_recent_activity(self.db_path, customer_id)
        if not customer or not account:
            return Answer("I could not find an account for this customer ID. "
                          "Please check the ID and try again, or ask for a human handoff.",
                          intent="account_question", escalated=True,
                          handoff_note="Customer ID not found.")
        lines = [
            f"Hi {customer['name']}, here is your account summary:",
            f"Account: {account['account_type']} {account['display_number']} - Status: {account['status']}",
            f"Balance: ${account['balance']:,.2f}",
            "Recent activity:",
        ]
        for item in activity:
            sign = "+" if item["direction"] == "Credit" else "-"
            lines.append(f"- {item['activity_date']}: {item['description']} "
                         f"({sign}${abs(item['amount']):,.2f})")
        lines.append("")
        lines.append("Contact on file: "
                     f"{mask_email(customer['email'])}, {mask_phone(customer['phone'])} "
                     "(masked for privacy).")
        source = "Snowflake CUSTOMER_ACCOUNTS and ACTIVITY_HISTORY (local demo copy)"
        return Answer("\n".join(lines), intent="account_question", sources=[source])

    def _ticket_answer(self, customer_id, question):
        match = re.search(r"tkt-\d+", question, re.IGNORECASE)
        ticket = data.get_ticket(self.db_path, customer_id,
                                 match.group(0).upper() if match else None)
        if not ticket:
            return Answer("I could not find that ticket for your account. "
                          "It may belong to a different account, or the ticket "
                          "number may be mistyped. I can hand this to an agent "
                          "to check, rather than guess.",
                          intent="ticket_status", escalated=True,
                          handoff_note="Ticket not found for this customer.")
        text = (
            f"Ticket {ticket['ticket_id']}: {ticket['subject']}\n"
            f"Status: {ticket['status']} (opened {ticket['opened_date']})\n"
            f"Next step: {ticket['next_step']}"
        )
        return Answer(text, intent="ticket_status",
                      sources=["Snowflake TICKET_STATUS (local demo copy)"])

    def _product_answer(self, question):
        results = self.retriever.retrieve(question, top_k=2)
        if not results:
            return Answer("I do not have a current approved policy that answers "
                          "that question, so I will not guess. Let me hand this "
                          "to an agent with your question attached.",
                          intent="product_guidance", escalated=True,
                          handoff_note="No current policy retrieved.")
        parts = ["Based on our current policies:"]
        sources = []
        for _score, chunk in results:
            parts.append(f"\n{chunk['text']}")
            sources.append(citation(chunk))
        return Answer("\n".join(parts), intent="product_guidance", sources=sources)

    # -- main entry point --------------------------------------------------
    def ask(self, customer_id, question):
        question = (question or "").strip()
        if not question:
            return Answer("Please ask a question, for example about your account, "
                          "a ticket, or a product.", intent="unknown", escalated=True)
        reason = self._escalation_reason(question)
        if reason:
            note = (f"Customer {customer_id} asked: '{question}'. "
                    f"Escalation reason: {reason}. No action was taken by the agent.")
            return Answer(
                "I understand, and I am not going to guess or take that action "
                "here. I have prepared a handoff for a human agent with your "
                "question and account context, so you will not have to repeat "
                "yourself. An agent will pick this up and confirm the next step "
                "with you directly.",
                intent="escalation", escalated=True, handoff_note=note)
        intent = self._intent(question)
        if intent == "account_question":
            return self._account_answer(customer_id)
        if intent == "ticket_status":
            return self._ticket_answer(customer_id, question)
        if intent == "product_guidance":
            return self._product_answer(question)
        # Unknown: try retrieval once, otherwise escalate honestly.
        results = self.retriever.retrieve(question, top_k=1)
        if results and results[0][0] >= 0.30:
            return self._product_answer(question)
        return Answer("I am not confident I have a current, approved answer for "
                      "that yet, so I would rather hand you to an agent than "
                      "risk a wrong answer.",
                      intent="unknown", escalated=True,
                      handoff_note=f"Low-confidence question: '{question}'.")
