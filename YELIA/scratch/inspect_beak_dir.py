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

# Filter vertices that are at the front (X > 0.45) and near center left-right (abs(Y) < 0.05)
# Let's separate them by whether their boca Z offset is positive (moving up) or negative (moving down)
up_beak = []
down_beak = []
static_beak = []

for i in range(len(base_positions)):
    x, y, z = base_positions[i]
    if x > 0.40 and abs(y) < 0.05:
        z_offset = boca_offsets[i][2]
        if z_offset > 0.005:
            up_beak.append((i, x, y, z, z_offset))
        elif z_offset < -0.005:
            down_beak.append((i, x, y, z, z_offset))
        else:
            static_beak.append((i, x, y, z, z_offset))

print(f"Up beak vertices (Z offset > 0.005): {len(up_beak)}")
print(f"Down beak vertices (Z offset < -0.005): {len(down_beak)}")
print(f"Static beak vertices: {len(static_beak)}")

if len(up_beak) > 0 and len(down_beak) > 0:
    print("\nSample Up Beak Vertices:")
    for v in up_beak[:5]:
        print(f"  Index {v[0]}: Pos=[{v[1]:.3f}, {v[2]:.3f}, {v[3]:.3f}], ZOffset={v[4]:.4f}")
    print("\nSample Down Beak Vertices:")
    for v in down_beak[:5]:
        print(f"  Index {v[0]}: Pos=[{v[1]:.3f}, {v[2]:.3f}, {v[3]:.3f}], ZOffset={v[4]:.4f}")
else:
    print("No matching vertices in both categories.")
