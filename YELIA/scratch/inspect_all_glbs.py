import struct
import json
import os

folder = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\avatars3d"

for filename in os.listdir(folder):
    if not filename.endswith('.glb'):
        continue
    glb_path = os.path.join(folder, filename)
    with open(glb_path, 'rb') as f:
        header = f.read(12)
        magic, version, length = struct.unpack('<III', header)
        
        # Read chunk 0 (JSON)
        chunk_header = f.read(8)
        chunk_length, chunk_type = struct.unpack('<II', chunk_header)
        
        json_bytes = f.read(chunk_length)
        json_data = json.loads(json_bytes.decode('utf-8'))
        
        print(f"\nFile: {filename}")
        meshes = json_data.get('meshes', [])
        print(f"Found {len(meshes)} meshes:")
        for idx, mesh in enumerate(meshes):
            name = mesh.get('name', '')
            primitives = mesh.get('primitives', [])
            targets = primitives[0].get('targets', []) if primitives else []
            extras = mesh.get('extras', {})
            target_names = extras.get('targetNames', [])
            print(f"  Mesh {idx}: '{name}' - Morph Targets: {target_names}")
