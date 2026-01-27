from model.qianfan_model import get_image
from model.genai_model import get_content
import requests
import tempfile
import os
from model.oss_service import OssUploadSimulation
from model.action_service import ActionService
from model.auth_service import AuthService
from dotenv import load_dotenv
from model.account import PHONE, PASSWORD

# Load environment variables from .env file (if exists)
# Must be called BEFORE importing any modules that use environment variables
load_dotenv()


def download_image(url):
    """Downloads an image from a URL to a temporary file and returns the file path."""
    print(f"[*] Downloading image from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Create a temporary file
        # We assume it's a jpg based on the simulated return, but in real world might need to check header
        fd, path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
        print(f"[+] Image downloaded to {path}")
        return path
    except Exception as e:
        print(f"[-] Failed to download image: {e}")
        return None


def main():

    # Use ActionService since it has the business logic we need.
    actions = ActionService()

    # Check if we need to login
    if not actions.token:
        print("[*] No valid session, initiating login...")
        auth = AuthService()
        if auth.login(PHONE, PASSWORD):
            # Reload session in actions client
            actions.load_session()
        else:
            return

    # --- New Flow Start ---

    # 1. Generate Content using GenAI
    print("[*] Generating content using GenAI...")
    genai_data = get_content()
    print(f"[+] Generated Title: {genai_data['title']}")
    print(f"[+] Generated Content: {genai_data['content']}")
    print(f"[+] Generated Prompt: {genai_data['prompt']}")

    # 2. Generate Image using Qianfan
    print("[*] Generating image using Qianfan...")
    image_url = get_image(genai_data['prompt'])
    print(f"[+] Image URL: {image_url}")

    if not image_url:
        print("[-] Failed to generate image.")
        return

    # 3. Download Image Locally
    local_image_path = download_image(image_url)
    if not local_image_path:
        print("[-] Failed to download generated image.")
        return

    try:
        # 4. Real OSS Upload
        oss_sim = OssUploadSimulation(actions)
        # Use the downloaded local image
        local_images = [local_image_path]

        # Use the improved upload method that performs real network requests
        upload_results = oss_sim.upload_and_prepare_opus(local_images)

        print(
            f"[*] Upload results (URLs should be accessible): {upload_results}")

        # 5. Executing business actions (Real Post Release)
        if upload_results["images"]:
            print("[*] Releasing real post with OSS items...")

            # Task 1: Check-in (Optional, can keep it)
            actions.sign()

            # Task 2: Release Post
            actions.release_post(
                title=genai_data['title'],
                content=genai_data['content'],
                category_id="707",
                images=upload_results["images"]
            )
        else:
            print("[-] Skip post release due to upload failure.")

    finally:
        # Clean up the temporary file
        if local_image_path and os.path.exists(local_image_path):
            os.remove(local_image_path)
            print(f"[*] Temporary file {local_image_path} removed.")


if __name__ == "__main__":
    main()
