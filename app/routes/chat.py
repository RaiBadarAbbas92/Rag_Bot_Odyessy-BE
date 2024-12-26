from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter , Depends
from langchain_community.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from uuid import uuid4
import os
import json  # Missing import for JSON operations
# from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, Session, create_engine
from typing import Optional

load_dotenv()

app = FastAPI()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# Define User model

# Define Chatbot model
class Chatbot(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    description: str
    tone: str
    personality: str
    index_file_path: str
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

SQLModel.metadata.create_all(engine)

# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session

# Initialize LLM and memory
llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
memory = ConversationBufferWindowMemory(k=5)

# Function to create a persona-based prompt
def create_prompt(persona_settings, user_query):
    template = """
    You are {persona_name}, {description}.
    Your personality is {personality}, and your tone is {tone}.
    Respond to the user query below:

    User: {user_query}
    """
    prompt = PromptTemplate(
        input_variables=["persona_name", "description", "personality", "tone", "user_query"],
        template=template,
    )
    return prompt.format(
        persona_name=persona_settings["name"],
        description=persona_settings["description"],
        personality=persona_settings["personality"],
        tone=persona_settings["tone"],
        user_query=user_query,
    )

# AI Router
ai_router = APIRouter(prefix="/ai")

@ai_router.post("/upload_file/{name}/{description}/{tone}/{personality}")
async def upload_file(name: str, description: str, tone: str, personality: str, file: UploadFile = File(...)):
    chatbot_id = str(uuid4())

    try:
        # Save the uploaded file
        content = await file.read()
        text = content.decode("utf-8")

        chatbot_dir = f"chatbots/{chatbot_id}"
        os.makedirs(chatbot_dir, exist_ok=True)

        temp_file_path = os.path.join(chatbot_dir, "source.txt")
        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(text)

        loader = TextLoader(temp_file_path)
        embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        index_creator = VectorstoreIndexCreator(embedding=embedding, text_splitter=text_splitter)
        index = index_creator.from_loaders([loader])
        embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        index_creator = VectorstoreIndexCreator(embedding=embedding, text_splitter=text_splitter)
        index = index_creator.from_loaders([loader])

        # Save chatbot metadata
        metadata = {
            "id": chatbot_id,
            "name": name,
            "description": description,
            "tone": tone,
            "personality": personality,
            "index_file": temp_file_path,
        }
        with open(os.path.join(chatbot_dir, "metadata.json"), "w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file)

        return {"message": "Chatbot created successfully", "chatbot_id": chatbot_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the uploaded file: {str(e)}")

@ai_router.post("/ask/{chatbot_id}")
async def ask_question(chatbot_id: str, question: str):
    chatbot_dir = f"chatbots/{chatbot_id}"

    if not os.path.exists(chatbot_dir):
        raise HTTPException(status_code=404, detail="Chatbot not found")

    # Load chatbot metadata
    metadata_file = os.path.join(chatbot_dir, "metadata.json")
    if not os.path.isfile(metadata_file):
        raise HTTPException(status_code=404, detail="Metadata not found")

    with open(metadata_file, "r", encoding="utf-8") as f:
        chatbot_metadata = json.load(f)

    # Create a persona-based prompt
    persona_settings = {
        "name": chatbot_metadata["name"],
        "description": chatbot_metadata["description"],
        "personality": chatbot_metadata.get("personality", "friendly"),
        "tone": chatbot_metadata["tone"],
    }
    prompt = create_prompt(persona_settings, question)

    # Reload the index
    index_file_path = chatbot_metadata["index_file"]
    loader = TextLoader(index_file_path)
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    index_creator = VectorstoreIndexCreator(embedding=embedding, text_splitter=text_splitter)
    index = index_creator.from_loaders([loader])

    # Query the index
    response = index.query(prompt, llm=llm, memory=memory)
    return {"response": response}

# Endpoint to get a list of all chatbots
@ai_router.get("/chatbots")
async def get_all_chatbots():
    chatbots_dir = "chatbots"
    chatbots_list = []

    if not os.path.exists(chatbots_dir):
        return {"chatbots": []}

    for chatbot_id in os.listdir(chatbots_dir):
        metadata_file = os.path.join(chatbots_dir, chatbot_id, "metadata.json")
        if os.path.isfile(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                chatbots_list.append(json.load(f))

    return {"chatbots": chatbots_list}

@ai_router.get("/chatboards")
async def get_all_chatboards(session: Session = Depends(get_session)):
        chatboards = session.query(Chatbot).all()
        return {"chatboards": chatboards}