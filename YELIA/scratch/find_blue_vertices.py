import struct
import json
import numpy as np

glb_path = r"c:\Users\USER\Downloads\YELIA4AP FASE 2-DOMENICA Y WILIAM\YELIA\YELIA\frontend\public\avatars3d\buho.glb"
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

accessors = json_data['accessors']
buffer_views = json_data['bufferViews']

# Load base positions
pos_accessor = accessors[primitives['attributes']['POSITION']]
pos_offset = buffer_views[pos_accessor['bufferView']]['byteOffset'] + pos_accessor.get('byteOffset', 0)
pos_count = pos_accessor['count']
base_positions = np.frombuffer(binary_data[pos_offset : pos_offset + pos_count * 12], dtype=np.float32).reshape((-1, 3))

# Load COLOR_0
color_accessor_idx = primitives['attributes']['COLOR_0']
color_accessor = accessors[color_accessor_idx]
color_bv = buffer_views[color_accessor['bufferView']]
color_offset = color_bv['byteOffset'] + color_accessor.get('byteOffset', 0)
color_count = color_accessor['count']

# ComponentType 5121 is UNSIGNED_BYTE, type is VEC4 (4 bytes per color)
if color_accessor['componentType'] == 5121:
    color_data = np.frombuffer(binary_data[color_offset : color_offset + color_count * 4], dtype=np.uint8).reshape((-1, 4))
    # Normalize to [0, 1]
    color_data = color_data.astype(np.float32) / 255.0
elif color_accessor['componentType'] == 5126:
    color_data = np.frombuffer(binary_data[color_offset : color_offset + color_count * 16], dtype=np.float32).reshape((-1, 4))

# Let's find vertices where blue component is significantly larger than red and green (blue iris)
# Or let's check blue vertices: e.g. blue > 0.4 and red < 0.3 and green < 0.3
blue_indices = np.where((color_data[:, 2] > 0.4) & (color_data[:, 0] < 0.4))[0]
print(f"Found {len(blue_indices)} blue vertices in COLOR_0.")

if len(blue_indices) > 0:
    blue_pos = base_positions[blue_indices]
    print(f"Blue vertices Y range: Min={np.min(blue_pos[:, 1]):.4f}, Max={np.max(blue_pos[:, 1]):.4f}")
    print(f"Blue vertices base positions bounding box:")
    print(f"  Min: {np.min(blue_pos, axis=0)}")
    print(f"  Max: {np.max(blue_pos, axis=0)}")
else:
    # Let's print some vertex colors to see their values
    print("No blue vertices found. Printing first 10 vertex colors:")
    for idx in range(10):
        print(f"  Vertex {idx}: Position={base_positions[idx]}, Color={color_data[idx]}")
