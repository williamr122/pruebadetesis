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

skins = json_data.get('skins', [])
nodes = json_data.get('nodes', [])

print(f"Skins count: {len(skins)}")
for idx, skin in enumerate(skins):
    print(f"  Skin {idx}: Joints count: {len(skin.get('joints', []))}")

print(f"Nodes count: {len(nodes)}")
for idx, node in enumerate(nodes):
    name = node.get('name', '')
    mesh = node.get('mesh')
    skin = node.get('skin')
    print(f"  Node {idx}: '{name}' - Mesh: {mesh} - Skin: {skin}")
