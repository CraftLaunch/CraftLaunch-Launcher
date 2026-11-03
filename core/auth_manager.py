import os
import json
import uuid
from typing import Dict, Any, Optional
import minecraft_launcher_lib

SESSION_FILE = "session.json"

class AuthManager:
    def __init__(self, client_id: str = "00000000402b5328", redirect_url: str = "https://live.com"):
        self.client_id = client_id
        self.redirect_url = redirect_url
        self.session_data = self.load_saved_session()

    def load_saved_session(self, self_param=None) -> Optional[Dict[str, Any]]:
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def save_session(self, data: Dict[str, Any]) -> None:
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.session_data = data
        except Exception:
            pass

    def create_offline_profile(self, username: str) -> Dict[str, Any]:
        profile_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, username)).replace("-", "")
        session = {
            "username": username,
            "uuid": profile_id,
            "access_token": "00000000000000000000000000000000",
            "token": "00000000000000000000000000000000",
            "user_properties": "{}",
            "user_type": "legacy"
        }
        self.session_data = session
        return session
