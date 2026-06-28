import os
import shutil
import sys

def copy_folder(src, dst):
    print(f"Copying from {src} to {dst}...")
    if not os.path.exists(src):
        print(f"Source directory does not exist: {src}")
        return False
    if os.path.exists(dst):
        print(f"Destination directory already exists, removing it first: {dst}")
        shutil.rmtree(dst)
    try:
        shutil.copytree(src, dst)
        print("Success!")
        return True
    except Exception as e:
        print(f"Error copying: {e}")
        return False

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    src_dir = os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION DE RECURSOS YELIA4AP")
    dst_frontend = os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP")
    dst_backend = os.path.join(project_root, "backend", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP")
    
    # 1. Copy to frontend destination
    copy_folder(src_dir, dst_frontend)
    # 2. Copy to backend destination
    copy_folder(src_dir, dst_backend)
