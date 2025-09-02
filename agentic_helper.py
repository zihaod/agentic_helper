
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


        role_mapping = {"user": "用户", "assistant": "营养师"}

        history_str = ""
        for item in chat_history:
            role = item['role']
            content = item['content']
            history_str += f"{role_mapping[role]}: {content} \n"


        generation_prompt = f"""#对话历史
        {history_str}

        #任务
        现在请你根据宠物档案信息和对话历史，以「营养师」的视角，继续发言。你的目的是为了询问并解决用户的相关宠物需求。
        请保持真人般的说话风格，并直接输出你的回复发言，不要生成任何多余内容。
        """

        messages.append({"role": "user", "content": generation_prompt})


        # Generate response
        response = client.chat.completions.create(
            model="glm-4.5v",
            messages=messages,
            temperature=0.7,
            max_tokens=4096
        )

        return response.choices[0].message.content

# Example usage (commented out for import purposes)
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
