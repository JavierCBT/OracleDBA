import json
import os
import re

def reformat_question_text(text):
    t = text.strip()
    
    # 1. Handle inline numbered lists like "1) ... 2) ... 3) ..."
    if re.search(r'\b1\)\s+[^\n]+2\)\s+', t):
        t = re.sub(r'\s*1\)\s+', '\n\n1. ', t)
        t = re.sub(r'\s*(\d+)\)\s+', r'\n\1. ', t)
        
    # 2. Fix known glued endings / intermediate text
    # Q36 in 1z0-078
    t = re.sub(
        r'(2\.\s+ACFS Encryption)\s+(To what minimum values must the compatible attributes be set\?)',
        r'\1\n\n\2',
        t
    )
    # Q7 in 1z0-078
    t = re.sub(
        r'(3\.\s+Compatibility settings set to 19\.0)\s+(The FG1 failure group goes offline due to hardware failure\.)\s+(Which two statements are true\?\s*\(Choose two\.\))',
        r'\1\n\n\2\n\n\3',
        t
    )
    # Q58 in 1z0-078
    t = re.sub(
        r'(7\.\s+Upgrade databases from one release to another\.)\s+(Your plan is to perform these tasks:)',
        r'\1\n\n\2',
        t
    )
    t = re.sub(
        r'(3\.\s+Create several RAC One Node databases\.)\s+(Which of the seven requirements are met by your plan\?)',
        r'\1\n\n\2',
        t
    )
    # Q60 in 1z0-078
    t = re.sub(
        r'(5\.\s+Grid infrastructure is installed and running in its default configuration\.)\s+(Which four benefits are provided by this configuration in Oracle 19c\?\s*\(Choose four\.\))',
        r'\1\n\n\2',
        t
    )
    # Q77 in 1z0-078
    t = re.sub(
        r'(8\.\s+Create a RAC database with DBCA using the template\.)\s+(Which option correctly lists the correct sequence of the minimum steps required to perform the conversion\?)',
        r'\1\n\n\2',
        t
    )
    # Q72 in 1z0-083
    t = re.sub(
        r'(5\.\s+UNDO RETENTION GUARANTEE is enabled\.)\s+(Multiple undesired multitable changes were made in all the PDBs\.)\s+(Which method can be used to undo the changes using a single command\?)',
        r'\1\n\n\2\n\n\3',
        t
    )

    # 3. Ensure blank line before numbered list block (e.g. "attributes:\n1." -> "attributes:\n\n1.")
    t = re.sub(r'([^\n])\n(\s*1\.\s+)', r'\1\n\n\2', t)

    # 4. Ensure blank line after numbered list block if followed by non-list text
    t = re.sub(r'\n(\d+\.\s+[^\n]+)\n(?!\s*(?:\d+\.|`))([^\n])', r'\n\1\n\n\2', t)

    # 5. Ensure the final question prompt is isolated with \n\n before it
    prompt_starters = (
        r'(?:Which|What|How|Why|When|Where|Who|To what|In which|For which|From which|At what|Under what|Choose)\b'
    )
    prompt_match = re.search(
        r'(?<=[.!?])\s+(' + prompt_starters + r'[^.?!\n]*\?(?:\s*\(Choose[^\)]+\)\.?)?\s*$)',
        t,
        re.IGNORECASE
    )
    if prompt_match:
        start_idx = prompt_match.start(1)
        before = t[:start_idx].rstrip()
        prompt = t[start_idx:].strip()
        t = f"{before}\n\n{prompt}"

    # 6. Normalize multiple blank lines to at most \n\n
    t = re.sub(r'\n{3,}', '\n\n', t)
    
    return t.strip()

def process_file(filepath):
    print(f"Reformatting question texts in {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    changed = 0
    for q in data:
        old_text = q['text']
        new_text = reformat_question_text(old_text)
        if new_text != old_text:
            changed += 1
            q['text'] = new_text
            
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
        
    print(f"Updated {changed}/{len(data)} questions in {filepath}.")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    process_file(os.path.join(data_dir, '1z0-078.json'))
    process_file(os.path.join(data_dir, '1z0-083.json'))
