import os
import json
import re

os.chdir('C:\\AI-Projects\\OracleDBA')

# 1. Check all static assets listed in sw.js exist
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

m = re.search(r'const STATIC_ASSETS = \[(.*?)\];', sw_content, re.DOTALL)
assets = [line.strip().strip("',\"") for line in m.group(1).split('\n') if line.strip() and not line.strip().startswith('//')]

print("Verifying Service Worker Static Assets:")
for a in assets:
    if a in ['./', './1z0-078/', './1z0-083/']:
        target = os.path.join(a.lstrip('./'), 'index.html') if a != './' else 'index.html'
    else:
        target = a.lstrip('./')
    exists = os.path.exists(target)
    size = os.path.getsize(target) if exists else 0
    print(f"  [{'OK' if exists else 'MISSING'}] {a} -> {target} ({size} bytes)")

# 2. Check manifest.webmanifest
with open('manifest.webmanifest', 'r', encoding='utf-8') as f:
    manifest = json.load(f)
print("\nManifest valid JSON with", len(manifest.get('icons', [])), "icons.")

# 3. Check data JSONs
for exam in ['1z0-078.json', '1z0-083.json']:
    path = os.path.join('data', exam)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Data {exam}: {len(data)} questions, valid JSON.")
