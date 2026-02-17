from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

password=os.getenv("password")
DATABASE_URL = f"postgresql+psycopg2://postgres:{password}@localhost:8000/Tax"

engine=create_engine(DATABASE_URL,echo=True)


Sessionlocal=sessionmaker(bind=engine,expire_on_commit=False)
