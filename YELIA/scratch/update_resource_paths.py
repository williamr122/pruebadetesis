import os

filepath = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\backend\content\course_content.json"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = content.replace("RECOMENDACION_DE_RECURSOS_YELIA4AP", "RECURSOS_YELIA4AP")
new_content = new_content.replace("RECOMENDACION DE RECURSOS YELIA4AP", "RECURSOS_YELIA4AP")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("course_content.json updated successfully!")
