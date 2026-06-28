import struct
import json
import os
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

# Let's locate the morph targets of Mesh 1
mesh = json_data['meshes'][1]
primitives = mesh['primitives'][0]
targets = primitives['targets'] # list of dicts, e.g. [{'POSITION': accessor_idx}, ...]
target_names = mesh['extras']['targetNames'] # ['boca', 'ojo']

accessors = json_data['accessors']
buffer_views = json_data['bufferViews']

for idx, name in enumerate(target_names):
    target_accessor_idx = targets[idx]['POSITION']
    accessor = accessors[target_accessor_idx]
    print(f"\nAccessor {target_accessor_idx}: {accessor}")
    if 'bufferView' not in accessor:
        print(f"No bufferView in accessor {target_accessor_idx}")
        continue
    bv_idx = accessor['bufferView']
    bv = buffer_views[bv_idx]
    
    count = accessor['count']
    comp_type = accessor['componentType'] # 5126 for FLOAT
    type_str = accessor['type'] # 'VEC3'
    
    offset = bv.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    length = bv['byteLength']
    
    # Read floats
    f_data = binary_data[offset : offset + count * 12]
    vertices = np.frombuffer(f_data, dtype=np.float32).reshape((count, 3))
    
    # Find bounding box of non-zero offsets
    non_zero = vertices[np.any(vertices != 0, axis=1)]
    print(f"Morph Target: '{name}'")
    print(f"Total vertices: {count}, Non-zero vertices: {len(non_zero)}")
    if len(non_zero) > 0:
        min_val = np.min(non_zero, axis=0)
        max_val = np.max(non_zero, axis=0)
        print(f"Bounding Box of offsets: Min={min_val}, Max={max_val}")
        
        # Print a few non-zero offsets
        print("First 5 non-zero offsets:")
        print(non_zero[:5])
