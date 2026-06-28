import os

def find_resources_sources():
    search_dirs = [
        r"c:\Users\USER\Downloads",
        r"c:\Users\USER\Desktop",
        r"c:\Users\USER\Documents",
    ]
    
    print("Searching for resource files...")
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            # Exclude standard directories we shouldn't scan
            if any(x in root for x in [".git", "node_modules", ".venv", "env", "AppData"]):
                continue
            for file in files:
                f_upper = file.upper()
                if "RECOMENDACION" in f_upper or "RECURSO" in f_upper:
                    print(f"File: {os.path.join(root, file)}")
            for directory in dirs:
                d_upper = directory.upper()
                if "RECOMENDACION" in d_upper or "RECURSO" in d_upper:
                    print(f"Directory: {os.path.join(root, directory)}")

if __name__ == "__main__":
    find_resources_sources()
