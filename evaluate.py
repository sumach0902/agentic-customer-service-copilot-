"""Golden-set evaluation: the number Suma can quote in the interview.

Each case checks three things: intent was right, a citation/source was
present when one was expected, and escalation happened exactly when
it should have. The script prints the scores and writes
results/eval_results.json. Run it after every change: a change that
improves wording but breaks citations must not ship.
"""
import json
from pathlib import Path

from copilot.agent import Agent
from copilot.data import init_db

# (customer, question, expected_intent, expected_source_substring, should_escalate)
CASES = [
    ("CUST-1001", "What is my account status?", "account_question", "CUSTOMER_ACCOUNTS", False),
    ("CUST-1001", "What is my balance?", "account_question", "CUSTOMER_ACCOUNTS", False),
    ("CUST-1001", "Show my recent activity", "account_question", "CUSTOMER_ACCOUNTS", False),
    ("CUST-1001", "What are my recent transactions?", "account_question", "CUSTOMER_ACCOUNTS", False),
    ("CUST-1002", "What is my account balance?", "account_question", "CUSTOMER_ACCOUNTS", False),
    ("CUST-1003", "What is my account status and recent activity?", "account_question", "CUSTOMER_ACCOUNTS", False),
    ("CUST-1001", "What is the status of my ticket TKT-5001?", "ticket_status", "TICKET_STATUS", False),
    ("CUST-1001", "Where is my card delivery request?", "ticket_status", "TICKET_STATUS", False),
    ("CUST-1001", "What is the status of my request?", "ticket_status", "TICKET_STATUS", False),
    ("CUST-1002", "What is the status of my ticket TKT-5003?", "ticket_status", "TICKET_STATUS", False),
    ("CUST-1003", "What is the status of my ticket TKT-5004?", "ticket_status", "TICKET_STATUS", False),
    ("CUST-1001", "How long do standard requests take?", "product_guidance", "Ticket and Request Status", False),
    ("CUST-1001", "What are the fees for my savings account?", "product_guidance", "Savings Account Features", False),
    ("CUST-1001", "Is there a monthly fee on savings?", "product_guidance", "Savings Account Features", False),
    ("CUST-1001", "When is my payment due?", "product_guidance", "Billing and Payments", False),
    ("CUST-1001", "What is the payment due date?", "product_guidance", "Billing and Payments", False),
    ("CUST-1001", "How does card delivery work?", "product_guidance", "Card Services", False),
    ("CUST-1001", "How do I log in to the mobile app?", "product_guidance", "Mobile App", False),
    ("CUST-1001", "What is the savings withdrawal limit?", "product_guidance", "Savings Account Features", False),
    ("CUST-1001", "What does In Progress mean for a ticket?", "product_guidance", "Ticket and Request Status", False),
    ("CUST-1001", "I want to cancel my account", "escalation", "", True),
    ("CUST-1001", "Close my account please", "escalation", "", True),
    ("CUST-1001", "Transfer all my money out", "escalation", "", True),
    ("CUST-1001", "Refund me right now", "escalation", "", True),
    ("CUST-1001", "Make a payment for me now", "escalation", "", True),
    ("CUST-1001", "I am unhappy and want to speak to a manager", "escalation", "", True),
    ("CUST-1001", "This is a complaint about my service", "escalation", "", True),
    ("CUST-1001", "I am in financial hardship and cannot afford this", "escalation", "", True),
    ("CUST-1001", "Replace my card please", "escalation", "", True),
    ("CUST-1001", "Order a new card for me", "escalation", "", True),
]


def main():
    init_db()
    agent = Agent()
    results = []
    for customer, question, expected_intent, expected_source, should_escalate in CASES:
        answer = agent.ask(customer, question)
        sources_text = " ".join(answer.sources)
        intent_ok = answer.intent == expected_intent
        source_ok = (not expected_source) or (expected_source in sources_text or expected_source in answer.text)
        escalation_ok = answer.escalated == should_escalate
        passed = intent_ok and source_ok and escalation_ok
        results.append({
            "question": question, "expected_intent": expected_intent,
            "got_intent": answer.intent, "escalated": answer.escalated,
            "intent_ok": intent_ok, "source_ok": source_ok,
            "escalation_ok": escalation_ok, "passed": passed,
        })
        print(f"{'PASS' if passed else 'FAIL'} | {question} "
              f"(intent {answer.intent}, escalated={answer.escalated})")

    total = len(results)
    summary = {
        "total": total,
        "passed": sum(r["passed"] for r in results),
        "intent_accuracy": sum(r["intent_ok"] for r in results) / total,
        "source_accuracy": sum(r["source_ok"] for r in results) / total,
        "escalation_accuracy": sum(r["escalation_ok"] for r in results) / total,
        "cases": results,
    }
    out = Path("results/eval_results.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nPassed {summary['passed']}/{total}")
    print(f"Intent accuracy: {summary['intent_accuracy']:.0%}")
    print(f"Source accuracy: {summary['source_accuracy']:.0%}")
    print(f"Escalation accuracy: {summary['escalation_accuracy']:.0%}")
    print(f"Wrote {out}")
    return 0 if summary["passed"] == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
