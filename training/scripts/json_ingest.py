# pip install chromadb tqdm

"""
This script ingests a JSON dataset of WordPress plugin vulnerabilities and stores it in a ChromaDB collection.
"""

import json
import os
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions

JSON_DATASET_PATH = "../model_data/vuln_data.json"
DB_DIR = "../chroma_db"
COLLECTION_NAME = "wp_vulnerabilities"

def load_and_parse_dataset(file_path):
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find dataset at {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    documents = []
    metadata = []
    ids = []
    
    for cve_id, details, in data.items():
        slug = details.get("slug", "unknown-plugin")
        description = details.get("description", "")
        score = details.get("score", 0.0)
        fix = details.get("fix", "")
        
        document_text = (
            f"Plugin Slug: {slug}\n"
            f"CVE ID: {cve_id}\n"
            f"Severity Score: {score}\n"
            f"Description: {description}\n"
            f"Remediation/Fix: {fix}"
        )
        
        documents.append(document_text)
        metadata.append({
            "cve_id": cve_id,
            "slug": slug,
            "score": float(score)
        })
        ids.append(cve_id)
    
    return documents, metadata, ids

def main():
    
    documents, metadata, ids = load_and_parse_dataset(JSON_DATASET_PATH)
    
    client = chromadb.PersistentClient(path=DB_DIR)
    
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction (
        model_name="all-MiniLM-L6-v2"
    )
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func
    )
    
    batch_size = 500
    for i in tqdm(range(0, len(documents), batch_size)):
        end_idx = min(i + batch_size, len(documents))
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadata[i:end_idx],
            ids=ids[i:end_idx]
        )
        
if __name__ == "__main__":
    main()