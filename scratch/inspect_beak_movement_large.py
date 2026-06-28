import struct
import json
import numpy as np

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"

with open(glb_path, 'rb') as f:
    header = f.read(12)
    magic, version, length = struct.unpack('<III', header)
    chunk_header = f.read(8)
    chunk_length, chunk_type = struct.unpack('<II', chunk_header)
    json_bytes = f.read(chunk_length)
    json_data = json.loads(json_bytes.decode('utf-8'))
    chunk1_header = f.read(8)
    c1_length, c1_type = struct.unpack('<II', chunk1_header)
    binary_data = f.read(c1_length)

mesh = json_data['meshes'][1]
primitives = mesh['primitives'][0]
targets = primitives['targets']

# Load base positions
pos_accessor = json_data['accessors'][primitives['attributes']['POSITION']]
pos_offset = json_data['bufferViews'][pos_accessor['bufferView']]['byteOffset'] + pos_accessor.get('byteOffset', 0)
base_positions = np.frombuffer(binary_data[pos_offset : pos_offset + pos_accessor['count'] * 12], dtype=np.float32).reshape((-1, 3))

# Load target offsets
def get_accessor_data(accessor_idx):
    accessor = json_data['accessors'][accessor_idx]
    count = accessor['count']
    if 'bufferView' in accessor:
        offset = json_data['bufferViews'][accessor['bufferView']]['byteOffset'] + accessor.get('byteOffset', 0)
        return np.frombuffer(binary_data[offset : offset + count * 12], dtype=np.float32).reshape((-1, 3))
    elif 'sparse' in accessor:
        sparse = accessor['sparse']
        s_count = sparse['count']
        indices = np.frombuffer(binary_data[json_data['bufferViews'][sparse['indices']['bufferView']]['byteOffset'] : json_data['bufferViews'][sparse['indices']['bufferView']]['byteOffset'] + s_count * 2], dtype=np.uint16)
        values = np.frombuffer(binary_data[json_data['bufferViews'][sparse['values']['bufferView']]['byteOffset'] : json_data['bufferViews'][sparse['values']['bufferView']]['byteOffset'] + s_count * 12], dtype=np.float32).reshape((-1, 3))
        data = np.zeros((count, 3), dtype=np.float32)
        for i, idx in enumerate(indices):
            data[idx] = values[i]
        return data

boca_offsets = get_accessor_data(targets[0]['POSITION'])
ojo_offsets = get_accessor_data(targets[1]['POSITION'])

# For 'boca' morph target (target 0), find top 5 vertices moving in Y
boca_y_move = np.abs(boca_offsets[:, 1])
top_y_b = np.argsort(boca_y_move)[::-1][:5]
print("\n'boca' Top 5 vertical (Y) movements:")
for idx in top_y_b:
    print(f"  Index {idx}: Base={base_positions[idx]}, Offset={boca_offsets[idx]}")

# For 'ojo' morph target (target 1), find top 5 vertices moving in Y
ojo_y_move = np.abs(ojo_offsets[:, 1])
top_y_o = np.argsort(ojo_y_move)[::-1][:5]
print("\n'ojo' Top 5 vertical (Y) movements:")
for idx in top_y_o:
    print(f"  Index {idx}: Base={base_positions[idx]}, Offset={ojo_offsets[idx]}")
