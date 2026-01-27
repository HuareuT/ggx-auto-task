import time
import uuid
import os
import hashlib
import hmac
import base64
import requests
import json
from datetime import datetime
from email.utils import formatdate
from typing import List, Dict, Any, Callable
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from PIL import Image


class OssService:
    """
    Handles real OSS upload process for the GuguXing app.
    Fetches STS tokens and performs PUT uploads to Aliyun OSS.
    """

    def __init__(self, client):
        self.client = client
        self.bucket = "guguxing"
        # Public host
        self.os_host_public = "https://media.caigetuxun.com/"
        # Aliyun OSS endpoint for PUT
        self.os_endpoint = "http://guguxing.oss-cn-hangzhou.aliyuncs.com/"
        self.parent_prefix = "multi/"
        self._sts_token = None
        self._token_expiry = 0

    def _get_user_id(self) -> str:
        # Use the user_id from the client (populated from session/login)
        return self.client.user_id or "1"

    def decrypt_param(self, encrypted_text: str) -> str:
        """
        Decrypts the 'param' field from API responses using AES/ECB/PKCS5Padding.
        Key from com.ggx_network.utils.AesUtil.
        """
        try:
            # AES key from com.ggx_network.utils.AesUtil
            key_base64 = "O7hvpcRJSnWLMzDKt/q0QcBPNJ3vTxX13yeutoD5e+w="
            key = base64.b64decode(key_base64)

            # ECB mode
            encrypted_data = base64.b64decode(encrypted_text)
            cipher = Cipher(algorithms.AES(key), modes.ECB(),
                            backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(
                encrypted_data) + decryptor.finalize()

            # Unpad PKCS5/PKCS7 (128-bit block size)
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"[-] Decryption failed: {e}")
            return None

    def fetch_sts_token(self) -> Dict[str, Any]:
        """
        Fetches real STS token from GuguXing server.
        Uses minimal headers as heavy headers cause 500 errors.
        """
        # Based on successful test_sts.py results
        name = "article"
        url = f"https://api.caigetuxun.com/gugux-services-poly-api/app/file/token?sessionName={name}"

        print(f"[*] Fetching real STS token (minimal headers)...")

        headers = {
            "token": self.client.token,
            "User-Agent": "okhttp/4.9.2"
        }

        # Perform request directly to avoid GuguClient heavy headers
        resp = requests.get(url, headers=headers, verify=False)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                # Regular success
                self._sts_token = data.get('data')
                print("[+] STS token fetched successfully.")
                return self._sts_token
            elif 'param' in data:
                # Encrypted success
                print("[*] Response returned encrypted param. Decrypting...")
                decrypted_json = self.decrypt_param(data['param'])
                if decrypted_json:
                    decrypted_data = json.loads(decrypted_json)
                    raw_data = decrypted_data.get('data')
                    if raw_data:
                        # Map capitalized keys to service-expected lowercase keys
                        self._sts_token = {
                            "accessKeyId": raw_data.get("AccessKeyId"),
                            "accessKeySecret": raw_data.get("AccessKeySecret"),
                            "securityToken": raw_data.get("SecurityToken"),
                            "bucket": raw_data.get("BucketName")
                        }
                        print("[+] STS token fetched and mapped successfully.")
                        return self._sts_token

        print(f"[-] Failed to fetch STS token. Results: {resp.text}")
        return None

    def _generate_oss_path(self, file_path: str, type_prefix: str = "article/") -> str:
        ext = os.path.splitext(file_path)[1] or ".jpeg"
        user_id = self._get_user_id()
        file_uuid = str(uuid.uuid4()).replace("-", "").lower()
        # Pattern matching curl: multi/article/3956043558293610315/150877154af54b69e64a10d09.jpeg
        # Note: The user's curl had a weird prefix in UUID, but let's use standard UUID.
        return f"{self.parent_prefix}{type_prefix}{user_id}/{file_uuid}{ext}"

    def _sign_oss_request(self, method: str, content_type: str, date_str: str, oss_headers: Dict[str, str], resource: str, access_key_secret: str) -> str:
        """
        Calculates Aliyun OSS V1 Signature.
        """
        # CanonicalizedOSSHeaders: sort by key, lower case, append with \n
        sorted_headers = sorted(oss_headers.items())
        canonicalized_headers = ""
        for k, v in sorted_headers:
            if k.lower().startswith("x-oss-"):
                canonicalized_headers += f"{k.lower()}:{v}\n"

        string_to_sign = f"{method}\n\n{content_type}\n{date_str}\n{canonicalized_headers}{resource}"

        h = hmac.new(access_key_secret.encode('utf-8'),
                     string_to_sign.encode('utf-8'), hashlib.sha1)
        signature = base64.b64encode(h.digest()).decode('utf-8')
        return signature

    def upload_file(self, local_path: str, type_prefix: str = "article/") -> str:
        """
        Performs real PUT upload to Aliyun OSS.
        """
        if not self._sts_token:
            if not self.fetch_sts_token():
                return None

        if not os.path.exists(local_path):
            print(f"[-] File not found: {local_path}")
            return None

        oss_path = self._generate_oss_path(local_path, type_prefix)
        url = f"{self.os_endpoint}{oss_path}"

        # Aliyun OSS Headers
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        content_type = "image/jpeg" if local_path.lower().endswith(('.jpg', '.jpeg')
                                                                   ) else "application/octet-stream"
        if local_path.lower().endswith('.png'):
            content_type = "image/png"
        elif local_path.lower().endswith('.mp4'):
            content_type = "video/mp4"

        oss_headers = {
            "x-oss-security-token": self._sts_token['securityToken']
        }

        # Resource must start with /bucket/
        bucket_name = self._sts_token.get('bucket', self.bucket)
        resource = f"/{bucket_name}/{oss_path}"

        signature = self._sign_oss_request(
            "PUT", content_type, date_str, oss_headers, resource, self._sts_token[
                'accessKeySecret']
        )

        headers = {
            "Authorization": f"OSS {self._sts_token['accessKeyId']}:{signature}",
            "Date": date_str,
            "Content-Type": content_type,
            "User-Agent": "aliyun-sdk-android/2.9.8(Linux/PySim)",
            **oss_headers
        }

        print(f"[*] Uploading to {url}...")
        with open(local_path, "rb") as f:
            resp = requests.put(url, data=f, headers=headers)

        if resp.status_code == 200:
            print(f"[+] Upload success: {oss_path}")
            # Return the public media URL
            return f"{self.os_host_public}{oss_path}"
        else:
            print(f"[-] Upload failed: {resp.status_code}")
            print(f"[-] Response: {resp.text}")
            return None


class OssUploadSimulation:
    """
    Higher level helper to integrate with GuguClient actions.
    """

    def __init__(self, gugu_client):
        self.oss_service = OssService(gugu_client)

    def upload_and_prepare_opus(self, images: List[str], video: str = None) -> Dict[str, Any]:
        """
        Uploads actual files and returns the structure for release_post.
        """
        print("\n--- Starting REAL OSS Upload Flow ---")

        # 1. Ensure token is fetched
        if not self.oss_service._sts_token:
            self.oss_service.fetch_sts_token()

        # 2. Upload Images
        uploaded_images = []
        for img in images:
            url = self.oss_service.upload_file(img, type_prefix="article/")
            if url:
                # Extract real dimensions
                try:
                    with Image.open(img) as im:
                        width, height = im.size
                except Exception as e:
                    print(f"[-] Failed to extract dimensions for {img}: {e}")
                    width, height = 1080, 1920  # Fallback

                uploaded_images.append({
                    "width": width,
                    "height": height,
                    "url": url
                })

        # 3. Upload Video
        uploaded_video = None
        if video:
            video_url = self.oss_service.upload_file(
                video, type_prefix="article_video/")
            if video_url:
                # Mock a thumbnail or upload actual if provided
                thumb_url = self.oss_service.upload_file(
                    images[0] if images else video, type_prefix="article/")
                uploaded_video = {
                    "coverUrl": thumb_url,
                    "videoUrl": video_url,
                    "width": 1080,
                    "height": 1920,
                    "duration": 15,
                    "size": os.path.getsize(video)
                }

        print("--- Real OSS Upload Completed ---\n")

        return {
            "images": uploaded_images,
            "video": uploaded_video
        }
