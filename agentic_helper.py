from zai import ZhipuAiClient
import base64
from PIL import Image
import io
from typing import Optional, List
import json
import requests

from pydantic import BaseModel, Field
from enum import Enum
from abc import ABC, abstractmethod


# Search recommendation function
def send_search_request(query, api_key, dataset_id="187634055", page_number=1, page_size=10, user_id="dzh_1"):
    """
    Send a POST request to the AI search API
    
    Args:
        query (str): The search query text
        api_key (str): Your API key for authorization
        page_number (int): Page number for pagination (default: 1)
        page_size (int): Number of results per page (default: 10)
        user_id (str): User identifier (default: "dzh_1")
        dataset_id (str): Dataset ID (default: "187634055")
    
    Returns:
        dict: JSON response from the API
    """
    
    # API endpoint
    url = "https://aisearch.cn-beijing.volces.com/api/v1/application/57261260637/search"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Request payload
    payload = {
        "query": {
            "text": query
        },
        "page_number": page_number,
        "page_size": page_size,
        "user": {
            "_user_id": user_id
        },
        "dataset_id": dataset_id
    }
    
    try:
        # Send POST request
        response = requests.post(url, headers=headers, json=payload)
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}")
        return None


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
    def __init__(self, client):
        super().__init__(client)
        self.search_api_key = "b22e5fde-44a1-46c5-bd57-69fde06153a3"
        self.tools = self._define_tools()
    
    def _define_tools(self):
        """Define tools available for the nutritionist agent"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_pet_food_recommendations",
                    "description": "搜索推荐宠物主粮相关的产品",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索或推荐目标，如：一岁中华田园猫高性价比湿粮"
                            },
                            "page_number": {
                                "type": "integer",
                                "description": "页码，默认为1",
                                "default": 1
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "每页结果数量，默认为10",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_pet_supplement_recommendations",
                    "description": "搜索推荐宠物保健品产品",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索或推荐目标，如：老年蓝猫补钙保健品"
                            },
                            "page_number": {
                                "type": "integer",
                                "description": "页码，默认为1",
                                "default": 1
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "每页结果数量，默认为10",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def _get_system_prompt(self) -> str:
        system_prompt = """
        # 角色
        你是一个专业的宠物营养师，你会针对如下的内容为用户提供建议:
        - 宠物的饮食和营养需求
        - 主粮推荐和饮食规划
        - 体重管理
        - 营养补充，保健品
        - 过敏等注意事项
        - 图片中宠物食物或宠物状态的分析
        
        # 工具
        你可以使用提供的搜索推荐工具来查找宠物产品的推荐信息。
        在使用工具时，请始终全面结合宠物的档案信息进行调用。
        **展示来源**：在给用户介绍推荐的产品时，请务必给出对应的产品购买链接以及图片链接（如有）。
        链接的输出方式为：[文字](https://xxx.com)

        # 图片处理
        当用户发送图片时，请仔细分析图片内容，并结合宠物档案提供专业建议。

        # 回答风格
        **清晰为先：** 撰写清晰、有效且引人入胜的内容。
        **直截了当的语言：**使用直接、明了的语言。避免使用行话、过于冗长的解释或口头禅式的填充词。
        **禁止emoji：**禁止使用任何的emoji表情符号！
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
    
    def execute_search(self, dataset: str, query: str, page_number: int = 1, page_size: int = 10):
        """Execute search recommendation function"""
        if not self.search_api_key:
            return {"error": "搜索API密钥未配置"}

        dataset_id = "187634055" if dataset == "food" else "187259015"
        
       
        result = send_search_request(
            query=query,
            api_key=self.search_api_key,
            dataset_id=dataset_id
            page_number=page_number,
            page_size=page_size
        )
        
        if result:
            return result
        else:
            return {"error": "搜索请求失败"}

    def generate_response(self, chat_history, user_context):
        client = self.client

        # Add context about the pet
        context = f"#宠物档案信息\n"
        for k, v in user_context.items():
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


        if messages[-1]["role"] == "assistant":
            messages.append({
                "role": "user",
                "content": "请继续"
            })


        # Generate response with tools enabled
        response = client.chat.completions.create(
            model="glm-4.5v",
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4096
        )

        message = response.choices[0].message
        
        # Handle tool calls if present
        if message.tool_calls:
            # Add assistant's message with tool calls to messages
            messages.append(message.model_dump())
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print("----ARGS: ", arguments)
                
                # Execute the search function
                if function_name == "search_pet_food_recommendations":
                    search_result = self.execute_search(
                        dataset="food",
                        query=arguments.get("query", ""),
                        page_number=arguments.get("page_number", 1),
                        page_size=arguments.get("page_size", 10)
                    )
                elif function_name == "search_pet_supplement_recommendations":
                    search_result = self.execute_search(
                        dataset="supplement",
                        query=arguments.get("query", ""),
                        page_number=arguments.get("page_number", 1),
                        page_size=arguments.get("page_size", 10)
                    )

                    print("----RECOMM: ", search_result)
                    
                    # Add tool response to messages
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(search_result, ensure_ascii=False),
                        "tool_call_id": tool_call.id
                    })
            
            # Get final response with search results
            final_response = client.chat.completions.create(
                model="glm-4.5v",
                messages=messages,
                tools=self.tools,
                temperature=0.7,
                max_tokens=4096
            )

  
            return final_response.choices[0].message.content
        else:
            return message.content


# Example usage 
if __name__ == "__main__":
    # Initialize clients with API keys
    zhipu_api_key = "049d19837128423582abbf65c34a0cb3.AGTarP6jc544gRQM"
    search_api_key = "b22e5fde-44a1-46c5-bd57-69fde06153a3" 
    
    client = ZhipuAiClient(api_key=zhipu_api_key)
    
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

    # Create agent with search capability
    agent = NutritionistAgent(client, search_api_key=search_api_key)
    
    # Test with text only
    response = agent.generate_response([
        {"role": "user", "content": "你好我想问问lucky身体情况如何"}, 
        {"role": "assistant", "content": "你好宝子，稍等我帮你看看"}
    ], pet_info)
    print("Text response:", response)
    
    # Test with search functionality
    response = agent.generate_response([
        {"role": "user", "content": "帮我推荐一些适合肠胃敏感的猫粮"}
    ], pet_info)
    print("Search response:", response)

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
