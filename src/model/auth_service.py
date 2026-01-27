import json
from .gugu_client import GuguClient


class AuthService(GuguClient):
    LOGIN_PATH = "/gugux-services-auth-api/app/auth/pwd/login"
    PUBLIC_KEY_PATH = "/gugux-services-auth-api/app/key"

    def get_public_key(self):
        print("[*] Fetching public key...")
        resp = self.get(self.PUBLIC_KEY_PATH)
        if resp.status_code == 200:
            try:
                data = resp.json()
                if 'code' in data and data['code'] == 200:
                    return data['data']
                elif 'data' in data:
                    return data['data']
            except ValueError:
                pass
        print(f"[-] Failed to fetch public key. Status: {resp.status_code}")
        return None

    def login(self, phone, password):
        public_key_str = self.get_public_key()
        if not public_key_str:
            return False

        encrypted_pwd = self.encrypt_password(public_key_str, password)
        payload = {"phone": phone, "password": encrypted_pwd}

        print("[*] Performing login POST...")
        resp = self.post(self.LOGIN_PATH, json_data=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') or data.get('code') == 200:
                login_data = data.get('data')
                if login_data and isinstance(login_data, dict):
                    self.token = login_data.get('accessToken')

                    # Extract userId from JWT payload
                    try:
                        _, payload_b64, _ = self.token.split('.')
                        # Add padding if needed
                        payload_b64 += '=' * (-len(payload_b64) % 4)
                        payload = json.loads(
                            base64.b64decode(payload_b64).decode())
                        self.user_id = str(payload.get('current_user_id'))
                    except Exception as e:
                        print(f"[-] Failed to extract userId from token: {e}")
                        self.user_id = None

                    print(f"[+] Login successful. User ID: {self.user_id}")
                    self.save_session()
                    return True
        print(f"[-] Login failed: {resp.text}")
        return False
