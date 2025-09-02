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
USER_URL = "http://localhost:8000"  # Will be updated by interactive setup

@app.get("/", response_class=HTMLResponse)
async def server_chat(request: Request):
    return templates.TemplateResponse("server_chat.html", {"request": request})

@app.post("/receive_message")
async def receive_message(request: Request):
    """Receive message from user server"""
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
        print(f"Received message from user: {message}")
    
    return {"status": "received"}

@app.post("/generate_ai_response")
async def generate_ai_response(request: Request):
    """Generate AI response for the given message"""
    data = await request.json()
    user_message = data.get("message", "").strip()
    
    if user_message:
        # Simple AI response generation (replace with GLM-4.5V integration)
        # For now, this is a placeholder response
        ai_response = f"AI Response to: '{user_message}'. This is where you would integrate GLM-4.5V model response."
        
        # TODO: Replace this with actual GLM-4.5V API call
        # Example:
        # ai_response = await call_glm_api(user_message)
        
        print(f"Generated AI response for: {user_message}")
        return {"response": ai_response}
    
    return {"response": ""}

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

    ngrok_tunnel = ngrok.connect(8001)
    print('Server Public URL:', ngrok_tunnel.public_url)

    interactive_url_setup()

    nest_asyncio.apply()

    uvicorn.run(app, port=8001)
