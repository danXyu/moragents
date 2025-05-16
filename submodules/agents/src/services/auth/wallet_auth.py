import secrets
from datetime import datetime
from typing import Dict, Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from web3 import Web3

from models.db.user_models import User


class WalletAuthService:
    def __init__(self):
        self.challenges: Dict[str, Dict] = {}
        self.web3 = Web3()

    def generate_challenge(self, wallet_address: str) -> str:
        """Generate a challenge message for the user to sign with their wallet"""
        nonce = secrets.token_hex(16)
        challenge = f"Sign this message to authenticate with the app: {nonce}"
        self.challenges[wallet_address.lower()] = {"message": challenge, "timestamp": datetime.utcnow()}
        return challenge

    def verify_signature(self, wallet_address: str, signature: str) -> bool:
        """Verify that the signature matches the challenge for the wallet address"""
        wallet_address = wallet_address.lower()

        if wallet_address not in self.challenges:
            return False

        challenge_data = self.challenges[wallet_address]
        # Check if challenge is expired (5 minutes)
        if (datetime.utcnow() - challenge_data["timestamp"]).total_seconds() > 300:
            del self.challenges[wallet_address]
            return False

        try:
            message = encode_defunct(text=challenge_data["message"])
            recovered_address = Account.recover_message(message, signature=signature)
            # Clean up the used challenge
            del self.challenges[wallet_address]
            return recovered_address.lower() == wallet_address
        except Exception:
            return False


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_wallet(self, wallet_address: str) -> Optional[User]:
        """Get a user by wallet address"""
        return self.db.query(User).filter(User.wallet_address == wallet_address.lower()).first()

    def create_user(self, wallet_address: str) -> User:
        """Create a new user with the given wallet address"""
        try:
            user = User(wallet_address=wallet_address.lower())
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            # User might have been created by another concurrent request
            return self.get_user_by_wallet(wallet_address)

    def get_or_create_user(self, wallet_address: str) -> User:
        """Get a user by wallet address or create if doesn't exist"""
        user = self.get_user_by_wallet(wallet_address)
        if not user:
            user = self.create_user(wallet_address)
        return user
