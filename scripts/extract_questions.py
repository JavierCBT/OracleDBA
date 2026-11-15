import json
import re
import os

os.makedirs('data', exist_ok=True)

# Extract 1z0-078
with open('1z0-078/1z0-078.html', 'r', encoding='utf-8') as f:
    c78 = f.read()

m78 = re.search(r'const ALL_QUESTIONS = (\[.*?\]);', c78, re.DOTALL)
if m78:
    qs78 = json.loads(m78.group(1))
    with open('data/1z0-078.json', 'w', encoding='utf-8') as f:
        json.dump(qs78, f, indent=2, ensure_ascii=False)
    print(f"Extracted {len(qs78)} questions to data/1z0-078.json")
else:
    print("Error extracting 1z0-078")

# Extract 1z0-083
with open('1z0-083/1z0-083.html', 'r', encoding='utf-8') as f:
    c83 = f.read()

m83 = re.search(r'const ALL_QUESTIONS = (\[.*?\]);', c83, re.DOTALL)
if m83:
    qs83 = json.loads(m83.group(1))
    with open('data/1z0-083.json', 'w', encoding='utf-8') as f:
        json.dump(qs83, f, indent=2, ensure_ascii=False)
    print(f"Extracted {len(qs83)} questions to data/1z0-083.json")
else:
    print("Error extracting 1z0-083")
