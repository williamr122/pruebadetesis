import os
import shutil

def path_safe(p):
    return "\\\\?\\" + os.path.abspath(p)

def copy_file_safe(src, dst):
    try:
        src_win = path_safe(src)
        dst_win = path_safe(dst)
        os.makedirs(os.path.dirname(dst_win), exist_ok=True)
        # If target exists and is locked, we can try to write to it directly
        shutil.copy2(src_win, dst_win)
        print(f"Copied: {os.path.basename(dst)}")
    except Exception as e:
        print(f"Error copying {src} -> {dst}: {e}")

def clean_copy():
    # Detect project root dynamically
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    src_external = r"c:\Users\USER\Downloads\DOMENICA\RECOMENDACION DE RECURSOS YELIA4AP"
    src_local = os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION DE RECURSOS YELIA4AP")
    
    # If the external folder exists (e.g. on the user's main PC), sync it to the local project folder first
    if os.path.exists(src_external):
        print(f"Syncing external source {src_external} to local raw folder: {src_local}")
        for root, dirs, files in os.walk(src_external):
            for f in files:
                src_file = os.path.join(root, f)
                rel = os.path.relpath(src_file, src_external)
                dst_file = os.path.join(src_local, rel)
                copy_file_safe(src_file, dst_file)
    else:
        print(f"External source not found. Using local raw folder: {src_local}")

    dest_dirs = [
        os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP"),
        os.path.join(project_root, "backend", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP")
    ]
    
    # Map files from local raw folder to normalized folders
    print(f"Mapping and copying files from: {src_local}")

    # Mapping configuration for underscore destinations
    mapping = {
        # Unit 1
        "UNIDAD 1 Introducción a la Programación Orientada a Objetos/PDF Unidad 1/UNIDAD 1 Introducción a la Programación Orientada a Objetos.pdf": "u1/pdf.pdf",
        "UNIDAD 1 Introducción a la Programación Orientada a Objetos/Presentación Unidad 1/Unidad1.pptx": "u1/presentation.pptx",
        "UNIDAD 1 Introducción a la Programación Orientada a Objetos/Taller Unidad 1/TALLER UNIDAD 1.pdf": "u1/workshop.pdf",
        "UNIDAD 1 Introducción a la Programación Orientada a Objetos/Lección Unidad 1 (5 preguntas)/Lección Unidad 1.pdf": "u1/lesson.pdf",
        "UNIDAD 1 Introducción a la Programación Orientada a Objetos/Examen Unidad 1 (10 preguntas)/Examen Unidad 1.pdf": "u1/exam.pdf",
        
        # Unit 2
        "UNIDAD 2 Lenguaje de Modelado Unificado/PDF Unidad 2/UNIDAD 2 Lenguaje de Modelado Unificado.pdf": "u2/pdf.pdf",
        "UNIDAD 2 Lenguaje de Modelado Unificado/Presentación Unidad 2/Unidad2.pptx": "u2/presentation.pptx",
        "UNIDAD 2 Lenguaje de Modelado Unificado/Taller Unidad 2/TALLER UNIDAD 2.pdf": "u2/workshop.pdf",
        "UNIDAD 2 Lenguaje de Modelado Unificado/Lección Unidad 2 (5 preguntas)/Lección Unidad 2.pdf": "u2/lesson.pdf",
        "UNIDAD 2 Lenguaje de Modelado Unificado/Examen Unidad 2 (10 preguntas)/Examen Unidad 2.pdf": "u2/exam.pdf",
        
        # Unit 3
        "UNIDAD 3 Aplicación de la Programación Orientada a Objetos/PDF Unidad 3/UNIDAD 3 Aplicación de la Programación Orientada a Objetos.pdf": "u3/pdf.pdf",
        "UNIDAD 3 Aplicación de la Programación Orientada a Objetos/Presentación Unidad 3/Unidad 3.pptx": "u3/presentation.pptx",
        "UNIDAD 3 Aplicación de la Programación Orientada a Objetos/Taller Unidad 3/Taller Unidad 3.pdf": "u3/workshop.pdf",
        "UNIDAD 3 Aplicación de la Programación Orientada a Objetos/Lección Unidad 3 (5 preguntas)/Lección Unidad 3.pdf": "u3/lesson.pdf",
        "UNIDAD 3 Aplicación de la Programación Orientada a Objetos/Examen Unidad 3 (10 preguntas)/Examen Unidad 3.pdf": "u3/exam.pdf",
        
        # Unit 4
        "UNIDAD 4 Acceso a Archivos y Base de Datos/PDF Unidad 4/UNIDAD 4 Acceso a Archivos y Base de Datos.pdf": "u4/pdf.pdf",
        "UNIDAD 4 Acceso a Archivos y Base de Datos/Presentación Unidad 4/Unidad 4.pptx": "u4/presentation.pptx",
        "UNIDAD 4 Acceso a Archivos y Base de Datos/Taller Unidad 4/Taller Unidad 4.pdf": "u4/workshop.pdf",
        "UNIDAD 4 Acceso a Archivos y Base de Datos/Lección Unidad 4 (5 preguntas)/Lección Unidad 4.pdf": "u4/lesson.pdf",
        "UNIDAD 4 Acceso a Archivos y Base de Datos/Examen Unidad 4 (10 preguntas)/Examen Unidad 4.pdf": "u4/exam.pdf",
        
        # Diagnostic
        "PRUEBA DE DIAGNOSTICO/PRUEBA DE DIAGNOSTICO EN BASE A  LAS 4 UNIDADES.pdf": "u0/diagnostic.pdf"
    }

    for dst_base in dest_dirs:
        print(f"\nProcessing target base: {dst_base}")
        for rel_src, rel_dst in mapping.items():
            src_file_alt1 = os.path.join(src_local, rel_src.replace("/", "\\"))
            src_file_alt2 = os.path.join(src_local, rel_src)
            src_file = src_file_alt1 if os.path.exists(path_safe(src_file_alt1)) else src_file_alt2
            
            dst_file = os.path.join(dst_base, rel_dst.replace("/", "\\"))
            
            if os.path.exists(path_safe(src_file)):
                copy_file_safe(src_file, dst_file)
            else:
                print(f"WARNING: Source file not found: {src_file}")

if __name__ == "__main__":
    clean_copy()
