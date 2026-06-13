# pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu130
# pip install unsloth
# flash-attn built on wheel from https://huggingface.co/Wildminder/AI-windows-whl/resolve/main/flash_attn-2.8.3%2Bd20260121.cu130torch2.10.0cxx11abiTRUE-cp312-cp312-win_amd64.whl
# trained on RTX 5070, pytorch 2.10.0, cuda 13.0, python 3.12

from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
DATA_PATH = "../model_data/chatml_training_data.jsonl"

def train():
    
    print("Loading Dataset...")
    dataset = load_dataset("json", data_files=DATA_PATH, split="train") 

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="meta-llama/Llama-3.1-8B-Instruct",
        max_seq_length=2048,
        load_in_4bit=True,  # Compresses base model to ~5.5GB
        dtype=torch.bfloat16,  # Native hardware acceleration for modern NVIDIA GPUs
        device_map="auto",
    )

    tokenizer = get_chat_template(
        tokenizer,
        chat_template="llama-3.1",
    )
    
    # unsloth requires a specific formatting of the input prompts for optimal training, so we preprocess the dataset accordingly.
    def formatting_prompts_func(examples):
        texts = [
            tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            for messages in examples["messages"]
        ]
        return {"text": texts}
    
    dataset = dataset.map(formatting_prompts_func, batched=True)

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=32,
        lora_dropout=0,  # Optimized to 0 for Unsloth
        bias="none",
        use_gradient_checkpointing="unsloth",  # Saves ~30% VRAM by recomputing activations
        random_state=3407,
        use_rslora=True,  # Rank-Stabilized LoRA for stable convergence
    )

    training_args = TrainingArguments(
        per_device_train_batch_size=1,  
        gradient_accumulation_steps=8,  # Simulates a global batch size of 8
        warmup_steps=10,
        num_train_epochs=1,
        learning_rate=2e-4,  
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),  # True for RTX 5070
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        output_dir="../cve-remediation/",
        report_to="none",
        save_strategy="no", # python's pickle package will crash due to how unsloth rewrites transformers and trl.
    )
    
    sft_trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        dataset_num_proc=2,
        packing=True,  
        args=training_args,
    )
    
    print("Starting training...")
    sft_trainer.train()

    model.save_pretrained_merged(
        "cve-remediation", tokenizer, save_method="lora"
    )
    print("Training complete. Adapters saved successfully!")

if __name__ == "__main__":
    train()