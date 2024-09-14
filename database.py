from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text
from databases import Database
from sqlalchemy.orm import sessionmaker


# PostgreSQL database connection details
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/chat"

# Database setup using SQLAlchemy and PostgreSQL
database = Database(DATABASE_URL)
metadata = MetaData()

# Define messages table
messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String),
    Column("message", Text),
)

# Create an engine to connect to PostgreSQL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure that the database table is created
metadata.create_all(engine)