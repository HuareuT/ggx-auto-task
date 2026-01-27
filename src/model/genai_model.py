import certifi
from google import genai
from datetime import datetime
import re
import os
from dotenv import load_dotenv

load_dotenv()

# api_key='AIzaSyBIpvPJF6Po4HPfM7YacNBL4JUXMM7BZO4',
client = genai.Client(
    api_key=os.environ.get('GENAI_API_KEY'),
    http_options={'client_args': {'verify': certifi.where()}}
)


def parse_ride_text(text):
    """
    解析包含title、prompt标签的骑行文本字符串

    参数:
        text (str): 需要解析的原始字符串

    返回:
        dict: 包含title、prompt、content三个键的字典
    """
    # 定义正则表达式，兼容</title>和<title>结尾的笔误情况
    title_pattern = r'<title>(.*?)</?title>'
    prompt_pattern = r'<prompt>(.*?)</?prompt>'

    # 提取title内容，处理匹配不到的情况
    title_match = re.search(title_pattern, text, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    # 提取prompt内容，处理匹配不到的情况
    prompt_match = re.search(prompt_pattern, text, re.DOTALL)
    prompt = prompt_match.group(1).strip() if prompt_match else ""

    # 提取正文内容：先移除title和prompt标签及内容，再清理多余空白
    content = re.sub(title_pattern, '', text, flags=re.DOTALL)
    content = re.sub(prompt_pattern, '', content, flags=re.DOTALL)
    # 将多个换行/空格/制表符替换为单个空格，最后去除首尾空白
    content = re.sub(r'\s+', ' ', content).strip()

    return {
        "title": title,
        "prompt": prompt,
        "content": content
    }


def get_content():
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().month
    season = "春" if 3 <= month <= 5 else "夏" if 6 <= month <= 8 else "秋" if 9 <= month <= 11 else "冬"
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""
        你是一个真实的摩托车玩家，性格洒脱，平时喜欢在社交圈分享骑行生活。
        现在是{season}季，今天是{today}。请根据当前季节和环境，写一条非常有生活感、不做作的动态。

        要求：
        1. 语气：像个真人在说话。多用短句、语气词，可以用一点自嘲或真实的感慨。绝对不要像机器人那样列提纲（如：1.xx 2.xx）。
        2. 内容：从以下角度选一个点切入：
           - 此时此地的骑行感受（比如冬天的风像刀子，或者春天第一场跑山的畅快）。
           - 车辆的某个细节（比如刚洗完车亮晶晶的轮毂，或者链条的油渍）。
           - 骑行路上的一个小发现（一个好喝的咖啡档、一段被落叶覆盖的小路）。
           - 关于“为什么要骑车”的矫情或硬核瞬间。
        3. 细节：要有具体的画面感。不要说“注意安全”，要说“风太大，压弯的时候感觉要把我整个人掀翻”。
        4. 禁忌：禁止出现“大家好”、“今天我来分享”、“总而言之”、“建议大家”这类明显的AI说明性语言。
        5. 长度：80-120字左右，排版要随性，带1-2个当下的心情emoji即可。
        6. 输出格式：
           - 第一部分：直接是正文内容。
           - 第二部分：用 <title>标题内容</title> 包裹一个吸引人的、像人类起出来的标题（不要太公关感）。
           - 第三部分：用 <prompt>提示词</prompt> 包裹一段用于文生图的英文Prompt。描述要写实、高级、电影感，画面要符合你写的这段话的意境，禁止出现AI感严重的构图描述。
           - 禁止输出任何其他的解释文字。

        车型参考：复古巡航。
        """
    )

    return parse_ride_text(response.text)

    # return {'title': '冬季骑行的“命门”，这几个数值你盯紧了吗？', 'prompt': 'A classic heavy cruiser motorcycle parked on a quiet frost-covered asphalt road during a cold winter morning, soft golden sunrise light, realistic textures, steam rising from the exhaust, cinematic atmosphere, 8k resolution.', 'content': '【2026-01-22 摩友安全说】 冬季安全预警💡：这两天冷空气透骨，早上出门发现胎压掉得厉害。我的大巡航平时习惯冷胎2.4/2.6，今天一测直接掉到2.1。千万别直接暴力起步，冬天柏油路硬得像钢板，抓地力大打折扣。建议起步先温和骑几公里，等胎温上来再放开。特别是过立交桥阴影处的霜冻路段，一定要提前降速，别盲目压弯。岁数大了，骑帅不骑快，平安进家门才是硬道理！🚦✨ #摩托车 #冬季骑行 #安全第一 #巡航大叔的日常'}


if __name__ == "__main__":
    result = get_content()
    print(result)
