import json

def convert_cve_to_chatm(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    processed_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for cve_id, details in raw_data.items():
            slug = details.get('slug', 'Unknown')
            description = details.get('description', 'No description available.')
            score = details.get('score', 'N/A')
            fix = details.get('fix', 'No fix information available.')
            
            user_content = (
                f"Vulnerability Report:\n"
                f"CVE: {cve_id}\n"
                f"Plugin: {slug}\n"
                f"Severity Score: {score}\n"
                f"Description: {description}"
            )
            
            training_example = {
                "messages": [
                    {
                    "role": "system",
                    "content": "You are a WordPress security expert. Given the name of a Wordpress plugin, identify if it is vulnerable and provide a detailed remediation plan if it is. If the plugin is not vulnerable, respond with 'No vulnerabilities found.'"
                    },
                    {
                        "role": "user",
                        "content": user_content
                    },
                    {
                        "role": "assistant",
                        "content": fix 
                    }
                ]
            }
            
            out_f.write(json.dumps(training_example) + '\n')
            processed_count += 1
        
    print(f"Processed {processed_count} CVE entries and saved to {output_file}")
    
if __name__ == "__main__":
    INPUT_FILE = 'vuln_data.json'  # Path to your input JSON file
    OUTPUT_FILE = 'chatml_training_data.jsonl'  # Path to your output JSONL file
    convert_cve_to_chatm(INPUT_FILE, OUTPUT_FILE)