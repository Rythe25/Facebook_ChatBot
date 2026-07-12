"""Create the Pinecone index once (run once)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pinecone import Pinecone, ServerlessSpec
from app.config import settings

pc = Pinecone(api_key=settings.pinecone_api_key)
name = settings.pinecone_index_name

if pc.has_index(name):
    print(f"Index '{name}' already exists.")
else:
    pc.create_index(
        name=name,
        dimension=768,          # Gemini embedding output -> 768
        metric="cosine",        # similarity measure
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),  # free tier
    )
    print(f"Created index '{name}'.")

print(pc.describe_index(name))