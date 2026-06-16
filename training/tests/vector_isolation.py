import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="../chroma_db")
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name="wp_vulnerabilities", embedding_function=embedding_func)

# 1. Use the exact slug for the metadata filter
exact_slug = "molie-instructure-canvas-linking-tool"

# 2. Query with the `where` clause
results = collection.query(
    query_texts=["vulnerability details"], # The text query becomes less important here
    n_results=1,
    where={"slug": exact_slug} # Forces ChromaDB to only return documents matching this slug
)

print("--- Metadata Match Results ---")
print(results["documents"])