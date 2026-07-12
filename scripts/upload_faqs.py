"""Embed faqs.csv and upsert into Pinecone (run once)."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from app.config import settings

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "faqs.csv")


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} FAQ rows.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.google_api_key,
        output_dimensionality=768,
    )
    values = embeddings.embed_documents([r["question"] for r in rows])

    records = [
        {"id": f"faq-{i}", "values": vec,
         "metadata": {"question": r["question"], "answer": r["answer"]}}
        for i, (r, vec) in enumerate(zip(rows, values))
    ]

    index = Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index_name)
    index.upsert(vectors=records)
    print(f"Upserted {len(records)} vectors.")
    print(index.describe_index_stats())


if __name__ == "__main__":
    main()