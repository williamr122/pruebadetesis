import struct
import json
import numpy as np

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA%20Y%20WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"
glb_path = glb_path.replace('%20', ' ')

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

# Load ojo offsets (target 1)
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

ojo_offsets = get_accessor_data(targets[1]['POSITION'])
movements_o = np.linalg.norm(ojo_offsets, axis=1)

# Find eye vertices (moved by 'ojo' with Y != 0)
eye_indices = np.where(movements_o > 0.01)[0]
print(f"Total eye vertices found: {len(eye_indices)}")

# Right eye: Y > 0.05
r_eye_indices = [idx for idx in eye_indices if base_positions[idx][1] > 0.05]
# Left eye: Y < -0.05
l_eye_indices = [idx for idx in eye_indices if base_positions[idx][1] < -0.05]

print(f"Right eye vertices: {len(r_eye_indices)}")
if len(r_eye_indices) > 0:
    r_pos = base_positions[r_eye_indices]
    print(f"  Right eye Y range: Min={np.min(r_pos[:, 1]):.4f}, Max={np.max(r_pos[:, 1]):.4f}")

print(f"Left eye vertices: {len(l_eye_indices)}")
if len(l_eye_indices) > 0:
    l_pos = base_positions[l_eye_indices]
    print(f"  Left eye Y range: Min={np.min(l_pos[:, 1]):.4f}, Max={np.max(l_pos[:, 1]):.4f}")
