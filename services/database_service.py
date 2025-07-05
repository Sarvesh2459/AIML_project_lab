import json
import os
from typing import List, Optional
from models.user import User

class DatabaseService:
    def __init__(self, db_file='data/users.json'):
        self.db_file = db_file
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure database file and directory exist"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        if not os.path.exists(self.db_file):
            self._save_users([])

    def _load_users(self) -> List[User]:
        """Load users from JSON file"""
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                return [User.from_dict(user_data) for user_data in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_users(self, users: List[User]):
        """Save users to JSON file"""
        with open(self.db_file, 'w') as f:
            json.dump([user.to_dict() for user in users], f, indent=2)

    def get_user_by_account(self, account_number: str) -> Optional[User]:
        """Get user by account number"""
        users = self._load_users()
        for user in users:
            if user.account_number == account_number:
                return user
        return None

    def get_user_by_name(self, name: str) -> Optional[User]:
        """Get user by name"""
        users = self._load_users()
        for user in users:
            if user.name.lower() == name.lower():
                return user
        return None

    def authenticate_user(self, name: str, account_number: str, auth_code: str) -> Optional[User]:
        """Authenticate user with credentials"""
        users = self._load_users()
        for user in users:
            if (user.name.lower() == name.lower() and 
                user.account_number == account_number and 
                user.verify_auth_code(auth_code) and 
                user.is_active):
                user.last_login = datetime.utcnow()
                self._save_users(users)
                return user
        return None

    def update_user(self, updated_user: User):
        """Update user in database"""
        users = self._load_users()
        for i, user in enumerate(users):
            if user.account_number == updated_user.account_number:
                users[i] = updated_user
                self._save_users(users)
                return True
        return False

    def transfer_money(self, from_account: str, to_account: str, amount: float) -> tuple[bool, str]:
        """Transfer money between accounts"""
        users = self._load_users()
        from_user = None
        to_user = None
        
        for user in users:
            if user.account_number == from_account:
                from_user = user
            elif user.account_number == to_account:
                to_user = user
        
        if not from_user:
            return False, "Source account not found"
        if not to_user:
            return False, "Destination account not found"
        if from_user.balance < amount:
            return False, "Insufficient funds"
        if amount <= 0:
            return False, "Invalid amount"
        
        try:
            from_user.update_balance(-amount)
            to_user.update_balance(amount)
            self._save_users(users)
            return True, "Transfer successful"
        except ValueError as e:
            return False, str(e)