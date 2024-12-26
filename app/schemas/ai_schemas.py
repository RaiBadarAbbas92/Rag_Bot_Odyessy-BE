from sqlmodel import SQLModel

class Message(SQLModel):
    id: str
    role: str
    content: str
    created_at: str

class AIRequest(SQLModel):
    query: str

class AIResponse(SQLModel):
    messages: list[Message]