from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import httpx
from datetime import datetime

import nest_asyncio
from pyngrok import ngrok

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage
chat_history = []
pending_messages = []
USER_URL = "http://localhost:8000"

@app.get("/", response_class=HTMLResponse)
async def server_chat(request: Request):
    return templates.TemplateResponse("server_chat.html", {
        "request": request, 
        "messages": chat_history,
        "pending": pending_messages
    })

@app.post("/receive_message")
async def receive_message(request: Request):
    data = await request.json()
    message = data.get("message", "").strip()
    
    if message:
        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        chat_history.append(user_msg)
        
        # Add to pending messages for staff review
        pending_msg = {
            "content": message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "ai_response": ""
        }
        pending_messages.append(pending_msg)
    
    return {"status": "received"}

@app.post("/generate_response")
async def generate_response(request: Request):
    data = await request.json()
    message_index = data.get("index", 0)
    
    if 0 <= message_index < len(pending_messages):
        # Simple AI response generation (you can integrate GLM-4.5V here)
        user_message = pending_messages[message_index]["content"]
        
        # Basic response generation (replace with GLM-4.5V integration)
        ai_response = f"AI Response to: '{user_message}'. This is where you would integrate GLM-4.5V model response."
        
        pending_messages[message_index]["ai_response"] = ai_response
    
    return {"status": "generated"}

@app.post("/send_response")
async def send_response(request: Request):
    data = await request.json()
    message_index = data.get("index", 0)
    edited_response = data.get("response", "").strip()
    
    if 0 <= message_index < len(pending_messages) and edited_response:
        # Add server response to history
        server_msg = {
            "role": "server",
            "content": edited_response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        chat_history.append(server_msg)
        
        # Send response back to user
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{USER_URL}/receive_response", 
                                json={"response": edited_response})
        except:
            pass  # User server might be offline
        
        # Remove from pending
        pending_messages.pop(message_index)
    
    return {"status": "sent"}

@app.get("/get_data")
async def get_data():
    return {
        "messages": chat_history,
        "pending": pending_messages
    }

if __name__ == "__main__":
    auth_token = "327rd97T1gGUvcX2xw51UKU4JG7_4AVEKTw7CAMoH2MNijqwd"

    # Set the authtoken
    ngrok.set_auth_token(auth_token)

    ngrok_tunnel = ngrok.connect(8001)
    print('Public URL:', ngrok_tunnel.public_url)

    nest_asyncio.apply()

    uvicorn.run(app, port=8001)
