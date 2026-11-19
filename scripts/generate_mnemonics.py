import json
import os
import re
import itertools

ARTICLES_AND_BANNED = {
    'a', 'an', 'the', 'this', 'that', 'these', 'those'
}

EDGE_STOPWORDS = {
    'in', 'on', 'at', 'to', 'for', 'of', 'by', 'with', 'from', 'into', 'onto',
    'and', 'or', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'it', 'its', 'their', 'theirs', 'our', 'ours', 'your', 'yours', 'my', 'his', 'her',
    'than', 'then', 'so', 'such', 'not', 'no', 'nor', 'but', 'if', 'can', 'may'
}

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

MANUAL_OVERRIDES = {
    # 1z0-078
    (78, 1): ["is stopped on all nodes.", "started on HOST01", "is started on all nodes."],
    (78, 7): ["redundancy", "tracked"],
    (78, 9): ["delete node -n host04 command as root on host01", "rootcrs.pl -deconfig -force command as root on host04"],
    (78, 10): ["across RAC database instances", "SCAN listeners", "or both"],
    (78, 15): ["Clusterware stack must be up on all cluster nodes where", "Grid Infrastructure must be installed on all cluster nodes where"],
    (78, 20): ["cannot", "not automatically registered"],
    (78, 27): ["CLUVFY", "OCRDUMP"],
    (78, 30): ["then to create"],
    (78, 47): ["dynamically", "OMF", "instance recovery"],
    (78, 58): ["1, 2, 3, 4 and 6."],
    
    # 1z0-083
    (83, 18): ["PDB snapshot can be", "DBCA"],
    (83, 32): ["Sorts", "private SQL area (UGA) is located in the System Global Area (SGA) when using shared servers"],
    (83, 33): ["Control file backups can be created while connected to the root container", "BACKUP TABLESPACE"],
    (83, 34): ["TYPICAL", "ALL", "forever"],
    (83, 38): ["give", "enabled", "target PDB must be registered in a base catalog"],
    (83, 39): ["application root", "application seed to", "regular PDB to"],
    (83, 41): ["SPFILE", "recovered to a consistent state", "ARCHIVAL attribute"],
    (83, 62): ["can get backed up automatically", "can be backed up manually as a binary copy", "can be backed up manually as a trace file"],
    (83, 85): ["PDB snapshot can be"],
    (83, 99): ["orainstRoot.sh", "cannot be specified"],
    (83, 107): ["not in the current FRA", "Oracle recovery files in the current FRA"],
    (83, 109): ["when using synchronous I/O.", "noticeably less", "then read I/O is"],
    (83, 116): ["drop requires that the RECYCLEBIN", "version query requires undo"],
    (83, 117): ["CREATE_FILE_DEST", "Set only", "Enable only"],
    (83, 119): ["Large Pool", "increase the System Global Area size by reducing the Program Global Area size", "Decision Support Systems"],
    (83, 120): ["losing all copies of the control file", "losing an archived log from before the most recent backup", "SYSTEM tablespace"],
    (83, 132): ["2, 4, 5"],
    (83, 133): ["snapshot copy PDB depends on a storage snapshot which can only be stored on specific file systems", "stand-alone clone PDB"],
    (83, 145): ["importing full exports", "convert conventional database users to local users", "convert common users to conventional users"],
    (83, 153): ["done on that physical standby database", "done on its primary database"],
    (83, 157): ["can be created in a pluggable database", "target.", "non-container database"],
    (83, 164): ["pluggable database in silent mode", "cloning a remote container database in silent mode"],
    (83, 168): ["CONFIGURE command to specify duplexing", "can be written to media"],
    (83, 175): ["HR_ROOT replica must exist in the remote CDB", "proxy PDB must exist in the application root in the local CDB"],
    (83, 177): ["applications and middleware", "both Oracle Database and Oracle Grid Infrastructure, including Oracle Restart"]
}

def clean_text(t):
    return re.sub(r'\s+', ' ', str(t or '')).strip()

def normalize_text(text):
    t = re.sub(r'[,;:?!\'\"()\[\]]|\.(?=\s|$)', ' ', text or '')
    return re.sub(r'\s+', ' ', t).strip()

def is_token_in_text(token, text):
    t = token.strip()
    if t.endswith('.'):
        pattern = r'(?<![A-Za-z0-9_\$\.])' + re.escape(t[:-1]) + r'\.(?:\s|$)'
        return bool(re.search(pattern, text, re.IGNORECASE))
        
    norm_text = normalize_text(text)
    norm_token = normalize_text(t)
    pattern = r'(?<![A-Za-z0-9_\$\.])' + re.escape(norm_token) + r'(?![A-Za-z0-9_\$\.])'
    return bool(re.search(pattern, norm_text, re.IGNORECASE))

def extract_candidates(text):
    candidates = []
    norm = normalize_text(text)
    tokens = [tok for tok in norm.split(' ') if tok]
    
    # 1. Single words (1-grams)
    for tok in tokens:
        tl = tok.lower()
        if tl in STOPWORDS or tl in ARTICLES_AND_BANNED or len(tok) < 2:
            continue
        candidates.append((1, tok))
        
    # 2. Number lists like "2, 4, 5"
    for nm in re.findall(r'\b\d+(?:,\s*\d+)+\b', text):
        candidates.append((1, nm))
        
    # 3. Multi-word phrases (2-grams to 4-grams)
    max_n = min(4, len(tokens))
    for n in range(2, max_n + 1):
        for i in range(len(tokens) - n + 1):
            slice_toks = tokens[i:i+n]
            # Exclude phrases with articles
            if any(t.lower() in ARTICLES_AND_BANNED for t in slice_toks):
                continue
            # Exclude phrases starting or ending with edge stopwords
            if slice_toks[0].lower() in EDGE_STOPWORDS or slice_toks[-1].lower() in EDGE_STOPWORDS:
                continue
            if all(t.lower() in STOPWORDS for t in slice_toks):
                continue
            phrase = " ".join(slice_toks)
            candidates.append((n, phrase))
            
    return candidates

def find_minimal_cover_for_question(q, exam_num=78):
    qid = q['id']
    if (exam_num, qid) in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[(exam_num, qid)]
        
    correct_keys = set(q.get('correct', []))
    correct_opts = [o for o in q.get('options', []) if (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    all_needed_keys = set(o.get('letter') or o.get('key') for o in correct_opts)
    
    cand_coverage = {}
    cand_info = {}
    
    all_cands = []
    for opt in correct_opts:
        all_cands.extend(extract_candidates(opt['text']))
        
    seen = set()
    unique_cands = []
    for n, cand in all_cands:
        cl = cand.lower().strip()
        if cl not in seen:
            seen.add(cl)
            unique_cands.append((n, cand.strip()))
            
    for n, cand in unique_cands:
        in_wrong = any(is_token_in_text(cand, wo['text']) for wo in wrong_opts)
        if in_wrong:
            continue
            
        covered = set()
        for opt in correct_opts:
            okey = opt.get('letter') or opt.get('key')
            if is_token_in_text(cand, opt['text']):
                covered.add(okey)
                
        if covered:
            score = 0
            # Higher score for Oracle technical identifiers
            if '_' in cand or '$' in cand: score += 50
            if cand.isupper() and len(cand) >= 3: score += 40
            if '.' in cand and not cand.endswith('.'): score += 30
            if any(c.isdigit() for c in cand): score += 15
            
            # Massive bonus for single words vs phrases
            if n == 1:
                score += 60
            else:
                score -= (n * 35)
                
            # Bonus for covering multiple options at once
            score += len(covered) * 120
            
            cand_coverage[cand] = covered
            cand_info[cand] = (n, -score, len(cand), cand)
            
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
            
        # 1. Verify no standalone articles as keywords
        for kw in kws:
            if kw.lower() in ARTICLES_AND_BANNED:
                print(f"ERROR: Q#{q['id']} kw '{kw}' is a standalone article!")
                errors += 1
            # Check for patterns like "the OCR" or "a PDB"
            if re.match(r'^(the|a|an)\s+[A-Za-z0-9_\$]+$', kw, re.I):
                print(f"ERROR: Q#{q['id']} kw '{kw}' is an article-noun pair!")
                errors += 1
                
        # 2. Verify exclusivity
        correct_keys = set(q.get('correct', []))
        wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
        for kw in kws:
            for wo in wrong_opts:
                wo_clean = wo['text'].strip()
                if re.match(r'^[\d,\s]+$', wo_clean):
                    if kw.strip() == wo_clean:
                        print(f"ERROR: Q#{q['id']} kw '{kw}' matches wrong numeric option {wo['key']}!")
                        errors += 1
                elif is_token_in_text(kw, wo['text']):
                    print(f"ERROR: Q#{q['id']} kw '{kw}' found in wrong option {wo['key']}!")
                    errors += 1
                    
        # 3. Verify coverage
        correct_opts = [o for o in q.get('options', []) if (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
        all_needed_keys = set(o.get('letter') or o.get('key') for o in correct_opts)
        covered = set()
        for kw in kws:
            for co in correct_opts:
                ckey = co.get('letter') or co.get('key')
                if is_token_in_text(kw, co['text']):
                    covered.add(ckey)
        if not all_needed_keys.issubset(covered):
            print(f"ERROR: Q#{q['id']} kws {kws} do not cover all correct options ({all_needed_keys - covered} missing)!")
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
        raise RuntimeError(f"Failed to process {filepath} due to {errors} errors.")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    process_exam_file(os.path.join(data_dir, '1z0-078.json'), 78, dry_run=False)
    process_exam_file(os.path.join(data_dir, '1z0-083.json'), 83, dry_run=False)
