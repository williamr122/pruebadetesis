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

# Let's find pairs of upper (static) and lower (moving) beak vertices that are at the same X, Y coordinates
# (within a tolerance of 0.005)
upper_verts = []
lower_verts = []

for i in range(len(base_positions)):
    x, y, z = base_positions[i]
    if x > 0.40 and abs(y) < 0.05:
        z_offset = boca_offsets[i][2]
        if z_offset > 0.005:
            lower_verts.append((i, x, y, z, z_offset))
        elif abs(z_offset) < 0.0001:
            upper_verts.append((i, x, y, z))

print(f"Found {len(upper_verts)} upper and {len(lower_verts)} lower beak vertices.")

# Find matching pairs
pairs = []
for l_idx, lx, ly, lz, loff in lower_verts:
    # Find the closest upper vertex in X and Y
    best_u = None
    best_dist = 9999.0
    for u_idx, ux, uy, uz in upper_verts:
        dist_xy = np.sqrt((lx - ux)**2 + (ly - uy)**2)
        if dist_xy < 0.005 and dist_xy < best_dist:
            # The upper beak is above the lower beak, so uz should be > lz in base positions
            if uz > lz:
                best_u = (u_idx, ux, uy, uz)
                best_dist = dist_xy
    if best_u:
        pairs.append((l_idx, lx, ly, lz, loff, best_u[0], best_u[3]))

print(f"Found {len(pairs)} matching pairs of upper/lower beak vertices.")

# Analyze average gap at different boca values
for val in [0.0, 0.5, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]:
    gaps = []
    for l_idx, lx, ly, lz, loff, u_idx, uz in pairs:
        current_lz = lz + loff * val
        gap = uz - current_lz
        gaps.append(gap)
    gaps = np.array(gaps)
    num_intersect = np.sum(gaps < 0)
    print(f"Boca = {val:.2f} -> Avg Gap: {np.mean(gaps):.4f}, Min Gap: {np.min(gaps):.4f}, Max Gap: {np.max(gaps):.4f}, Intersecting Vertices: {num_intersect}/{len(pairs)}")
