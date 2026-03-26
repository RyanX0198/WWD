#!/usr/bin/env python3
import struct
import zlib
import shutil

# 生成一个简单的 32x32 PNG 图标
# PNG 文件头
png_header = b'\x89PNG\r\n\x1a\n'

# IHDR chunk
width = 32
height = 32
bit_depth = 8
color_type = 2  # RGB
compression = 0
filter_method = 0
interlace = 0

ihdr_data = struct.pack('>IIBBBBB', width, height, bit_depth, color_type, compression, filter_method, interlace)
ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
ihdr_chunk = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)

# IDAT chunk (压缩的图像数据)
# 创建蓝色方块
raw_data = b''
for y in range(height):
    raw_data += b'\x00'  # filter byte
    for x in range(width):
        raw_data += b'\x3b\x82\xf6'  # 蓝色 RGB

compressed = zlib.compress(raw_data)
idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
idat_chunk = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)

# IEND chunk
iend_crc = zlib.crc32(b'IEND') & 0xffffffff
iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)

# 组合 PNG
png_data = png_header + ihdr_chunk + idat_chunk + iend_chunk

# 保存
with open('icon.png', 'wb') as f:
    f.write(png_data)

# 复制各种尺寸
shutil.copy('icon.png', '32x32.png')
shutil.copy('icon.png', '128x128.png')
shutil.copy('icon.png', '128x128@2x.png')

print('图标生成完成')