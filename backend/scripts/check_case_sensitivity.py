import os
import ast
import sys

def check_path_exists_case_sensitive(root, parts):
    """
    Checks if path constructed from parts exists in root with exact casing.
    Returns (True, None) if exists.
    Returns (False, message) if mismatch or missing.
    """
    current_path = root
    params_checked = []
    
    for i, part in enumerate(parts):
        try:
            entries = os.listdir(current_path)
        except OSError:
            # Not a directory, maybe previous part was a file?
            # If so, we can't look inside it.
            return False, f"Cannot look inside {current_path}"
            
        if part in entries:
            current_path = os.path.join(current_path, part)
            params_checked.append(part)
            continue
            
        # Check if it exists with different case
        for entry in entries:
            if entry.lower() == part.lower():
                return False, f"Case mismatch! Expected '{part}' but found '{entry}' in '{current_path}'"
        
        # Check if it's a .py file (imports often omit .py)
        if i == len(parts) - 1:
            py_part = part + ".py"
            if py_part in entries:
                return True, None
            for entry in entries:
                if entry.lower() == py_part.lower():
                    return False, f"Case mismatch! Expected '{py_part}' but found '{entry}' in '{current_path}'"

        # Check if it is a package (dir with __init__.py)
        # Verify if directory exists but was missed above? No, we checked part in entries.
        
        return False, f"Module/File '{part}' not found in '{current_path}'"
        
    return True, None

def process_file(file_path, backend_root):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        return

    for node in ast.walk(tree):
        module_name = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('apps.') or alias.name.startswith('config.'):
                    module_name = alias.name
                    parts = module_name.split('.')
                    ok, msg = check_path_exists_case_sensitive(backend_root, parts)
                    if not ok:
                        print(f"File: {file_path}")
                        print(f"  Import: {module_name}")
                        print(f"  Error: {msg}")
                        print("-" * 20)

        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module.startswith('apps.') or node.module.startswith('config.')):
                module_name = node.module
                parts = module_name.split('.')
                ok, msg = check_path_exists_case_sensitive(backend_root, parts)
                if not ok:
                    print(f"File: {file_path}")
                    print(f"  Import: {module_name}")
                    print(f"  Error: {msg}")
                    print("-" * 20)

def main():
    # Assume script is in backend/scripts/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.dirname(script_dir)
    
    print(f"Scanning backend at {backend_root}...")
    
    for root, dirs, files in os.walk(backend_root):
        if '.git' in root or '__pycache__' in root or 'venv' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                process_file(full_path, backend_root)

if __name__ == "__main__":
    main()
