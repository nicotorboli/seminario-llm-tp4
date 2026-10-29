import os

from dotenv import load_dotenv
from upstash_vector import Index

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MODEL: str = os.getenv("MODEL") or ""
HOST: str = os.getenv("HOST", "http://localhost:11434")
UPSTASH_VECTOR_REST_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
UPSTASH_VECTOR_REST_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

if not MODEL:
    raise RuntimeError("Falta MODEL en el .env")

if not UPSTASH_VECTOR_REST_URL or not UPSTASH_VECTOR_REST_TOKEN:
    raise RuntimeError("Faltan UPSTASH_VECTOR_REST_URL / UPSTASH_VECTOR_REST_TOKEN en el .env")

cliente_upstash = Index(url=UPSTASH_VECTOR_REST_URL, token=UPSTASH_VECTOR_REST_TOKEN)
