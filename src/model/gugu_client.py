import requests
import time
import json
import base64
import os
import urllib3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GuguClient:
    BASE_URL = "https://api.caigetuxun.com"
    VERSION_CODE = "547"
    VERSION_NAME = "5.4.7"
    PLATFORM = "Android_33_13_Xiaomi_Mi10Pro"
    BRAND = "Xiaomi"
    DEVICE_ID = "22972135dee6e38edb62a06ba64c2ed00"

    def __init__(self, session_file="session.json"):
        self.session_file = session_file
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.equals_id = str(int(time.time() * 1000))
        self.request_id = 0
        self.load_session()

    def save_session(self):
        print(f"[*] Saving session to {self.session_file}...")
        session_data = {
            "token": self.token,
            "user_id": self.user_id,
            "cookies": self.session.cookies.get_dict(),
            "equals_id": self.equals_id,
            "request_id": self.request_id
        }
        with open(self.session_file, "w") as f:
            json.dump(session_data, f)

    def load_session(self):
        if os.path.exists(self.session_file):
            print(f"[*] Loading session from {self.session_file}...")
            try:
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                    self.token = session_data.get("token")
                    self.user_id = session_data.get("user_id")
                    self.equals_id = session_data.get(
                        "equals_id", self.equals_id)
                    self.request_id = session_data.get("request_id", 0)
                    cookies = session_data.get("cookies", {})
                    self.session.cookies.update(cookies)
                print(f"[+] Session loaded. Token exists: {bool(self.token)}")
                return True
            except Exception as e:
                print(f"[-] Failed to load session: {e}")
        return False

    def get_headers(self):
        self.request_id += 1
        ts = str(int(time.time() * 1000))
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "d_deviceId": self.DEVICE_ID,
            "d_equalsId": self.equals_id,
            "d_platform": self.PLATFORM,
            "d_brand": self.BRAND,
            "d_requestId": str(self.request_id),
            "d_versionCode": self.VERSION_CODE,
            "d_versionName": self.VERSION_NAME,
            "d_clientTs": ts,
            "User-Agent": "okhttp/4.9.1"
        }
        if self.token:
            headers["token"] = self.token
        return headers

    def encrypt_password(self, public_key_str, password):
        if "BEGIN PUBLIC KEY" not in public_key_str:
            public_key_str = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"
        public_key = serialization.load_pem_public_key(public_key_str.encode())
        encrypted = public_key.encrypt(
            password.encode(),
            padding.PKCS1v15()
        )
        return base64.b64encode(encrypted).decode()

    def post(self, url, json_data=None, use_base_url=True, headers=None):
        full_url = f"{self.BASE_URL}{url}" if use_base_url else url
        request_headers = self.get_headers()
        if headers:
            request_headers.update(headers)
        return self.session.post(full_url, headers=request_headers, json=json_data, verify=False)

    def get(self, url, use_base_url=True, headers=None):
        full_url = f"{self.BASE_URL}{url}" if use_base_url else url
        request_headers = self.get_headers()
        if headers:
            request_headers.update(headers)
        return self.session.get(full_url, headers=request_headers, verify=False)
