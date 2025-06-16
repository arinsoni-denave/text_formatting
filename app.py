import os
import json
import re
import csv
from pathlib import Path

def remove_bold_from_bullets(text):
    lines = text.splitlines()
    new_lines = []
    removed_bold = []
    for line in lines:
        if line.strip().startswith('- '):
            def replacer(m):
                removed_bold.append(m.group(1))
                return m.group(1)
            clean_line = re.sub(r'\*\*(.+?)\*\*', replacer, line)
            new_lines.append(clean_line)
        else:
            new_lines.append(line)
    return '\n'.join(new_lines), removed_bold

def remove_all_bold(text):
    return re.sub(r'\*\*(.+?)\*\*', r'\1', text)

def keep_only_letters(text):
    return re.sub(r'[^A-Za-z]+', '', text)

def validate_letters_only_unchanged(original, cleaned):
    orig_letters = keep_only_letters(remove_all_bold(original))
    clean_letters = keep_only_letters(remove_all_bold(cleaned))
    return orig_letters == clean_letters

def process_file(filepath, key_path):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ref = data
    validation_status = "N/A"
    try:
        for k in key_path[:-1]:
            ref = ref[k]
        last_key = key_path[-1]
        if last_key in ref and isinstance(ref[last_key], str):
            original_text = ref[last_key]
            cleaned_text, removed_bold = remove_bold_from_bullets(original_text)
            if cleaned_text != original_text:
                valid = validate_letters_only_unchanged(original_text, cleaned_text)
                validation_status = "True" if valid else "False"
                ref[last_key] = cleaned_text
                return True, validation_status, data
        return False, validation_status, data
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, "Error", data

def process_folder(input_folder, output_folder, key_path, log_csv='bold_removal_log.csv'):
    log = []
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    for root, dirs, files in os.walk(input_folder):
        for fname in files:
            if fname.endswith('.json'):
                full_path = Path(root) / fname
                changed, validation_status, new_data = process_file(str(full_path), key_path)
                rel_path = full_path.relative_to(input_folder)
                out_path = output_folder / rel_path

                if changed:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, indent=2, ensure_ascii=False)
                
                log.append({
                    'filename': str(rel_path),
                    'changed': changed,
                    'validation_status': validation_status
                })

    log_path = output_folder / log_csv
    with open(log_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'changed', 'validation_status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in log:
            writer.writerow(row)
    print(f"Done. Changed files saved to {output_folder}. Log written to {log_path}")

if __name__ == "__main__":
    input_folder = r"Test"       
    output_folder = r"Result"      
    key_path = ['personalized narrative', 'tele scripts', 'customer engagement suite', 'objection handling']
    process_folder(input_folder, output_folder, key_path)
