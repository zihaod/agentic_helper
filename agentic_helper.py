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
        - 图片中宠物食物或宠物状态的分析
        请始终结合宠物的档案信息进行综合考虑和回答.
        当用户发送图片时，请仔细分析图片内容，并结合宠物档案提供专业建议。
        你的说话风格应当像一个真人客服，简短明了，不乱添加表情或特殊符号。

        """

        return system_prompt

    def _process_image_content(self, content_item):
        """Process image content and convert base64 data URL to proper format"""
        if content_item.get("type") == "image_url":
            image_url = content_item["image_url"]["url"]
            
            # Check if it's a base64 data URL
            if image_url.startswith("data:image"):
                # Extract just the base64 part after the comma
                base64_data = image_url.split(",", 1)[1] if "," in image_url else image_url
                return {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_data
                    }
                }
            else:
                # It's already in the right format or a regular URL
                return content_item
        
        return content_item

    def generate_response(self, chat_history, user_context):
        client = self.client

        # Add context about the pet
        context = f"#宠物档案信息\n"
        for k,v in user_context.items():
            context += f"{k}: {v}\n"

        # Construct system prompt
        messages = [{"role": "system", "content": self.system_prompt + context}]

        # Process chat history and handle image content
        for item in chat_history:
            processed_message = {
                "role": item["role"],
                "content": item["content"]
            }
            
            # Process image content if it's a list (mixed content)
            if isinstance(item["content"], list):
                processed_content = []
                for content_item in item["content"]:
                    processed_item = self._process_image_content(content_item)
                    processed_content.append(processed_item)
                processed_message["content"] = processed_content
            
            messages.append(processed_message)

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
    
    # Test with text only
    response = agent.generate_response([
        {"role": "user", "content": "你好我想问问lucky身体情况如何"}, 
        {"role": "assistant", "content": "你好宝子，稍等我帮你看看"}
    ], pet_info)
    print("Text response:", response)

    # Test with image
    img_path = "your/path/xxx.png"
    try:
        with open(img_path, "rb") as img_file:
            img_base = base64.b64encode(img_file.read()).decode("utf-8")
        
        # Test with mixed content (text + image)
        mixed_content_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请看看这张图片，分析一下lucky的状况"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base}"
                        }
                    }
                ]
            }
        ]

        response = agent.generate_response(mixed_content_messages, pet_info)
        print("Image response:", response)
        
    except FileNotFoundError:
        print("Image file not found, skipping image test")
    except Exception as e:
        print(f"Error processing image: {e}")
