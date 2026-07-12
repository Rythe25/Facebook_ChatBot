"""FAQ retrieval tool backed by Pinecone."""
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from app.config import settings

# Build clients ONCE at import, reuse on every call.
_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.google_api_key,
    output_dimensionality=768,        # MUST match the index + upload
)
_index = Pinecone(api_key=settings.pinecone_api_key).Index(settings.pinecone_index_name)

SCORE_THRESHOLD = 0.5


@tool
def search_faq(query: str) -> str:
    """Look up the pet salon's FAQ to answer customer questions about hours,
    prices, services, location, payment, booking, and policies.
    Call this whenever the customer asks anything about the business."""
    vector = _embeddings.embed_query(query)
    result = _index.query(vector=vector, top_k=3, include_metadata=True)
    matches = [m for m in result["matches"] if m["score"] >= SCORE_THRESHOLD]
    if not matches:
        return "No relevant FAQ found. Tell the customer you'll check and follow up."
    return "\n\n".join(f"Q: {m['metadata']['question']}\nA: {m['metadata']['answer']}" for m in matches)