"""
See:
    https://en.wikipedia.org/wiki/Portable_Network_Graphics
    https://www.w3.org/TR/PNG/
"""


def check_normal_format(data):
    file_header = data[:8]
    assert file_header == b'\x89PNG\r\n\x1a\n'

    ihdr_type, ihdr_data, offset = parse_chunk(data, 8)
    # First chunk has to be the IHDR chunk
    assert ihdr_type == b'IHDR'
    width, height, bit_depth = parse_ihdr_data(ihdr_data)

    chunk_type, chunk_data, offset = parse_chunk(data, offset)
    assert chunk_type == b'IDAT'
    # We look elsewhere at actual pixel values with Pillow

    chunk_type, chunk_data, offset = parse_chunk(data, offset)
    assert chunk_type == b'IEND'
    assert len(chunk_data) == 0
    assert len(data) == offset


def parse_chunk(data, offset):
    length = int.from_bytes(data[offset:offset + 4], 'big')
    chunk_type = data[offset + 4:offset + 8]
    chunk_data = data[offset + 8:offset + 8 + length]
    # NB: data may be hidden in CRC. We ignore it here.
    return chunk_type, chunk_data, offset + 8 + length + 4


def parse_ihdr_data(data):
    width = int.from_bytes(data[:4], 'big')
    height = int.from_bytes(data[4:8], 'big')
    bit_depth = int.from_bytes(data[8:9], 'big')
    assert bit_depth in (1, 2, 4, 8, 16)
    colour_type = int.from_bytes(data[9:10], 'big')
    assert colour_type in (0, 2, 3, 4, 6)
    colour_type_str = {
        0: 'greyscale',
        2: 'truecolour',
        3: 'indexed-colour',
        4: 'greyscale with alpha',
        6: 'truecolour with alpha',
    }[colour_type]
    print(f'Dimensions: {width}x{height}, {bit_depth}-bit, {colour_type_str}')
    compression_method = int.from_bytes(data[10:11], 'big')
    assert compression_method == 0
    filter_method = int.from_bytes(data[11:12], 'big')
    assert filter_method == 0
    interlace_method = int.from_bytes(data[13:14], 'big')
    assert interlace_method == 0
    assert len(data) == 13
    return width, height, bit_depth
