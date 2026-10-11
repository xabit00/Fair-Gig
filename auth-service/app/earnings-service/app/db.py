import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fairgig")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
