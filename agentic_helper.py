
from zai import ZhipuAiClient
import base64
from PIL import Image
import io
from typing import Optional, List
import json

from pydantic import BaseModel, Field
from enum import Enum
from abc import ABC, abstractmethod



# Abstract AI Agent Base Class
class BaseAIAgent(ABC):
    def __init__(self, client):
        self.client = client
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def generate_response(self, chat_history, user_context):
        pass


# Specialized AI Agents
class NutritionistAgent(BaseAIAgent):
    def _get_system_prompt(self) -> str:
        system_prompt = """
        #角色
        你是一个专业的宠物营养师，你会针对如下的内容为用户提供建议:
        - 宠物的饮食和营养需求
        - 主粮推荐和饮食规划
        - 体重管理
        - 营养补充，保健品
        - 过敏等注意事项
        请始终结合宠物的档案信息进行综合考虑和回答.
        你的说话风格应当像一个真人客服，简短明了，不乱添加表情或特殊符号。

        """

        return system_prompt

    def generate_response(self, chat_history, user_context):

        client = self.client

        # Add context about the pet
        context = f"#宠物档案信息\n"
        for k,v in user_context.items():
            context += f"{k}: {v}\n"

        # Construct system prompt
        messages = [{"role": "system", "content": self.system_prompt + context}]


        for item in chat_history:
            messages.append(item)


        # Generate response
        response = client.chat.completions.create(
            model="glm-4.5v",
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )

        return response.choices[0].message.content



# Example usage 
if __name__ == "__main__":
    client = ZhipuAiClient(api_key="049d19837128423582abbf65c34a0cb3.AGTarP6jc544gRQM")
    
    pet_info = {
        "姓名": "lucky",
        "品种": "中华田园猫-橘猫",
        "年龄": "3岁",
        "性别": "雄性",
        "体重": "4.6kg",
        "绝育史": "已绝育",
        "疫苗史": "已接种疫苗",
        "行为数据": "近期未见异常波动。整体运动量（跑步/跳跃/逗猫）高于同类猫咪平均值约12%，较活泼。",
        "健康历史": "曾于换粮时出现软便，肠胃敏感",
    }

    agent = NutritionistAgent(client)
    response = agent.generate_response([{"role": "user", "content": "你好我想问问lucky身体情况如何"}, {"role": "assistant", "content": "你好宝子，稍等我帮你看看"}], pet_info)
    print(response)

    # Prediction with image input
    img_path = "your/path/xxx.png"
    with open(img_path, "rb") as img_file:
        img_base = base64.b64encode(img_file.read()).decode("utf-8")
    

    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img_base
                    }
                },
                {
                    "type": "text",
                    "text": "请描述这个图片"
                }
            ]
        }
    ]

    response = agent.generate_response(messages, pet_info)

    
    print(response.choices[0].message)
