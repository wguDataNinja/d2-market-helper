import os
import re
import json

# Source files
FILES_TO_SCAN = [
    "/Users/buddy/Desktop/traderie/Traderie_page_files/f.txt",
    "/Users/buddy/Desktop/traderie/Traderie_page_files/f_002.txt"
]

# Output directory
OUTPUT_DIR = "/data/.old/site data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_json_like_objects(text):
    """
    Extracts potential JSON-like strings from the text.
    """
    pattern = r'{.*?}'
    candidates = re.findall(pattern, text, re.DOTALL)
    json_objects = []
    for c in candidates:
        try:
            obj = json.loads(c)
            json_objects.append(obj)
        except json.JSONDecodeError:
            continue
    return json_objects

def process_file(file_path):
    print(f"🔍 Processing: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            json_blobs = extract_json_like_objects(content)
            print(f"✅ Found {len(json_blobs)} JSON-like objects")
            if json_blobs:
                output_file = os.path.join(
                    OUTPUT_DIR,
                    os.path.basename(file_path) + ".parsed.json"
                )
                with open(output_file, "w", encoding="utf-8") as out:
                    json.dump(json_blobs, out, indent=2)
                print(f"💾 Saved to: {output_file}")
            else:
                print("⚠️  No valid JSON objects found.")
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")

def main():
    for file_path in FILES_TO_SCAN:
        process_file(file_path)

if __name__ == "__main__":
    main()