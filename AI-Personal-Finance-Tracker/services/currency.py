CURRENCIES = {
    'INR': {'symbol': '₹', 'name': 'Indian Rupee'},
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
    'AUD': {'symbol': 'A$', 'name': 'Australian Dollar'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar'},
    'AED': {'symbol': 'د.إ', 'name': 'UAE Dirham'},
    'SGD': {'symbol': 'S$', 'name': 'Singapore Dollar'},
}

def get_currency_symbol(db, user_id):
    """Fetch user's currency_symbol from DB, returns '₹' if not set."""
    if not user_id:
        return '₹'
    try:
        row = db.execute("SELECT currency_symbol FROM users WHERE id = ?", (user_id,)).fetchone()
        if row and row["currency_symbol"]:
            return row["currency_symbol"]
    except Exception as e:
        print(f"Error fetching currency symbol for user {user_id}: {e}")
    return '₹'
