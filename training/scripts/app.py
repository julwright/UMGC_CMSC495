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


TRAINED_SYSTEM_PROMPT = (
    "You are a WordPress security expert. Given the name of a Wordpress plugin, "
    "identify if it is vulnerable and provide a detailed remediation plan if it is. "
    "If the plugin is not vulnerable, respond with 'No vulnerabilities found.'"
)
@app.get("/health")
def health_check():
    return {"status": "healthy", "gpu_available": torch.cuda.is_available()}


@app.post("/api/remediate", response_model=AuditResponse)
async def analyze_plugins(request: AuditRequest):
    """
    Call the model once per CVE using the exact prompt format it was trained on,
     then group the results by plugin.
    """
    if not request.plugins:
        raise HTTPException(status_code=400, detail="The plugin list cannot be empty.")

    plugin_sections = []
    total_cves_found = 0

    for plugin in request.plugins:
        results = collection.get(where={"slug": plugin.slug})

        if not (results and results["documents"]):
            continue

        cve_blocks = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            cve_id = meta["cve_id"]
            score = meta["score"]

         
            description = ""
            if "Description:" in doc:
                description = doc.split("Description:", 1)[1]
                description = description.split("Remediation/Fix:", 1)[0].strip()

            # Exact training-time user prompt format (chatML_data.py).
            user_prompt = (
                f"Vulnerability Report:\n"
                f"CVE: {cve_id}\n"
                f"Plugin: {plugin.slug}\n"
                f"Severity Score: {score}\n"
                f"Description: {description}"
            )

            remediation = generate_remediation([
                {"role": "system", "content": TRAINED_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ])

            cve_blocks.append(f"[{cve_id}] (Severity {score})\n{remediation}")
            total_cves_found += 1

        if cve_blocks:
            label = "vulnerability" if len(cve_blocks) == 1 else "vulnerabilities"
            section = (
                f"=== PLUGIN: {plugin.slug} (v{plugin.version}) - "
                f"{len(cve_blocks)} {label} ===\n\n"
                + "\n\n".join(cve_blocks)
            )
            plugin_sections.append(section)

    if not plugin_sections:
        return AuditResponse(
            remediation_plan="No known vulnerabilities were found in your vector "
                             "database for the provided plugins.",
            vulnerabilities_found=0
        )

    final_plan = "\n\n========================================\n\n".join(plugin_sections)
    return AuditResponse(
        remediation_plan=final_plan,
        vulnerabilities_found=total_cves_found
    )

def generate_remediation(messages):
    """Run one chat completion through the fine-tuned model and return the text."""
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
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
