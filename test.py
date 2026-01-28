import mimetypes
import base64
from openai import OpenAI
import os
from dotenv import load_dotenv
import glob
import datetime

load_dotenv()

client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key=os.environ.get('QIANFAN_API_KEY')
)
# api_key='bce-v3/ALTAK-Hn7D61iovWJgLDoOc8nl1/5b5d7ad6b94bd950cf7248d6c837419c8ac9990c'


def get_daily_image():
    # 获取当前文件所在目录的上一级目录，即 src 目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'src/static')
    # print(base_dir)

    # 获取所有图片文件
    extensions = ['*.png', '*.jpg', '*.jpeg']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(static_dir, ext)))

    if not images:
        print("Warning: No images found in static directory. Using default.")
        return "./example.jpg"

    images.sort()

    # 根据当天的日期选择一张图片
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    image_index = day_of_year % len(images)

    selected_image = images[image_index]
    print(selected_image)
    print(
        f"[Daily Image] Selected: {os.path.basename(selected_image)} (Day {day_of_year})")
    return selected_image


def get_content(image_path_or_url):
    print(f"Processing image: {image_path_or_url}")

    final_url = image_path_or_url
    if os.path.exists(image_path_or_url):
        mime_type, _ = mimetypes.guess_type(image_path_or_url)
        if not mime_type:
            mime_type = "image/jpeg"

        with open(image_path_or_url, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            final_url = f"data:{mime_type};base64,{base64_image}"

    response = client.chat.completions.create(
        model="qianfan-ocr",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": final_url
                        }
                    },
                    {
                        "type": "text",
                        "text": "请极其详细地描述这张照片。包括图中摩托车的型号、颜色、改装细节、停放的环境、光线情况（例如是阴天还是晴天）、如果有人物也需要描述人物的状态和穿搭以及姿势、以及照片的摄影风格（例如是手机抓拍的还是专业摄影）。\n    只需输出描述段落，不要带任何前言后语，字符数量必须小于1000字"
                    }

                ]
            }
        ],
        temperature=0.000001,
        top_p=1

    )

    print(f"{response}")
    return response.choices[0].message.content


if __name__ == '__main__':
    img = get_daily_image()
    cot = get_content(img)
    print(cot)
