from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import httpx
from datetime import datetime
import base64

import nest_asyncio
from pyngrok import ngrok

# Import the agent components
from agentic_helper import NutritionistAgent
from zai import ZhipuAiClient

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage
chat_history = []
USER_URL = "https://qialg2.ngrok.app"  # Will be updated by interactive setup

# Initialize the AI client and agent
client = ZhipuAiClient(api_key="049d19837128423582abbf65c34a0cb3.AGTarP6jc544gRQM")
agent = NutritionistAgent(client)

# Pet information - you might want to make this configurable per user
pet_info = {
    "姓名": "笨笨",
    "品种": "巴哥犬",
    "年龄": "13岁",
    "性别": "雌性",
    "体重": "9.8kg",
    "绝育史": "已绝育",
    "疫苗史": "已接种疫苗",
    "行为数据": "近期未见异常波动。整体运动量（跑步/跳跃/逗猫）低于同类狗狗平均值约5%",
    "健康历史": "曾患皮肤病，无其它慢性疾病",
}

@app.get("/", response_class=HTMLResponse)
async def server_chat(request: Request):
    return templates.TemplateResponse("server_chat.html", {"request": request})

@app.post("/receive_message")
async def receive_message(request: Request):
    """Receive message from user server"""
    data = await request.json()
    message = data.get("message")
    
    if message:
        # Add user message to history (message is already formatted correctly)
        chat_history.append(message)
        
        # Log message info
        if isinstance(message.get("content"), list):
            has_image = any(item.get("type") == "image_url" for item in message["content"])
            has_text = any(item.get("type") == "text" for item in message["content"])
            log_msg = f"Received message - Text: {has_text}, Image: {has_image}"
        else:
            log_msg = f"Received text message: {message['content'][:50]}..."
        
        print(log_msg)
    
    return {"status": "received"}

@app.post("/generate_ai_response")
async def generate_ai_response(request: Request):
    """Generate AI response for the given message using NutritionistAgent"""
    print("=== Generate AI Response Called ===")
    
    try:
        data = await request.json()
        user_message = data.get("message")
        print(f"Received user_message: {type(user_message)}")
        print(f"Current chat_history length: {len(chat_history)}")
        
        # Print last few messages for debugging
        print("Last 3 messages in chat_history:")
        for i, msg in enumerate(chat_history[-3:]):
            content_preview = ""
            if isinstance(msg.get("content"), str):
                content_preview = msg["content"][:50]
            elif isinstance(msg.get("content"), list):
                text_items = [item.get("text", "") for item in msg["content"] if item.get("type") == "text"]
                content_preview = " ".join(text_items)[:50]
                has_image = any(item.get("type") == "image_url" for item in msg["content"])
                if has_image:
                    content_preview += " [+Image]"
            
            print(f"  {len(chat_history)-3+i}: {msg['role']} - {content_preview}...")
        
        if not user_message:
            print("No user message provided")
            return {"response": ""}
        
        # Convert chat_history format to match agent expectations
        # Filter out timestamp and convert role names
        agent_history = []
        for i, msg in enumerate(chat_history):
            role = msg["role"]
            if role == "server":
                role = "assistant"
            
            agent_history.append({
                "role": role,
                "content": msg["content"]
            })
        
        # Print the exact history that will be sent to the agent
        print("=== EXACT AGENT HISTORY ===")
        for i, item in enumerate(agent_history):
            content_str = ""
            if isinstance(item["content"], str):
                content_str = item["content"][:100]
            elif isinstance(item["content"], list):
                content_parts = []
                for part in item["content"]:
                    if part.get("type") == "text":
                        content_parts.append(f"Text: {part.get('text', '')[:50]}")
                    elif part.get("type") == "image_url":
                        content_parts.append("Image: [base64 data]")
                content_str = ", ".join(content_parts)
            
            print(f"{i}: {item['role']} -> {content_str}")
        print("=== END AGENT HISTORY ===")
        
        # Generate response using the nutritionist agent
        ai_response = agent.generate_response(
            chat_history=agent_history,
            user_context=pet_info
        )
        
        return {"response": ai_response}
        
    except Exception as e:
        print(f"ERROR in generate_ai_response: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response
        ai_response = "服务器繁忙，请稍后再试。"
        return {"response": ai_response}

@app.post("/send_response")
async def send_response(request: Request):
    """Send staff response to user"""
    data = await request.json()
    response = data.get("response", "").strip()
    
    if response:
        # Add server response to history
        server_msg = {
            "role": "server",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        chat_history.append(server_msg)
        
        # Send response back to user
        try:
            print(f"Sending response to user at {USER_URL}: {response}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                result = await client.post(f"{USER_URL}/receive_response", 
                                          json={"response": response})
                print(f"Response sent successfully. Status: {result.status_code}")
        except Exception as e:
            print(f"Error sending response to user: {e}")
            return {"status": "error", "message": str(e)}
    
    return {"status": "sent"}

@app.get("/get_chat_history")
async def get_chat_history():
    """Get all chat messages"""
    return {"messages": chat_history}

def interactive_url_setup():
    """Interactive setup for server URL"""
    global USER_URL
    
    print("\n" + "="*50)
    print("🔗 URL CONFIGURATION")
    print("="*50)
    print("Please start your user_server.py and get its ngrok URL")
    print("Then enter it below:")
    
    while True:
        url = input("\nEnter User Server URL (https://xxx.ngrok-free.app): ").strip()
        if url.startswith("https://") and "ngrok" in url:
            USER_URL = url
            print(f"✅ User Server URL set to: {USER_URL}")
            break
        else:
            print("❌ Please enter a valid ngrok HTTPS URL")
    
    print("="*50)

if __name__ == "__main__":
    auth_token = "327rd97T1gGUvcX2xw51UKU4JG7_4AVEKTw7CAMoH2MNijqwd"

    # Set the authtoken
    ngrok.set_auth_token(auth_token)

    #ngrok_tunnel = ngrok.connect(8001)
    ngrok_tunnel = ngrok.connect(8001, domain="qialg.ngrok.app")
        
    print('Server Public URL:', ngrok_tunnel.public_url)

    #interactive_url_setup()

    nest_asyncio.apply()

    uvicorn.run(app, port=8001)
