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

# Let's look at all front center beak vertices (X > 0.44, abs(Y) < 0.02)
# and find:
# 1. The maximum Z position of the lower beak (where ZOffset > 0)
# 2. The minimum Z position of the upper beak (where ZOffset == 0)
# 3. How they behave at different values of boca (0.0 to 1.0)
lower_beak = []
upper_beak = []

for i in range(len(base_positions)):
    x, y, z = base_positions[i]
    if x > 0.44 and abs(y) < 0.02:
        z_offset = boca_offsets[i][2]
        if z_offset > 0.005:
            lower_beak.append((i, x, y, z, z_offset))
        elif abs(z_offset) < 0.0001:
            upper_beak.append((i, x, y, z, z_offset))

print(f"Lower beak vertices: {len(lower_beak)}")
print(f"Upper beak vertices: {len(upper_beak)}")

if len(lower_beak) > 0 and len(upper_beak) > 0:
    # Let's find the highest lower beak vertex when boca = val
    # and the lowest upper beak vertex
    upper_z_min = min(v[3] for v in upper_beak)
    print(f"Static upper beak minimum Z: {upper_z_min:.4f}")
    
    # We want the highest lower beak vertex (with boca applied) to meet the static upper beak Z,
    # or just look at the gap/intersection at different boca values:
    for val in [0.0, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]:
        lower_z_max = max(v[3] + v[4] * val for v in lower_beak)
        diff = upper_z_min - lower_z_max
        status = "GAP" if diff > 0 else "INTERSECT"
        print(f"Boca = {val:.2f} -> Max Lower Beak Z: {lower_z_max:.4f}, Diff: {diff:+.4f} ({status})")
