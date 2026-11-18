import json
import os
import re

STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'also', 'am', 'an', 'and', 'any', 'are', 'aren',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'cannot',
    'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has',
    'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into',
    'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off',
    'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should',
    'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these',
    'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn', 'we', 'were',
    'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'would', 'you', 'your'
}

def clean_text(t):
    return re.sub(r'\s+', ' ', str(t or '')).strip()

def find_best_discriminator_for_option(opt_text, wrong_combined_text):
    clean_opt = clean_text(opt_text)
    
    # 1. Oracle-specific identifiers: ALL_CAPS with underscores/$, commands, views, params
    terms = re.findall(r'\b[A-Za-z0-9_\$]{3,}\b', clean_opt)
    oracle_terms = []
    for tok in terms:
        tl = tok.lower()
        if tl in STOPWORDS or len(tok) < 3:
            continue
        if f" {tl} " not in wrong_combined_text:
            if '_' in tok or '$' in tok or (tok.isupper() and len(tok) >= 3):
                oracle_terms.append(tok)
    if oracle_terms:
        oracle_terms.sort(key=lambda t: (('_' in t or '$' in t), len(t)), reverse=True)
        return oracle_terms[0]
        
    # 2. Meaningful 2-word or 3-word phrase with non-stopwords
    words = re.findall(r'\b[A-Za-z0-9_\$-\']+\b', clean_opt)
    best_phrases = []
    for length in [2, 3]:
        for i in range(len(words) - length + 1):
            phrase = " ".join(words[i:i+length])
            pl = phrase.lower()
            if f" {pl} " not in wrong_combined_text:
                non_stops = [w for w in words[i:i+length] if w.lower() not in STOPWORDS]
                if len(non_stops) >= 1:
                    score = len(non_stops) * 2 + (5 if any(w[0].isupper() for w in words[i:i+length]) else 0)
                    best_phrases.append((score, phrase))
    if best_phrases:
        best_phrases.sort(key=lambda p: p[0], reverse=True)
        return best_phrases[0][1]

    # 3. Single distinctive word
    for w in words:
        wl = w.lower()
        if wl not in STOPWORDS and len(w) >= 4 and f" {wl} " not in wrong_combined_text:
            return w
            
    return None

def extract_keywords_for_question(q):
    correct_keys = set(q.get('correct', []))
    correct_opts = [o for o in q.get('options', []) if (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    wrong_opts = [o for o in q.get('options', []) if not (o.get('key') in correct_keys or o.get('letter') in correct_keys)]
    
    wrong_combined_text = " " + " ".join([clean_text(o['text']).lower() for o in wrong_opts]) + " "
    
    keywords = []
    for opt in correct_opts:
        disc = find_best_discriminator_for_option(opt['text'], wrong_combined_text)
        if disc and disc not in keywords and not any(disc.lower() == k.lower() for k in keywords):
            keywords.append(disc)
            
    if len(keywords) < len(correct_opts) or len(keywords) < 2:
        for opt in correct_opts:
            clean_opt = clean_text(opt['text'])
            terms = re.findall(r'\b[A-Za-z0-9_\$]{3,}\b', clean_opt)
            for tok in terms:
                tl = tok.lower()
                if tl not in STOPWORDS and f" {tl} " not in wrong_combined_text and tok not in keywords:
                    keywords.append(tok)
                    if len(keywords) >= 3:
                        break
                        
    # Fallback if somehow still empty (e.g. Q15 of 078 or single-choice identical structures)
    if not keywords:
        for ct in [clean_text(o['text']) for o in correct_opts]:
            words = ct.split()
            for length in [4, 3, 2]:
                for i in range(len(words) - length + 1):
                    ph = " ".join(words[i:i+length])
                    if f" {ph.lower()} " not in wrong_combined_text:
                        keywords.append(ph)
                        break
                if keywords: break
            if keywords: break
            
    return keywords[:4]

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

def process_exam_file(filepath, dry_run=False):
    print(f"\nProcessing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        questions = json.load(f)
        
    updated = 0
    for q in questions:
        kws = extract_keywords_for_question(q)
        anchor = extract_anchor_for_question(q)
        q['mnemonic'] = {
            'keywords': kws,
            'anchor': anchor
        }
        updated += 1
        
    print(f"Enriched {updated}/{len(questions)} questions with mnemonic data.")
    
    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"Successfully saved {filepath}")
    else:
        print("[Dry Run] Did not write to disk.")

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    for exam in ['1z0-078.json', '1z0-083.json']:
        fp = os.path.join(data_dir, exam)
        process_exam_file(fp, dry_run=False)
