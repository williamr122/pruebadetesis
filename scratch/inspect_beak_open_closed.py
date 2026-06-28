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

# Let's find beak vertices.
# In the previous script, top vertices moving in 'ojo' (which is the beak) had base coordinates around [0.35, +/-0.168, 0.051]
# Wait, let's look at the vertices affected by 'ojo' (which is the beak)
ojo_offsets = get_accessor_data(targets[1]['POSITION'])
movements_o = np.linalg.norm(ojo_offsets, axis=1)
large_ojo_indices = np.where(movements_o > 0.05)[0]

# Let's see the base positions of these beak vertices:
# They have X around 0.35, Y around +/-0.168.
# Let's select one vertex with Y > 0 (upper beak) and one with Y < 0 (lower beak) from the beak vertices
upper_beak_indices = [idx for idx in large_ojo_indices if base_positions[idx][1] > 0.05]
lower_beak_indices = [idx for idx in large_ojo_indices if base_positions[idx][1] < -0.05]

if len(upper_beak_indices) > 0 and len(lower_beak_indices) > 0:
    u_idx = upper_beak_indices[0]
    l_idx = lower_beak_indices[0]
    
    pos_u_base = base_positions[u_idx]
    pos_l_base = base_positions[l_idx]
    dist_base = np.linalg.norm(pos_u_base - pos_l_base)
    
    # Position with 'boca' morph target applied (influence = 1.0)
    pos_u_boca = pos_u_base + boca_offsets[u_idx]
    pos_l_boca = pos_l_base + boca_offsets[l_idx]
    dist_boca = np.linalg.norm(pos_u_boca - pos_l_boca)
    
    # Position with 'ojo' morph target applied (influence = 1.0)
    pos_u_ojo = pos_u_base + ojo_offsets[u_idx]
    pos_l_ojo = pos_l_base + ojo_offsets[l_idx]
    dist_ojo = np.linalg.norm(pos_u_ojo - pos_l_ojo)
    
    print(f"Upper beak vertex base: {pos_u_base}")
    print(f"Lower beak vertex base: {pos_l_base}")
    print(f"Base distance: {dist_base:.4f}")
    print(f"Distance with 'boca' = 1.0: {dist_boca:.4f} (Delta: {dist_boca - dist_base:+.4f})")
    print(f"Distance with 'ojo' = 1.0: {dist_ojo:.4f} (Delta: {dist_ojo - dist_base:+.4f})")
else:
    print("Could not find upper/lower beak vertices.")
