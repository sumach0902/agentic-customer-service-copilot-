"""Rebuild the synthetic customer database."""
from copilot.data import DB_PATH, init_db

if __name__ == "__main__":
    path = init_db()
    print(f"Created {path}")
    print("Demo customers: CUST-1001 (Priya Sharma), CUST-1002 (Arjun Patel), CUST-1003 (Maya Chen)")
