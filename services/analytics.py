from collections import defaultdict
from datetime import datetime

class AnalyticsService:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    def generate_dashboard_summary(self):
        income = self._sum_transactions("income")
        expenses = self._sum_transactions("expense")
        balance = income - expenses
        savings_rate = round((balance / income * 100), 2) if income > 0 else 0
        return {
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "balance": round(balance, 2),
            "savings_rate": savings_rate,
        }

    def _sum_transactions(self, transaction_type):
        row = self.db.execute(
            "SELECT SUM(amount) AS total FROM transactions WHERE user_id = ? AND transaction_type = ?",
            (self.user_id, transaction_type),
        ).fetchone()
        return row["total"] if row["total"] else 0

    def expense_breakdown_by_category(self):
        rows = self.db.execute(
            "SELECT category, SUM(amount) AS total FROM transactions WHERE user_id = ? AND transaction_type = 'expense' GROUP BY category",
            (self.user_id,),
        ).fetchall()
        categories = [row["category"] for row in rows]
        values = [round(row["total"], 2) for row in rows]
        return {"categories": categories, "values": values}

    def monthly_trend_data(self):
        import datetime
        six_months_ago = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
        rows = self.db.execute(
            "SELECT substr(transaction_date, 1, 7) AS month, SUM(amount) AS total FROM transactions "
            "WHERE user_id = ? AND transaction_type = 'expense' AND transaction_date >= ? "
            "GROUP BY month ORDER BY month ASC",
            (self.user_id, six_months_ago),
        ).fetchall()
        labels = [row["month"] for row in rows]
        values = [round(row["total"], 2) for row in rows]
        return {"labels": labels, "values": values}

    def budget_status_summary(self):
        rows = self.db.execute(
            "SELECT b.id, b.category, b.budget_amount, b.month, COALESCE(SUM(t.amount), 0) AS spent FROM budgets b LEFT JOIN transactions t ON b.user_id = t.user_id AND b.category = t.category AND t.transaction_type = 'expense' AND substr(t.transaction_date, 1, 7) = b.month WHERE b.user_id = ? GROUP BY b.id ORDER BY b.month DESC",
            (self.user_id,),
        ).fetchall()
        budget_status = []
        for row in rows:
            spent = row["spent"]
            remaining = round(row["budget_amount"] - spent, 2)
            status = "on-track"
            if remaining < 0:
                status = "over-budget"
            elif remaining <= row["budget_amount"] * 0.2:
                status = "warning"
            budget_status.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "month": row["month"],
                    "budget_amount": round(row["budget_amount"], 2),
                    "spent": round(spent, 2),
                    "remaining": remaining,
                    "status": status,
                }
            )
        return budget_status
