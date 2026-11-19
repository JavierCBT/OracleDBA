import json
import os
import re
import itertools

STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'also', 'am', 'an', 'and', 'any', 'are', 'aren',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'cannot',
    'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has',
    'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into',
    'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off',
    'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should',
    'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these',
    'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn', 'we', 'were',
    'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'would', 'you', 'your',
    'statement', 'statements', 'true', 'false', 'correct', 'incorrect', 'following', 'oracle', 'database',
    'may', 'might', 'must', 'shall', 'should', 'used', 'using', 'use', 'uses', 'get', 'gets', 'set', 'sets',
    'one', 'two', 'three', 'four', 'five', 'six', 'first', 'second', 'third', 'either', 'neither', 'another',
    'always', 'never', 'sometimes', 'become', 'becomes', 'became', 'show', 'shows', 'shown', 'see', 'seen',
    'take', 'takes', 'taken', 'give', 'gives', 'given', 'need', 'needs', 'needed', 'make', 'makes', 'made'
}

def clean_text(t):
    return re.sub(r'\s+', ' ', str(t or '')).strip()

def normalize_for_match(text):
    t = re.sub(r'[,;:?!\'\"()\[\]]|\.(?=\s|$)', ' ', text or '')
    return re.sub(r'\s+', ' ', t).strip()

def is_token_in_text(token, text):
    # Check whole token / phrase match (case-insensitive)
    norm_text = normalize_for_match(text)
    norm_token = normalize_for_match(token)
    pattern = r'(?<![A-Za-z0-9_\$\.])' + re.escape(norm_token) + r'(?![A-Za-z0-9_\$\.])'
    return bool(re.search(pattern, norm_text, re.IGNORECASE))

def extract_candidates_for_option(opt_text):
    candidates = []
    
    # 1. Comma numbers like "2, 4, 5" or "1, 3, 4, 6, 8"
    num_matches = re.findall(r'\b\d+(?:,\s*\d+)+\b', opt_text)
    for nm in num_matches:
        candidates.append((1, nm))

    # 2. Words preserving Oracle characters
    norm = normalize_for_match(opt_text)
    tokens = [tok for tok in norm.split(' ') if tok]
    
    # 1-grams
    for tok in tokens:
        tl = tok.lower()
        if tl not in STOPWORDS and len(tok) >= 2:
            candidates.append((1, tok))
            
    # 2-grams to 6-grams from normalized text
    max_n = min(6, len(tokens))
    for n in range(2, max_n + 1):
        for i in range(len(tokens) - n + 1):
            slice_toks = tokens[i:i+n]
            if all(w.lower() in STOPWORDS for w in slice_toks):
                continue
            phrase = " ".join(slice_toks)
            candidates.append((n, phrase))
            
    # 3. Raw substrings with internal punctuation (e.g. "ASM to 12.1, COMPATIBLE.RDBMS to 11.2")
    raw_words = opt_text.split()
    for n in range(3, min(8, len(raw_words) + 1)):
        for i in range(len(raw_words) - n + 1):
            phrase = " ".join(raw_words[i:i+n]).rstrip('.,;:')
            if phrase and phrase not in [c[1] for c in candidates]:
                candidates.append((n, phrase))

    # 4. Check if option has distinctive period end like "on all nodes."
    clean_strip = opt_text.strip()
    if clean_strip.endswith('.'):
        for n in range(2, min(5, len(tokens) + 1)):
            end_phrase = " ".join(tokens[-n:]) + "."
            candidates.append((n, end_phrase))
            
    return candidates

# Specific manual overrides for known highly-distractor questions where automatic n-grams need precise tailoring
MANUAL_OVERRIDES = {
    # 1z0-078
    (78, 1): ["is stopped on all nodes.", "started on HOST01", "is started on all nodes."],
    (78, 9): ["delete node -n host04 command as root on host01", "rootcrs.pl -deconfig -force command as root on host04"],
    (78, 15): ["Clusterware stack must be up on all cluster nodes where", "Grid Infrastructure must be installed on all cluster nodes where"],
    # 1z0-083
    (83, 32): ["Sorts", "UGA) is located in the System Global Area (SGA) when using shared servers"],
    (83, 33): ["Control file backups can be created while connected to the root container", "BACKUP TABLESPACE"],
    (83, 107): ["not in the current FRA", "Oracle recovery files in the current FRA"],
    (83, 132): ["2, 4, 5"],
    (83, 133): ["snapshot copy PDB depends on a storage snapshot which can only be stored on specific file systems", "stand-alone clone PDB"],
    (83, 157): ["can be created in a pluggable database", "target.", "non-container database"],
    (83, 164): ["pluggable database in silent mode", "cloning a remote container database in silent mode"]
}

def find_minimal_cover_for_question(q, exam_num=78):
    qid = q['id']
    if (exam_num, qid) in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[(exam_num, qid)]
        
    correct_keys = set(q.get('correct', []))
    correct_opts = [o for o in q.get('options', []) if (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    
    wrong_texts = [o['text'] for o in wrong_opts]
    
    cand_coverage = {}
    cand_info = {}
    
    all_cands = []
    for opt in correct_opts:
        all_cands.extend(extract_candidates_for_option(opt['text']))
        
    seen_lower = set()
    unique_cands = []
    for n, cand in all_cands:
        cl = cand.lower().strip()
        if cl not in seen_lower:
            seen_lower.add(cl)
            unique_cands.append((n, cand.strip()))
            
    for n, cand in unique_cands:
        # Exclusivity check: MUST NOT appear in any wrong option
        cand_in_wrong = False
        for wt in wrong_texts:
            if cand.endswith('.'):
                if cand.lower() in wt.lower():
                    cand_in_wrong = True
                    break
            else:
                if is_token_in_text(cand, wt) or (cand.lower() in wt.lower() and len(cand) > 15):
                    cand_in_wrong = True
                    break
        if cand_in_wrong:
            continue
            
        covered = set()
        for opt in correct_opts:
            okey = opt.get('letter') or opt.get('key')
            if cand.endswith('.'):
                if cand.lower() in opt['text'].lower():
                    covered.add(okey)
            else:
                if is_token_in_text(cand, opt['text']) or cand.lower() in opt['text'].lower():
                    covered.add(okey)
                
        if covered:
            score = 0
            if '_' in cand or '$' in cand: score += 30
            if cand.isupper() and len(cand) >= 3: score += 25
            if any(c.isdigit() for c in cand): score += 15
            if '.' in cand and not cand.endswith('.'): score += 10
            # Prefer shorter n-grams
            score -= (n * 12)
            # Big bonus for covering multiple correct options
            score += len(covered) * 70
            score -= int(len(cand) * 0.2)
            
            cand_coverage[cand] = covered
            cand_info[cand] = (n, -score, len(cand), cand)
            
    all_needed_keys = set(o.get('letter') or o.get('key') for o in correct_opts)
    all_valid_cands = sorted(cand_coverage.keys(), key=lambda c: (cand_info[c][1], cand_info[c][0], cand_info[c][2]))
    
    best_solution = None
    for r in range(1, len(all_needed_keys) + 1):
        for combo in itertools.combinations(all_valid_cands, r):
            union_covered = set().union(*(cand_coverage[c] for c in combo))
            if all_needed_keys.issubset(union_covered):
                best_solution = list(combo)
                break
        if best_solution:
            break
            
    return best_solution or []

def extract_anchor_for_question(q):
    exp = q.get('explanation', '')
    if not exp:
        return ""
    
    exp_text = re.sub(r'```[\s\S]*?```', '', exp)
    sentences = re.split(r'(?<=[.!?])\s+', exp_text)
    
    candidate_anchors = []
    for s in sentences:
        s_clean = clean_text(s)
        s_clean = re.sub(r'^(The (?:defensible )?key is [A-G](?:, [A-G])*(?: and [A-G])*\.?\s*)', '', s_clean, flags=re.I)
        s_clean = re.sub(r'^(Option [A-G] is (?:the )?correct(?: answer)?(?::| because|\.)?\s*)', '', s_clean, flags=re.I)
        s_clean = re.sub(r'^([A-G] is correct(?::| because|\.)?\s*)', '', s_clean, flags=re.I)
        s_clean = re.sub(r'^(Options [A-G](?:, [A-G])*(?: and [A-G])* are correct(?::| because|\.)?\s*)', '', s_clean, flags=re.I)
        s_clean = clean_text(s_clean)
        
        if re.match(r'^(Option [A-G] is (?:false|incorrect)|[A-G] is false)', s_clean, re.I):
            continue
        if re.search(r'\b(is false because|is incorrect because)\b', s_clean, re.I):
            continue
        if 'For a practical investigation' in s_clean or 'After extending a tablespace' in s_clean:
            continue
            
        if 35 <= len(s_clean) <= 160:
            candidate_anchors.append(s_clean)
            
    if candidate_anchors:
        return candidate_anchors[0]
        
    for s in sentences:
        sc = clean_text(s)
        if len(sc) > 30:
            return sc[:140] + ("..." if len(sc) > 140 else "")
            
    return "Review the core Oracle documentation principles for this topic."

def process_exam_file(filepath, exam_num, dry_run=False):
    print(f"\nProcessing {filepath} (Exam {exam_num})...")
    with open(filepath, 'r', encoding='utf-8') as f:
        questions = json.load(f)
        
    updated = 0
    errors = 0
    for q in questions:
        kws = find_minimal_cover_for_question(q, exam_num)
        if not kws:
            print(f"ERROR: Q#{q['id']} could not find minimal exclusive cover!")
            errors += 1
            continue
            
        # Verify exclusivity of every keyword!
        correct_keys = set(q.get('correct', []))
        wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
        for kw in kws:
            kw_clean = kw.rstrip('.')
            for wo in wrong_opts:
                wo_clean = wo['text'].strip()
                # For pure numeric sequence options (e.g. "2, 4, 5"), check exact match
                if re.match(r'^[\d,\s]+$', wo_clean):
                    if kw.strip() == wo_clean:
                        print(f"WARNING: Q#{q['id']} kw '{kw}' matches wrong numeric option {wo['key']}!")
                        errors += 1
                elif kw.endswith('.'):
                    if kw.lower() in wo['text'].lower():
                        print(f"WARNING: Q#{q['id']} kw '{kw}' found in wrong option {wo['key']}!")
                        errors += 1
                elif is_token_in_text(kw_clean, wo['text']):
                    print(f"WARNING: Q#{q['id']} kw '{kw}' found in wrong option {wo['key']}!")
                    errors += 1
                    
        anchor = extract_anchor_for_question(q)
        q['mnemonic'] = {
            'keywords': kws,
            'anchor': anchor
        }
        updated += 1
        
    print(f"Enriched {updated}/{len(questions)} questions with exclusive minimal mnemonics (Errors: {errors}).")
    
    if not dry_run and errors == 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"Successfully saved {filepath}")
    elif dry_run:
        print("[Dry Run] Did not write to disk.")
    else:
        print("Encountered errors, aborting save.")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    process_exam_file(os.path.join(data_dir, '1z0-078.json'), 78, dry_run=False)
    process_exam_file(os.path.join(data_dir, '1z0-083.json'), 83, dry_run=False)
