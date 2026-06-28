import os
import shutil

def normalize_text(text):
    import unicodedata
    raw = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return raw.strip().lower()

def copy_robust():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    src_base = os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION DE RECURSOS YELIA4AP")
    dest_dirs = [
        os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP"),
        os.path.join(project_root, "backend", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP")
    ]

    if not os.path.exists(src_base):
        print(f"Source base does not exist: {src_base}")
        return

    # Walk directories beyond 260 chars on Windows
    src_base_win = "\\\\?\\" + os.path.abspath(src_base)
    all_files = []
    for root, dirs, files in os.walk(src_base_win):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, src_base_win)
            all_files.append((rel_path, full_path))

    print(f"Found {len(all_files)} total files in source.")

    for dest_base in dest_dirs:
        dest_base_win = "\\\\?\\" + os.path.abspath(dest_base)
        print(f"\nTarget directory: {dest_base_win}")
        if os.path.exists(dest_base_win):
            shutil.rmtree(dest_base_win)
        os.makedirs(dest_base_win, exist_ok=True)
        
        for rel_path, full_src in all_files:
            norm_rel = normalize_text(rel_path)
            unit = None
            target_rel = None
            
            # Determine unit
            if "unidad 1" in norm_rel or "unidad1" in norm_rel:
                unit = "u1"
            elif "unidad 2" in norm_rel or "unidad2" in norm_rel:
                unit = "u2"
            elif "unidad 3" in norm_rel or "unidad3" in norm_rel:
                unit = "u3"
            elif "unidad 4" in norm_rel or "unidad4" in norm_rel:
                unit = "u4"
            
            # Determine mapping
            if "diagnostico" in norm_rel:
                target_rel = "u0/diagnostic.pdf"
            elif unit:
                if "taller" in norm_rel:
                    target_rel = f"{unit}/workshop.pdf"
                elif "leccion" in norm_rel:
                    target_rel = f"{unit}/lesson.pdf"
                elif "examen" in norm_rel:
                    target_rel = f"{unit}/exam.pdf"
                elif "pdf" in norm_rel:
                    target_rel = f"{unit}/pdf.pdf"
                elif norm_rel.endswith(".pptx"):
                    target_rel = f"{unit}/presentation.pptx"

            if target_rel:
                dest_file = os.path.join(dest_base_win, target_rel.replace("/", "\\"))
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(full_src, dest_file)
                print(f"Copied {rel_path} -> {target_rel}")
            else:
                print(f"Skipped/Unmatched: {rel_path}")

if __name__ == "__main__":
    copy_robust()
