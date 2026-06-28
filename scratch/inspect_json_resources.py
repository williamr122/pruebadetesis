import json
from pathlib import Path

content_path = Path(r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\backend\content\course_content.json")

with content_path.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)

for unit in data.get("units", []):
    print(f"Unit {unit.get('id')}: {unit.get('title')}")
    for res in unit.get("resources", []):
        print(f"  Type: {res.get('type')}")
        print(f"  Title: {res.get('title')}")
        print(f"  Source: {res.get('source')}")
        print(f"  Preview length: {len(res.get('text_preview', '')) if res.get('text_preview') else 0}")
