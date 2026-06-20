import os
import torch
import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from chromadb.utils import embedding_functions
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_PATH = "CoolGuy320/wordpress-plugin-remediation"
DB_PATH = "../chroma_db"
COLLECTION_NAME = "wp_vulnerabilities"

app = FastAPI(
    title="WordPress Security RAG API",
    description="API for fetching plugin vulnerability remediation plans using a fine tuned model"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to point to your specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = chromadb.PersistentClient(path=DB_PATH)
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_func)

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="cuda",
    torch_dtype=torch.bfloat16
)

class PluginInfo(BaseModel):
    slug: str
    version: str

class AuditRequest(BaseModel):
    plugins: List[PluginInfo]
    
class AuditResponse(BaseModel):
    remediation_plan: str
    vulnerabilities_found: int
    
@app.get("/health")
def health_check():
    return {"status": "healthy", "gpu_available": torch.cuda.is_available()}

@app.post("/api/remediate", response_model=AuditResponse)
async def analyze_plugins(request: AuditRequest):
    if not request.plugins:
        raise HTTPException(status_code=400, details="The plugin list cannot be empty.")
    
    retrieved_contexts = []
    total_cves_found = 0
    unique_cves = set()
    
    for plugin in request.plugins:
        results = collection.get(
            where={"slug": plugin.slug}
        )
        
        if results and results['documents']:
            plugins_cves = []
            
            for doc, meta in zip(results['documents'], results['metadatas']):
                cve_id = meta['cve_id']
                score = meta['score']
                
                plugins_cves.append(doc)
                total_cves_found += 1
                
            if plugins_cves:
                bundled_plugin_context = (
                    f"=== VULNERABILITY REPORT FOR PLUGIN: {plugin.slug} ===\n"
                    f"Total Active Vulnerabilities Found: {len(plugins_cves)}\n\n"
                    + "\n\n----------------------------------------\n\n".join(plugins_cves)
                )
                retrieved_contexts.append(bundled_plugin_context)
    
    if not retrieved_contexts:
        return AuditResponse(
            remediation_plan="No known vulnerabilities were found in your vector database for the provided plugin.",
            vulnerabilities_found=0
        )
        
    context_str = "\n\n========================================\n\n".join(retrieved_contexts)
    
    system_prompt = (
        "You are an elite WordPress security expert. Review the provided vulnerability data "
        "for the user's active plugins. Synthesize a comprehensive, prioritized remediation "
        "plan. Group critical findings together, recommend specific patches or workarounds, "
        "and explicitly state if a plugin needs to be deleted due to unpatched risks."
    )
    
    user_prompt = f"Here is the vulnerability raw data for my plugins:\n\n{context_str}\n\nPlease generate my remediation plan."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    formatted_input = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(formatted_input, return_tensors="pt").to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024, # High enough token limit for detailed remediation scripts
            temperature=0.1,     # Low temperature for precise, fact-grounded recommendations
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id
        )
        
    generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
    remediation_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    
    return AuditResponse(
        remediation_plan=remediation_text.strip(),
        vulnerabilities_found=total_cves_found
    )
    
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)