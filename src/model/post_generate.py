import glob
import datetime
from .qianfan_model import get_image
from google import genai
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

import json
import certifi
import os
import mimetypes
import base64


load_dotenv()
client = genai.Client(
    api_key=os.environ.get('GENAI_API_KEY'),
    http_options={'client_args': {'verify': certifi.where()}}
)

clientBd = OpenAI(
    base_url='https://qianfan.baidubce.com/v2',
    api_key=os.environ.get('QIANFAN_API_KEY')
)


def get_image_description(local_image_path):
    """
    步骤 2: 让 AI 看您的本地照片，生成一个极其详细的描述 Prompt
    """
    img = Image.open(local_image_path)
    # 这个 Prompt 很关键，引导它关注细节
    prompt = """
    请极其详细地描述这张照片。包括图中摩托车的型号、颜色、改装细节、停放的环境、光线情况（例如是阴天还是晴天）、如果有人物也需要描述人物的状态和穿搭以及姿势、以及照片的摄影风格（例如是手机抓拍的还是专业摄影）。
    只需输出描述段落，不要带任何前言后语，字符数量必须小于1000字。
    """
    response = client.models.generate_content(
        model='gemini-flash-latest', contents=[prompt, img])
    # 去除空格和换行
    description = response.text.replace("\n", "").replace(" ", "")
    print(f"[AI看图结果]: {description}")
    return description


def generate_human_caption(new_image_path):
    """
    步骤 4: 看这张新生成的图，写一句像真人的话
    """
    # img = Image.open(new_image_path)

    # 人设 Prompt (至关重要)
    persona_prompt = """
    你是一个玩摩托车的普通车友，现在要发一条朋友圈，生成一个标题和内容。
    标题规则：
    1. 只要一句话，非常简短，不超过 20 个字。
    2. 语气要随意、口语化、高冷一点，不要像机器人客服。
    3. 可以带点车圈黑话（比如：溜一下、操控不错、这天气绝了）。
    4. 允许不加标点符号。
    5. 绝对不要用感叹号，不要用 Emoji。
    内容规则：
    1. 只要一句话，非常简短，不超过 20 个字。
    2. 语气要随意、口语化、高冷一点，不要像机器人客服。

    输出规则：
    <title>标题<title>
    <content>内容</content>

    根据这张图，输出内容。
    """

    response = client.models.generate_content(
        model='gemini-flash-latest', contents=[persona_prompt, new_image_path])
    caption = response.text.strip()
    print(f"[生成的文案]: {caption}")
    return caption


def get_daily_image():
    # 获取当前文件所在目录的上一级目录，即 src 目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(base_dir, 'static')

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


def get_image_description2(image_path_or_url, prompt):
    print(f"Processing image: {image_path_or_url}")

    final_url = image_path_or_url
    if os.path.exists(image_path_or_url):
        mime_type, _ = mimetypes.guess_type(image_path_or_url)
        if not mime_type:
            mime_type = "image/jpeg"

        with open(image_path_or_url, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            final_url = f"data:{mime_type};base64,{base64_image}"

    response = clientBd.chat.completions.create(
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
                        "text": prompt
                    }

                ]
            }
        ],
        temperature=0.000001,
        top_p=1

    )

    print(f"{response.choices[0].message.content}")
    return response.choices[0].message.content


prompt1 = "请极其详细地描述这张照片。包括图中摩托车的型号、颜色、改装细节、停放的环境、光线情况（例如是阴天还是晴天）、如果有人物也需要描述人物的状态和穿搭以及姿势、以及照片的摄影风格（例如是手机抓拍的还是专业摄影）。\n    只需输出描述段落，不要带任何前言后语，字符数量必须小于1000字"
prompt2 = "据这张图，生成一个10个字以内的贴子标题和20字以内的贴字内容，标题（title）和内容（content），数组形式输出"


def generate_post():
    image_path = get_daily_image()
    desc2 = get_image_description2(image_path, prompt2)
    desc2 = json.loads(desc2)
    desc = get_image_description2(image_path, prompt1)
    url = get_image(desc)
    title = desc2['title']
    content = desc2['content']
    return {
        "img_url": url,
        "title": title,
        "content": content
    }


if __name__ == "__main__":
    result = generate_post()
    print(result)

    # img = get_daily_image()
    # print(f'aa{img}')

    # generate_post()
