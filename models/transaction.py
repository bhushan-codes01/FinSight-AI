class Transaction:
    def __init__(self, id, user_id, amount, category, description, transaction_type, transaction_date, created_at):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.category = category
        self.description = description
        self.transaction_type = transaction_type
        self.transaction_date = transaction_date
        self.created_at = created_at
