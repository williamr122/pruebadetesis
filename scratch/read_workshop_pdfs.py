import pypdf
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
base_dir = project_root / "frontend" / "public" / "resources" / "RECOMENDACION_DE_RECURSOS_YELIA4AP"

pdf_path = base_dir / "u1" / "workshop.pdf"
reader = pypdf.PdfReader(pdf_path)
for i, page in enumerate(reader.pages):
    print(f"Page {i+1}:")
    print(page.extract_text())
