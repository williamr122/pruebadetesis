import struct
import json

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA%20Y%20WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"
# Let's fix path to be standard
glb_path = glb_path.replace('%20', ' ')

with open(glb_path, 'rb') as f:
    header = f.read(12)
    magic, version, length = struct.unpack('<III', header)
    chunk_header = f.read(8)
    chunk_length, chunk_type = struct.unpack('<II', chunk_header)
    json_bytes = f.read(chunk_length)
    json_data = json.loads(json_bytes.decode('utf-8'))

materials = json_data.get('materials', [])
images = json_data.get('images', [])

print("Materials:")
for idx, mat in enumerate(materials):
    print(f"  Material {idx}: '{mat.get('name', '')}'")

meshes = json_data.get('meshes', [])
for idx, mesh in enumerate(meshes):
    print(f"\nMesh {idx}: '{mesh.get('name', '')}'")
    for prim_idx, prim in enumerate(mesh.get('primitives', [])):
        mat_idx = prim.get('material')
        mat_name = materials[mat_idx].get('name', '') if mat_idx is not None else 'None'
        print(f"  Primitive {prim_idx}: Material index={mat_idx} ('{mat_name}')")
