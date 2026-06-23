# pip install safetensors

"""
This script reads multiple safetensor files from a specified input directory,
redistributes all weights into new, evenly sized shards, and saves them to an output directory.
It also generates a Hugging Face index layout for the newly created shards.
This script was originally needed to fit safetensor files into the 2GB limit for files on GitHub.
"""

import json
import os
import glob
from safetensors import safe_open
from safetensors.torch import save_file

def split_multiple_safetensors(input_dir, output_dir, max_shard_size_gb=2.0):
    """
    Reads multiple safetensor files from an input directory and redistributes 
    all weights into new, evenly sized shards.
    """
    os.makedirs(output_dir, exist_ok=True)
    max_shard_bytes = int(max_shard_size_gb * 1024 * 1024 * 1024)
    
    # Find all safetensor files in the source directory
    input_files = glob.glob(os.path.join(input_dir, "*.safetensors"))
    if not input_files:
        print(f"Error: No .safetensors files found in {input_dir}")
        return

    print(f"Found {len(input_files)} source files to process...")
    
    weight_map = {}
    current_shard_tensors = {}
    current_shard_bytes = 0
    shard_count = 1

    # 1. Loop through every existing safetensors file
    for file_path in sorted(input_files):
        print(f"Reading tensors from: {os.path.basename(file_path)}")
        
        with safe_open(file_path, framework="pt", device="cpu") as f:
            for key in sorted(f.keys()):
                tensor = f.get_tensor(key)
                tensor_bytes = tensor.nelement() * tensor.element_size()
                
                # 2. Flush current shard if it overflows the target size threshold
                if current_shard_bytes + tensor_bytes > max_shard_bytes and current_shard_tensors:
                    shard_name = f"model-{shard_count:05d}-of-XXXXX.safetensors"
                    save_path = os.path.join(output_dir, shard_name)
                    
                    save_file(current_shard_tensors, save_path)
                    print(f"  -> Saved: {shard_name} ({len(current_shard_tensors)} tensors)")
                    
                    current_shard_tensors = {}
                    current_shard_bytes = 0
                    shard_count += 1
                
                current_shard_tensors[key] = tensor
                current_shard_bytes += tensor_bytes
                weight_map[key] = f"model-{shard_count:05d}-of-TOTAL_PLACEHOLDER.safetensors"

    # 3. Save the trailing leftovers
    if current_shard_tensors:
        shard_name = f"model-{shard_count:05d}-of-XXXXX.safetensors"
        save_path = os.path.join(output_dir, shard_name)
        save_file(current_shard_tensors, save_path)
        print(f"  -> Saved final: {shard_name} ({len(current_shard_tensors)} tensors)")

    total_shards = shard_count
    print(f"\nFinalizing metadata for {total_shards} shards...")

    # 4. Correct placeholder file names on disk
    for filename in os.listdir(output_dir):
        if "-of-XXXXX.safetensors" in filename:
            new_name = filename.replace("XXXXX", f"{total_shards:05d}")
            os.rename(os.path.join(output_dir, filename), os.path.join(output_dir, new_name))
            
    # 5. Fix strings in the internal metadata mapping
    for key in weight_map:
        weight_map[key] = weight_map[key].replace("TOTAL_PLACEHOLDER", f"{total_shards:05d}")
        
    # 6. Build the Hugging Face index layout
    index_data = {
        "metadata": {
            "total_size": sum(
                os.path.getsize(os.path.join(output_dir, f"model-{i:05d}-of-{total_shards:05d}.safetensors")) 
                for i in range(1, total_shards + 1)
            )
        },
        "weight_map": weight_map
    }
    
    index_path = os.path.join(output_dir, "model.safetensors.index.json")
    with open(index_path, "w", encoding="utf-8") as index_file:
        json.dump(index_data, index_file, indent=2)
        
    print(f"\nSuccess! Re-sharded model into {total_shards} pieces.")
    print(f"Index layout saved to: {index_path}")

# Example Usage
if __name__ == "__main__":
    # Point this to the folder containing your current large files
    SOURCE_FOLDER = r"C:\Users\acdur\Projects\Capstone\UMGC_CMSC495\training\model.safetensors"
    # Point this to where you want the new smaller shards saved
    OUTPUT_FOLDER = r"C:\Users\acdur\Projects\Capstone\UMGC_CMSC495\training\sharded_output"
    
    split_multiple_safetensors(
        input_dir=SOURCE_FOLDER, 
        output_dir=OUTPUT_FOLDER, 
        max_shard_size_gb=2.0  # Adjust target size per shard here
    )