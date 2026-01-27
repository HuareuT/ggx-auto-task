from .gugu_client import GuguClient


class ActionService(GuguClient):

    def sign(self):
        if not self.token:
            print("[-] No token available. Please login first.")
            return False

        print("[*] Performing sign POST...")
        path = "/gugux-services-activity-api/app/sign"
        resp = self.post(path)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') or data.get('code') == 200:
                print("[+] Sign in successful!")
                self.save_session()
                return True
            elif data.get('msg') == "今日已签到":
                print("[!] Already signed in today.")
                self.save_session()
                return True
            else:
                print(f"[-] Sign in failed: {data.get('msg')}")
                if data.get('code') == 401 or data.get('guCode') == 401:
                    print("[!] Token expired or invalid.")
                    self.token = None
                    return False
        return False

    def release_post(self, title, content, category_id="707", images=None):
        """
        Releases a forum post (opus).
        :param title: Post title
        :param content: Post content
        :param category_id: Category ID (default "707")
        :param images: List of image dicts with 'url', 'width', 'height'
        """
        if not self.token:
            print("[-] No token available. Please login first.")
            return False

        path = "/gugux-services-forumsphere-api/app/forumsphere/opus/release"
        print(f"[*] Releasing post: {title}...")

        if images is None:
            images = [
                {
                    "height": 4032,
                    "url": "https://media.caigetuxun.com/multi/article/3956043558293610315/74220832b764e7b7d06aad1d.jpeg",
                    "width": 3024
                }
            ]

        cover = images[0] if images else None

        payload = {
            "addressName": None,
            "atUserIds": [],
            "categoryId": category_id,
            "circleId": "",
            "circleInfo": None,
            "circleOnlyFlag": "0",
            "content": content,
            "cover": cover,
            "images": images,
            "latitude": 0.0,
            "locationTrackId": "",
            "longitude": 0.0,
            "opusType": "1",
            "originalFlag": False,
            "recommendedCity": "",
            "title": title,
            "topics": [],
            "video": None
        }

        resp = self.post(path, json_data=payload)
        print(f"[*] Release Post Response Status: {resp.status_code}")
        print(f"[*] Release Post Response Body: {resp.text}")

        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') or data.get('code') == 200:
                print("[+] Post released successfully!")
                self.save_session()
                return True
            else:
                print(f"[-] Failed to release post: {data.get('msg')}")
        return False

    # 帖子列表
    def list_posts(self,  category_id="706", is_top=True):

        if not self.token:
            print("[-] No token available. Please login first.")
            return False

        path = f"/gugux-services-forumsphere-api/app/forumsphere/opus/list?categoryId={category_id}&getTop={is_top}&getNum=10"
        resp = self.get(path)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                print("[+] Post list successfully!")
                return data.get('data')
            else:
                print(f"[-] Failed to list post: {data.get('msg')}")
        return False

      # 帖子点赞
    def like_post(self, opus_Id=None, category_id=None):

        if not self.token:
            print("[-] No token available. Please login first.")
            return False

        path = f"/gugux-services-forumsphere-api/app/forumsphere/opus/like"
        payload = {
            "action": 1,
            "categoryId": category_id,
            "opusId": opus_Id,
            "traceInfo": None
        }

        resp = self.post(path, json_data=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                print("[+] Post liked successfully!")
                return True
            else:
                print(f"[-] Failed to like post: {data.get('msg')}")
        return False

      # 帖子收藏
    def collect_post(self, opus_Id=None, category_id=None):

        if not self.token:
            print("[-] No token available. Please login first.")
            return False

        path = f"/gugux-services-forumsphere-api/app/forumsphere/opus/collect"
        payload = {
            "action": 1,
            "categoryId": category_id,
            "opusId": opus_Id,
            "traceInfo": None
        }

        resp = self.post(path, json_data=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                print("[+] Post collected successfully!")
                return True
            else:
                print(f"[-] Failed to collect post: {data.get('msg')}")
        return False

      # 帖子评论
    def comment_post(self, opus_Id=None,):

        if not self.token:
            print("[-] No token available. Please login first.")
            return False

        path = f"/gugux-services-forumsphere-api/app/forumsphere/comment/comment"
        payload = {
            "opusId": opus_Id,
            "images": None,
            "mainCommentId": 0,
            "contents": "帅！"
        }

        resp = self.post(path, json_data=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                print("[+] Post commented successfully!")
                return True
            else:
                print(f"[-] Failed to comment post: {data.get('msg')}")
        return False
