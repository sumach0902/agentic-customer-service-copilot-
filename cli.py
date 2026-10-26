"""Command-line demo. No web server, no API key needed.

Usage:
    python3 generate_data.py
    python3 cli.py --demo
    python3 cli.py --customer CUST-1001 --ask "What is my account status?"
    python3 cli.py --interactive
"""
import argparse
import sys

from copilot.agent import Agent
from copilot.data import init_db

DEMO_QUESTIONS = [
    "What is my account status and recent activity?",
    "What is the status of my ticket TKT-5001?",
    "What are the fees for my savings account?",
    "I want to cancel my account and transfer all my money out.",
]


def show(answer):
    print(f"\n[{answer.intent}] escalated={answer.escalated}")
    print(answer.text)
    if answer.sources and "Sources:" not in answer.text:
        print("\nSources:")
        for source in answer.sources:
            print(f"- {source}")
    if answer.handoff_note:
        print(f"\nHandoff note (agent only): {answer.handoff_note}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer", default="CUST-1001")
    parser.add_argument("--ask")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    init_db()
    agent = Agent()

    if args.demo:
        for question in DEMO_QUESTIONS:
            print(f"\n=== Customer {args.customer} asks: {question} ===")
            show(agent.ask(args.customer, question))
        return 0

    if args.ask:
        show(agent.ask(args.customer, args.ask))
        return 0

    if args.interactive:
        print(f"Customer: {args.customer} (type 'quit' to exit)")
        while True:
            question = input("\nYou: ").strip()
            if question.lower() in ("quit", "exit"):
                break
            show(agent.ask(args.customer, question))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
