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
    if 'sparse' in accessor:
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

# Print all vertices at the front center (X > 0.47, abs(Y) < 0.01) sorted by Z descending
beak_verts = []
for i in range(len(base_positions)):
    x, y, z = base_positions[i]
    if x > 0.47 and abs(y) < 0.01:
        beak_verts.append((i, x, y, z, boca_offsets[i][2]))

beak_verts.sort(key=lambda x: x[3], reverse=True)

print("Vertices at front center sorted by Z (descending):")
for v in beak_verts:
    print(f"Index {v[0]:5d}: Pos=[{v[1]:.4f}, {v[2]:.4f}, {v[3]:.4f}], Boca Z Offset={v[4]:.4f}")
