import requests
import streamlit as st
from typing import Optional, Dict, List

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or st.secrets.get("BACKEND_URL", "http://backend:8000")
        self.token = None
        self.role = None
    
    def set_token(self, token: str, role: str):
        self.token = token
        self.role = role
        st.session_state["auth_token"] = token
        st.session_state["user_role"] = role
    
    def get_headers(self) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        try:
            response = requests.post(f"{self.base_url}/token", data={"username": username, "password": password}, headers={"Content-Type": "application/x-www-form-urlencoded"})            
            if response.status_code == 200:
                data = response.json()
                self.set_token(data["access_token"], data["role"])
                return data
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None
    
    def logout(self):
        self.token = None
        self.role = None
        st.session_state.pop("auth_token", None)
        st.session_state.pop("user_role", None)
    
    def create_session(self, name: str) -> Optional[Dict]:
        try:
            response = requests.post(f"{self.base_url}/sessions/", json={"name": name}, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_sessions(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/sessions/", headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def query(self, query: str, session_id: Optional[str] = None, mode: str = "hybrid") -> Optional[Dict]:
        try:
            payload = {"query": query, "mode": mode}
            if session_id:
                payload["session_id"] = session_id
            response = requests.post(f"{self.base_url}/query", json=payload, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def quick_query(self, query: str) -> Optional[Dict]:
        try:
            response = requests.post(f"{self.base_url}/quick-query", json={"query": query})
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def create_user(self, username: str, password: str, role: str) -> Optional[Dict]:
        try:
            response = requests.post(
                f"{self.base_url}/users/",
                json={"username": username, "password": password, "role": role},
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                st.warning(f"Пользователь '{username}' уже существует")
            else:
                st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

    def update_user(self, username: str, password: str, role: str) -> Optional[Dict]:
        try:
            response = requests.put(
                f"{self.base_url}/users/{username}",
                json={"username": username, "password": password, "role": role},
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

    def delete_user(self, username: str) -> Optional[Dict]:
        try:
            response = requests.delete(
                f"{self.base_url}/users/{username}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

api_client = APIClient()
