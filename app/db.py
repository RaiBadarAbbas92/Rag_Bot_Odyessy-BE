from sqlmodel import SQLModel, Session, create_engine
from app import config 

# Create the SQLAlchemy engine
engine = create_engine(config.DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session