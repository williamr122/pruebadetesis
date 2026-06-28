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
accessors = json_data['accessors']
buffer_views = json_data['bufferViews']

# Load base positions
pos_accessor = accessors[primitives['attributes']['POSITION']]
pos_offset = buffer_views[pos_accessor['bufferView']]['byteOffset'] + pos_accessor.get('byteOffset', 0)
base_positions = np.frombuffer(binary_data[pos_offset : pos_offset + pos_accessor['count'] * 12], dtype=np.float32).reshape((-1, 3))

# Load target offsets (boca index 0, ojo index 1)
def get_accessor_data(accessor_idx):
    accessor = accessors[accessor_idx]
    count = accessor['count']
    data = np.zeros((count, 3), dtype=np.float32)
    if 'bufferView' in accessor:
        bv = buffer_views[accessor['bufferView']]
        offset = bv.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        f_data = binary_data[offset : offset + count * 12]
        data = np.frombuffer(f_data, dtype=np.float32).reshape((count, 3))
    elif 'sparse' in accessor:
        sparse = accessor['sparse']
        s_count = sparse['count']
        indices_bv = buffer_views[sparse['indices']['bufferView']]
        indices_offset = indices_bv.get('byteOffset', 0)
        indices_data = binary_data[indices_offset : indices_offset + s_count * 2]
        indices = np.frombuffer(indices_data, dtype=np.uint16)
        values_bv = buffer_views[sparse['values']['bufferView']]
        values_offset = values_bv.get('byteOffset', 0)
        values_data = binary_data[values_offset : values_offset + s_count * 12]
        values = np.frombuffer(values_data, dtype=np.float32).reshape((s_count, 3))
        for i, idx in enumerate(indices):
            data[idx] = values[i]
    return data

boca_offsets = get_accessor_data(targets[0]['POSITION'])
ojo_offsets = get_accessor_data(targets[1]['POSITION'])

# Define proposed factor logic
def get_factor(y, z):
    absY = abs(y)
    if absY >= 0.08 or z >= -0.12:
        return 0.0
    elif absY > 0.05:
        return (0.08 - absY) / 0.03
    return 1.0

# Verify beak vertices that move the beak tip (Z <= -0.19, absY <= 0.047)
beak_factors = []
for i in range(len(base_positions)):
    x, y, z = base_positions[i]
    if x > 0.40 and abs(y) <= 0.047 and z <= -0.19:
        beak_factors.append(get_factor(y, z))

# Verify eye vertices (ojo offset > 0.01)
eye_factors = []
for i in range(len(base_positions)):
    x, y, z = base_positions[i]
    if np.linalg.norm(ojo_offsets[i]) > 0.01:
        eye_factors.append(get_factor(y, z))

print(f"Beak vertices verified: {len(beak_factors)}")
print(f"Min beak factor: {min(beak_factors):.4f}")

print(f"\nEye vertices verified: {len(eye_factors)}")
print(f"Max eye factor: {max(eye_factors):.4f}")
