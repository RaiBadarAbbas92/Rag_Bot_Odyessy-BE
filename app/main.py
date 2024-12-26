# from app.routes import  chat

# from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# from fastapi import FastAPI, Depends, HTTPException, status
# from sqlmodel import SQLModel, Field, Session, create_engine, select
# from pydantic import BaseModel
# from passlib.context import CryptContext
# from jose import JWTError, jwt
# from datetime import datetime, timedelta

# # App setup


# app = FastAPI()


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # replace with your frontend URL
#     allow_credentials=True,
#     allow_methods=["*"],  # allows all methods, adjust as needed
#     allow_headers=["*"],  # allows all headers, adjust as needed
# )

# app.include_router(chat.ai_router)

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

# def start():
#     import uvicorn
#     uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)



from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.routes import  chat
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# App setup
app = FastAPI()
engine = create_engine(DATABASE_URL)

# Models
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str
    password_hash: str

SQLModel.metadata.create_all(engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Utility functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Dependency
def get_session():
    with Session(engine) as session:
        yield session

# Signup
@app.post("/signup")
def signup(username: str, email: str, password: str, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "User created successfully", "user_id": user.id}

# Login
class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/login", response_model=Token)
def login(username: str, password: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
    
app.include_router(chat.ai_router)


def start():
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
