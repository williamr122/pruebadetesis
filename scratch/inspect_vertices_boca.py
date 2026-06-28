import struct
import json
import numpy as np

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"

with open(glb_path, 'rb') as f:
    header = f.read(12)
    magic, version, length = struct.unpack('<III', header)
    
    # Read chunk 0 (JSON)
    chunk_header = f.read(8)
    chunk_length, chunk_type = struct.unpack('<II', chunk_header)
    json_bytes = f.read(chunk_length)
    json_data = json.loads(json_bytes.decode('utf-8'))
    
    # Read chunk 1 (Binary buffer)
    chunk1_header = f.read(8)
    c1_length, c1_type = struct.unpack('<II', chunk1_header)
    binary_data = f.read(c1_length)

# Mesh 1
mesh = json_data['meshes'][1]
primitives = mesh['primitives'][0]
targets = primitives['targets'] # [{'POSITION': accessor_idx}, ...]
target_names = mesh['extras']['targetNames'] # ['boca', 'ojo']

accessors = json_data['accessors']
buffer_views = json_data['bufferViews']

# Load base positions
pos_accessor_idx = primitives['attributes']['POSITION']
pos_accessor = accessors[pos_accessor_idx]
pos_bv = buffer_views[pos_accessor['bufferView']]
pos_offset = pos_bv.get('byteOffset', 0) + pos_accessor.get('byteOffset', 0)
pos_count = pos_accessor['count']
pos_data = binary_data[pos_offset : pos_offset + pos_count * 12]
base_positions = np.frombuffer(pos_data, dtype=np.float32).reshape((pos_count, 3))

# Load target offsets (boca is index 0)
# Since accessor 10 is sparse, let's load sparse data
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
        
        # indices
        indices_bv = buffer_views[sparse['indices']['bufferView']]
        indices_offset = indices_bv.get('byteOffset', 0)
        indices_comp = sparse['indices']['componentType']
        # componentType 5123 is UNSIGNED_SHORT (2 bytes)
        indices_data = binary_data[indices_offset : indices_offset + s_count * 2]
        indices = np.frombuffer(indices_data, dtype=np.uint16)
        
        # values
        values_bv = buffer_views[sparse['values']['bufferView']]
        values_offset = values_bv.get('byteOffset', 0)
        # type is VEC3, float
        values_data = binary_data[values_offset : values_offset + s_count * 12]
        values = np.frombuffer(values_data, dtype=np.float32).reshape((s_count, 3))
        
        for i, idx in enumerate(indices):
            data[idx] = values[i]
            
    return data

boca_offsets = get_accessor_data(targets[0]['POSITION'])
ojo_offsets = get_accessor_data(targets[1]['POSITION'])

# Print stats
print("Base positions bounding box:")
print(f"Min: {np.min(base_positions, axis=0)}")
print(f"Max: {np.max(base_positions, axis=0)}")

# Find vertices affected by boca
boca_indices = np.where(np.any(boca_offsets != 0, axis=1))[0]
print(f"\nBoca affects {len(boca_indices)} vertices.")
if len(boca_indices) > 0:
    # Print the bounding box of the base positions of vertices affected by boca
    affected_base = base_positions[boca_indices]
    print(f"Base position bounding box of vertices affected by 'boca':")
    print(f"  Min: {np.min(affected_base, axis=0)}")
    print(f"  Max: {np.max(affected_base, axis=0)}")

# Find vertices affected by ojo
ojo_indices = np.where(np.any(ojo_offsets != 0, axis=1))[0]
print(f"\nOjo affects {len(ojo_indices)} vertices.")
if len(ojo_indices) > 0:
    affected_base = base_positions[ojo_indices]
    print(f"Base position bounding box of vertices affected by 'ojo':")
    print(f"  Min: {np.min(affected_base, axis=0)}")
    print(f"  Max: {np.max(affected_base, axis=0)}")
