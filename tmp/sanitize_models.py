import os

models = [
    r'd:\Bios\ml\models\dir_model.txt',
    r'd:\Bios\ml\models\regime_model.txt',
    r'd:\Bios\ml\models\vol_model.txt'
]

for model_path in models:
    if not os.path.exists(model_path):
        print(f"Skipping {model_path} (not found)")
        continue
        
    print(f"Sanitizing {model_path}...")
    
    with open(model_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.splitlines()
    
    # Remove tree_sizes line if present
    # Force blank lines where expected
    new_lines = []
    for line in lines:
        if line.startswith('tree_sizes='):
            continue
        new_lines.append(line)
        
    # Write back with LF endings to see if it helps LightGBM parser
    with open(model_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(new_lines) + '\n')

print("All models sanitized.")
