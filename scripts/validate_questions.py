"""
Question Dataset Validator for OracleDBA Certification Simulators
Validates JSON schemas, consistency between options and answers, and reports statistics.
"""

import json
import os
import sys

def validate_exam(json_path):
    filename = os.path.basename(json_path)
    print(f"\n==========================================")
    print(f" Validating: {filename}")
    print(f"==========================================")
    
    if not os.path.exists(json_path):
        print(f"ERROR: File not found: {json_path}")
        return False
        
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except Exception as e:
        print(f"ERROR: Invalid JSON file: {e}")
        return False
        
    errors = []
    warnings = []
    
    ids = [q.get('id') for q in questions]
    if len(ids) != len(set(ids)):
        duplicates = [x for x in ids if ids.count(x) > 1]
        errors.append(f"Duplicate question IDs found: {set(duplicates)}")
        
    domain_counts = {}
    status_counts = {}
    type_counts = {}
    
    for idx, q in enumerate(questions, 1):
        qid = q.get('id', f"index_{idx}")
        
        # Domain check
        domain = q.get('domain')
        if not domain:
            errors.append(f"Q#{qid}: Missing 'domain'")
        else:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
        # Review status
        status = q.get('review_status', 'unreviewed')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Type
        qtype = q.get('type')
        if qtype not in ['single', 'multiple']:
            errors.append(f"Q#{qid}: Invalid type '{qtype}'")
        type_counts[qtype] = type_counts.get(qtype, 0) + 1
        
        # Options
        options = q.get('options', [])
        if not options or len(options) < 2:
            errors.append(f"Q#{qid}: Question has fewer than 2 options")
            
        opt_keys = []
        for o in options:
            k = o.get('letter') or o.get('key')
            if not k:
                errors.append(f"Q#{qid}: Option missing letter/key")
            elif k in opt_keys:
                errors.append(f"Q#{qid}: Duplicate option key '{k}'")
            else:
                opt_keys.append(k)
                
        # Correct answers
        correct = q.get('correct', [])
        if not correct:
            errors.append(f"Q#{qid}: Missing 'correct' answers")
        else:
            for ans in correct:
                if ans not in opt_keys:
                    errors.append(f"Q#{qid}: Correct answer '{ans}' not found in options {opt_keys}")
                    
        # Select count
        select_count = q.get('select_count', 1)
        if len(correct) != select_count:
            errors.append(f"Q#{qid}: 'select_count' ({select_count}) does not match number of correct answers ({len(correct)})")
            
        if select_count == 1 and qtype != 'single':
            warnings.append(f"Q#{qid}: select_count is 1 but type is '{qtype}'")
        elif select_count > 1 and qtype != 'multiple':
            warnings.append(f"Q#{qid}: select_count is {select_count} but type is '{qtype}'")
            
        # Explanation
        if not q.get('explanation'):
            warnings.append(f"Q#{qid}: Missing explanation")

    print(f"Total questions: {len(questions)}")
    print(f"Domains: {domain_counts}")
    print(f"Review statuses: {status_counts}")
    print(f"Types: {type_counts}")
    
    if warnings:
        print(f"\n[!] Warnings ({len(warnings)}):")
        for w in warnings[:10]:
            print(f"  - {w}")
            
    if errors:
        print(f"\n[X] Errors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  - {e}")
        return False
    else:
        print("\n[OK] All integrity checks passed successfully!")
        return True

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    success = True
    for exam in ['1z0-078.json', '1z0-083.json']:
        filepath = os.path.join(data_dir, exam)
        if not validate_exam(filepath):
            success = False
            
    sys.exit(0 if success else 1)
