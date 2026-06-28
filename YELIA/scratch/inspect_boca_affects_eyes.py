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

# Load boca offsets (target 0)
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

# Filter vertices in the eye region (Y > 0.15)
eye_indices = np.where(base_positions[:, 1] > 0.15)[0]
print(f"Total vertices in eye region (Y > 0.15): {len(eye_indices)}")

# Check movement in 'boca' for these eye vertices
boca_eye_offsets = boca_offsets[eye_indices]
boca_eye_norms = np.linalg.norm(boca_eye_offsets, axis=1)

print(f"Number of eye vertices affected by 'boca' (offset > 0.001): {np.sum(boca_eye_norms > 0.001)}")
print(f"Max displacement in 'boca' in eye region: {np.max(boca_eye_norms):.4f}")

if np.max(boca_eye_norms) > 0.001:
    top_eye_indices = np.argsort(boca_eye_norms)[::-1][:5]
    print("\nTop 5 eye vertices affected by 'boca':")
    for local_idx in top_eye_indices:
        global_idx = eye_indices[local_idx]
        print(f"  Index {global_idx}: Base={base_positions[global_idx]}, Offset={boca_offsets[global_idx]}, Norm={boca_eye_norms[local_idx]:.4f}")
