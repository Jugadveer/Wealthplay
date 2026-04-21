import lightgbm as lgb
import os

model_path = r'd:\Bios\ml\models\dir_model.txt'
print(f"Testing model: {model_path}")

try:
    bst = lgb.Booster(model_file=model_path)
    print("SUCCESS: Model loaded normally")
except Exception as e:
    print(f"FAILED: {e}")

# Try loading with slower/linear parsing by removing tree_sizes if it fails
print("\nAttempting fix: removing tree_sizes line...")
with open(model_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = [l for l in lines if not l.startswith('tree_sizes=')]

with open(model_path + '.tmp', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)

try:
    bst = lgb.Booster(model_file=model_path + '.tmp')
    print("SUCCESS: Model loaded after removing tree_sizes and forcing LF")
except Exception as e:
    # If it still fails, it might be the model content itself or Python 3.13
    print(f"FAILED even after fix: {e}")
