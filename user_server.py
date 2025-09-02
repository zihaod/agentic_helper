from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import httpx
import asyncio
from datetime import datetime

import nest_asyncio
from pyngrok import ngrok


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage
chat_history = []
SERVER_URL = "http://localhost:8001"

@app.get("/", response_class=HTMLResponse)
async def user_chat(request: Request):
    return templates.TemplateResponse("user_chat.html", {"request": request, "messages": chat_history})

@app.post("/send_message")
async def send_message(request: Request):
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
        
        # Send to server for processing
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{SERVER_URL}/receive_message", 
                                json={"message": message})
        except:
            pass  # Server might be offline
    
    return {"status": "sent"}

@app.post("/receive_response")
async def receive_response(request: Request):
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
    
    return {"status": "received"}

@app.get("/get_messages")
async def get_messages():
    return {"messages": chat_history}



def interactive_url_setup():
    """Interactive setup for server URL"""
    global SERVER_URL
    
    print("\n" + "="*50)
    print("🔗 URL CONFIGURATION")
    print("="*50)
    print("Please start your server_server.py and get its ngrok URL")
    print("Then enter it below:")
    
    while True:
        url = input("\nEnter Staff Server URL (https://xxx.ngrok-free.app): ").strip()
        if url.startswith("https://") and "ngrok" in url:
            SERVER_URL = url
            print(f"✅ Staff Server URL set to: {SERVER_URL}")
            break
        else:
            print("❌ Please enter a valid ngrok HTTPS URL")
    
    print("="*50)


if __name__ == "__main__":
    #uvicorn.run(app, host="0.0.0.0", port=8000)
    auth_token = "328506F8MSDrngMzSW9iVNbO8x0_3h5YdfJYVqpgL3p6EUCuj"

    # Set the authtoken
    ngrok.set_auth_token(auth_token)

    ngrok_tunnel = ngrok.connect(8000)
    print('Public URL:', ngrok_tunnel.public_url)

    interactive_url_setup()
    
    nest_asyncio.apply()

    uvicorn.run(app, port=8000)
