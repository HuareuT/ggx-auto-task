from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url='https://qianfan.baidubce.com/v2/musesteamer',
    api_key=os.environ.get('QIANFAN_API_KEY')
)
# api_key='bce-v3/ALTAK-Hn7D61iovWJgLDoOc8nl1/5b5d7ad6b94bd950cf7248d6c837419c8ac9990c'


def get_image(prompt):
    response = client.images.generate(
        model="musesteamer-air-image",
        prompt=prompt,
        size="1152x864",
        n=1,
        extra_body={
            "prompt_extend": True
        }
    )
    return response.data[0].url
    # return "http://qianfan-modelbuilder-img-gen.bj.bcebos.com/musesteamer-air-image/30fb0c3e1d714b0b99e385e972eb40dc/30fb0c3e1d714b0b99e385e972eb40dc/img-2324fb7a-8a13-44a1-63e0-6bb09f2ee7e0.jpeg?authorization=bce-auth-v1%2FALTAKEDe5Wum0DnGzeUzScVC94%2F2026-01-22T08%3A13%3A32Z%2F86400%2Fhost%2F48d91228797a038a8a8af4501f9f7d4704754ecea780d4e32cd4cd096f6b9491"


if __name__ == '__main__':
    print(get_image("一个穿着白色衣服的女子"))
