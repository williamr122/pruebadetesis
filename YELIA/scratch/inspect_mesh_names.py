import struct
import json

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"
glb_path = glb_path.replace('%20', ' ')

with open(glb_path, 'rb') as f:
    header = f.read(12)
    magic, version, length = struct.unpack('<III', header)
    chunk_header = f.read(8)
    chunk_length, chunk_type = struct.unpack('<II', chunk_header)
    json_bytes = f.read(chunk_length)
    json_data = json.loads(json_bytes.decode('utf-8'))

meshes = json_data.get('meshes', [])
nodes = json_data.get('nodes', [])

print("Meshes:")
for idx, mesh in enumerate(meshes):
    print(f"  Mesh {idx}: Name='{mesh.get('name', '')}'")
    for prim_idx, prim in enumerate(mesh.get('primitives', [])):
        print(f"    Primitive {prim_idx}: Attributes={list(prim.get('attributes', {}).keys())}")

print("\nNodes:")
for idx, node in enumerate(nodes):
    print(f"  Node {idx}: Name='{node.get('name', '')}', Mesh={node.get('mesh')}, Translation={node.get('translation')}, Rotation={node.get('rotation')}, Scale={node.get('scale')}")
