from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from interactive_story_tl import format_user_initial, user_proxy, story_agent
import uvicorn

app = FastAPI()


class ChatInitiation(BaseModel):
    genre: str
    initial_message: Optional[str] = None
    seed: Optional[int] = None


@app.post("/initiate_chat")
async def initiate_chat(chat_initiation: ChatInitiation):
    # Assuming user_proxy and story_agent are globally available and initialized
    try:
        initial_message = format_user_initial(
            f"User: Genre - {chat_initiation.genre}")
        user_proxy.initiate_chat(
            recipient=story_agent,
            message=initial_message,
            clear_history=True,
        )
        return {"status": "Chat initiated successfully", "message": initial_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
