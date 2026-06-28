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

# Load target offsets (boca index 0)
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

# Find beak vertices (boca offset > 0.005)
beak_z = []
for i in range(len(base_positions)):
    if np.linalg.norm(boca_offsets[i]) > 0.005:
        beak_z.append(base_positions[i][2])

beak_z = np.array(beak_z)
print(f"Beak vertices total count: {len(beak_z)}")
print(f"Z Range of beak vertices: Min={np.min(beak_z):.4f}, Max={np.max(beak_z):.4f}")

# Distribution of Z
for threshold in [-0.10, -0.11, -0.12, -0.13, -0.14, -0.15]:
    count = np.sum(beak_z < threshold)
    print(f"  Z < {threshold:.2f}: {count}/{len(beak_z)} ({count/len(beak_z)*100:.1f}%)")
