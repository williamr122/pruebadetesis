import json
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
content_path = project_root / "backend" / "content" / "course_content.json"

# Load existing content
with content_path.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)

# Loop and update units
for unit in data.get("units", []):
    unit_id = unit.get("id")
    unit_title = unit.get("title", f"Unidad {unit_id}")
    
    # Extract existing text previews for PDF and Workshop
    old_pdf_preview = ""
    old_workshop_preview = ""
    
    for res in unit.get("resources", []):
        if res.get("type") == "unit_content":
            old_pdf_preview = res.get("text_preview", "")
        elif res.get("type") == "workshop":
            old_workshop_preview = res.get("text_preview", "")
            
    # Define new resource list
    new_resources = [
        {
            "unit_id": unit_id,
            "unit_title": unit_title,
            "type": "pdf",
            "title": f"📄 PDF Unidad {unit_id}",
            "description": f"Documento de lectura principal para la Unidad {unit_id}.",
            "source": f"/resources/RECOMENDACION_DE_RECURSOS_YELIA4AP/u{unit_id}/pdf.pdf",
            "text_preview": old_pdf_preview,
            "visible": True
        },
        {
            "unit_id": unit_id,
            "unit_title": unit_title,
            "type": "presentation",
            "title": f"📊 Presentación Unidad {unit_id}",
            "description": f"Diapositivas y material visual explicativo para la Unidad {unit_id}.",
            "source": f"/resources/RECOMENDACION_DE_RECURSOS_YELIA4AP/u{unit_id}/presentation.pptx",
            "text_preview": f"Material visual y diapositivas (PowerPoint) de la Unidad {unit_id} para estudio individual.",
            "visible": True
        },
        {
            "unit_id": unit_id,
            "unit_title": unit_title,
            "type": "workshop",
            "title": f"📝 Taller Unidad {unit_id}",
            "description": f"Taller práctico y actividades de autoevaluación para la Unidad {unit_id}.",
            "source": f"/resources/RECOMENDACION_DE_RECURSOS_YELIA4AP/u{unit_id}/workshop.pdf",
            "text_preview": old_workshop_preview,
            "visible": True
        },
        {
            "unit_id": unit_id,
            "unit_title": unit_title,
            "type": "lesson",
            "title": f"📘 Lección Unidad {unit_id}",
            "description": f"Cuestionario de autoevaluación (PDF) de la Unidad {unit_id}.",
            "source": f"/resources/RECOMENDACION_DE_RECURSOS_YELIA4AP/u{unit_id}/lesson.pdf",
            "text_preview": f"Cuestionario oficial impreso (PDF) de la lección autoevaluativa para la Unidad {unit_id}.",
            "visible": True
        },
        {
            "unit_id": unit_id,
            "unit_title": unit_title,
            "type": "exam",
            "title": f"✅ Examen Unidad {unit_id}",
            "description": f"Evaluación formativa del docente (PDF) para la Unidad {unit_id}.",
            "source": f"/resources/RECOMENDACION_DE_RECURSOS_YELIA4AP/u{unit_id}/exam.pdf",
            "text_preview": f"Banco oficial de preguntas (PDF) correspondiente al examen de la Unidad {unit_id}.",
            "visible": True
        }
    ]
    
    # Update unit resources
    unit["resources"] = new_resources
    print(f"Updated Unit {unit_id} with {len(new_resources)} resources.")

# Write back
with content_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
print("Finished saving updated course_content.json!")
