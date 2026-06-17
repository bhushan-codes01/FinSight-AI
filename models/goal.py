import sqlite3

class Goal:
    def __init__(self, id, user_id, title, target_amount, current_amount, deadline, created_at=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.target_amount = target_amount
        self.current_amount = current_amount
        self.deadline = deadline
        self.created_at = created_at

    @staticmethod
    def create(db, user_id, title, target_amount, deadline):
        cursor = db.execute(
            "INSERT INTO goals (user_id, title, target_amount, current_amount, deadline) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, target_amount, 0.0, deadline)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_all_by_user(db, user_id):
        rows = db.execute(
            "SELECT id, user_id, title, target_amount, current_amount, deadline, created_at FROM goals WHERE user_id = ? ORDER BY deadline ASC",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def update_progress(db, goal_id, user_id, amount):
        row = db.execute(
            "SELECT current_amount, target_amount FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        ).fetchone()
        if not row:
            return None
        new_amount = min(row["current_amount"] + amount, row["target_amount"])
        db.execute(
            "UPDATE goals SET current_amount = ? WHERE id = ? AND user_id = ?",
            (new_amount, goal_id, user_id)
        )
        db.commit()
        return new_amount

    @staticmethod
    def delete(db, goal_id, user_id):
        cursor = db.execute(
            "DELETE FROM goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        db.commit()
        return cursor.rowcount > 0
