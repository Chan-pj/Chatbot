import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "welbot_db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WELFARE_API_KEY = os.getenv("WELFARE_API_KEY", "")

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
