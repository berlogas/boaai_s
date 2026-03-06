import requests
import httpx
import streamlit as st
from typing import Optional, Dict, List

class APIClient:
    def __init__(self, base_url: str = None):
        # Используем имя сервиса Docker для надёжности
        # IP адрес может меняться при пересоздании контейнеров
        self.base_url = base_url or "http://backend:8000"
        # Инициализируем токен из session_state при каждом создании экземпляра
        self.token = st.session_state.get("auth_token", None)
        self.role = st.session_state.get("user_role", None)
    
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

    def get_global_documents(self) -> List[Dict]:
        """Получить список документов в глобальной базе (доступно всем)"""
        try:
            # Используем публичный endpoint без авторизации
            response = requests.get(
                f"{self.base_url}/global-index/documents",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return []

    def upload_to_global_index(self, uploaded_file) -> Optional[Dict]:
        """Загрузить документ в глобальную базу через curl"""
        try:
            token = st.session_state.get("auth_token")
            if not token:
                st.error("Нет токена авторизации.")
                return None
            
            import subprocess
            import json
            import os
            
            # Сохраняем файл
            file_data = uploaded_file.read()
            tmp_path = f'/tmp/upload_{uploaded_file.name}'
            
            with open(tmp_path, 'wb') as f:
                f.write(file_data)
            
            st.write(f"📤 Загрузка файла...")
            
            # Выполняем curl БЕЗ capture_output - вывод напрямую
            cmd = f'curl -s -w "\\nHTTP_CODE:%{{http_code}}" -X POST "http://backend:8000/admin/global-index/upload" -H "Authorization: Bearer {token}" -H "Connection: close" -F "file=@{tmp_path}"'
            
            st.write(f"📞 {cmd}")
            
            # Используем shell=True для правильного экранирования
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=60,
                bufsize=1
            )
            
            output = result.stdout
            
            st.write(f"📥 Вывод curl:")
            st.code(output[:500])
            
            # Ищем HTTP код
            if 'HTTP_CODE:' in output:
                http_code = output.split('HTTP_CODE:')[1].strip()
                body = '\n'.join(output.split('HTTP_CODE:')[0].split('\n')[:-1])
                
                if http_code == '200':
                    try:
                        response_data = json.loads(body)
                        st.write(f"✅ Успех: {response_data.get('message', 'OK')}")
                        return response_data
                    except Exception as e:
                        st.error(f"Ошибка парсинга JSON: {e}")
                        st.error(f"Тело: {body[:200]}")
                else:
                    st.error(f"HTTP ошибка: {http_code}")
                    st.error(f"Ответ: {body[:200]}")
            else:
                st.error("Не найден HTTP_CODE в выводе")
            
            return None
            
        except subprocess.TimeoutExpired:
            st.error("⏰ Таймаут (60 сек)")
            return None
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def delete_global_document(self, doc_name: str) -> Optional[Dict]:
        """Удалить документ из глобальной базы"""
        try:
            response = requests.delete(
                f"{self.base_url}/admin/global-index/documents/{doc_name}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

    def rebuild_global_index(self) -> Optional[Dict]:
        """Переиндексировать глобальную базу"""
        try:
            response = requests.post(
                f"{self.base_url}/admin/global-index/rebuild",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

    def get_pending_uploads(self) -> List[Dict]:
        """Получить список файлов в папке uploads"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/global-index/pending",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return []

    def process_pending_uploads(self) -> Optional[Dict]:
        """Загрузить все файлы из папки uploads в глобальную базу"""
        try:
            response = requests.post(
                f"{self.base_url}/admin/global-index/process-uploads",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

    def delete_pending_upload(self, file_name: str) -> Optional[Dict]:
        """Удалить файл из папки uploads без загрузки"""
        try:
            response = requests.delete(
                f"{self.base_url}/admin/global-index/pending/{file_name}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"Ошибка: {response.status_code}")
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None

    def get_upload_status(self) -> Dict:
        """Получить статус загрузки файлов"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/global-index/process-uploads/status",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return {"message": "Нет данных о загрузке"}
        except Exception as e:
            return {"message": f"Ошибка: {str(e)}"}

    def get_audit_log(self) -> List[Dict]:
        """Получить журнал аудита"""
        try:
            response = requests.get(
                f"{self.base_url}/admin/audit-log",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return []

api_client = APIClient()
