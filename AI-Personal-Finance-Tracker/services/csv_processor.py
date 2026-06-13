import csv
from io import TextIOWrapper

class CSVProcessor:
    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file

    def parse_transactions(self):
        reader = csv.DictReader(TextIOWrapper(self.uploaded_file, encoding="utf-8"))
        transactions = []
        for row in reader:
            transactions.append(
                {
                    "amount": float(row.get("amount", 0) or 0),
                    "category": row.get("category", "Other"),
                    "description": row.get("description", ""),
                    "transaction_type": row.get("transaction_type", "expense"),
                    "transaction_date": row.get("transaction_date", ""),
                }
            )
        return transactions
