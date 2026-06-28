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
        chunk_header = f.read(8)
        chunk_length, chunk_type = struct.unpack('<II', chunk_header)
        json_bytes = f.read(chunk_length)
        json_data = json.loads(json_bytes.decode('utf-8'))
        
        print(f"\nFile: {filename}")
        accessors = json_data['accessors']
        meshes = json_data.get('meshes', [])
        for idx, mesh in enumerate(meshes):
            prim = mesh['primitives'][0]
            pos_acc = accessors[prim['attributes']['POSITION']]
            indices_acc = accessors[prim['indices']] if 'indices' in prim else None
            
            vertex_count = pos_acc['count']
            index_count = indices_acc['count'] if indices_acc else 0
            
            targets = prim.get('targets', [])
            print(f"  Mesh {idx}: '{mesh.get('name', '')}' - Vertices: {vertex_count}, Indices: {index_count}, Morph Targets count: {len(targets)}")
