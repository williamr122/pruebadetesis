import struct
import json

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"

with open(glb_path, 'rb') as f:
    header = f.read(12)
    magic, version, length = struct.unpack('<III', header)
    print(f"Magic: {magic:x}, Version: {version}, Length: {length}")
    
    # Read chunk 0 (JSON)
    chunk_header = f.read(8)
    chunk_length, chunk_type = struct.unpack('<II', chunk_header)
    print(f"Chunk 0 Length: {chunk_length}, Type: {chunk_type:x}")
    
    json_bytes = f.read(chunk_length)
    json_data = json.loads(json_bytes.decode('utf-8'))
    
    # Let's inspect meshes
    meshes = json_data.get('meshes', [])
    print(f"Found {len(meshes)} meshes:")
    for idx, mesh in enumerate(meshes):
        name = mesh.get('name', '')
        primitives = mesh.get('primitives', [])
        targets = primitives[0].get('targets', []) if primitives else []
        extras = mesh.get('extras', {})
        target_names = extras.get('targetNames', [])
        print(f"  Mesh {idx}: '{name}' - Morph Targets count: {len(targets)} - Target Names: {target_names}")

    # Let's inspect nodes
    nodes = json_data.get('nodes', [])
    print(f"\nFound {len(nodes)} nodes:")
    for idx, node in enumerate(nodes):
        name = node.get('name', '')
        mesh_idx = node.get('mesh')
        scale = node.get('scale', [1, 1, 1])
        print(f"  Node {idx}: '{name}' - Mesh index: {mesh_idx} - Scale: {scale}")
