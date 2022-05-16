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
    while chunk_type != b'IEND':
        match chunk_type:
            case b'IDAT':
                # We look elsewhere at actual pixel values with Pillow
                pass
            case b'eXIf':
                print('eXIf chunk: Exif data detected. Run exiftool.')
            case b'sRGB':
                assert len(chunk_data) == 1
                # print(f'sRGB chunk: sRGB colour space (rendering intent {chunk_data[0]}).')
            case b'pHYs':
                assert len(chunk_data) == 9
                ppu_x = int.from_bytes(chunk_data[:4], 'big')
                ppu_y = int.from_bytes(chunk_data[4:8], 'big')
                unit = chunk_data[8]
                assert unit == 1  # Metres
                # print(f'pHYs chunk: Pixels per meter: {ppu_x}x{ppu_y}.')
            case b'iTXt':
                assert chunk_data.startswith(
                    b'XML:com.adobe.xmp\x00\x00\x00\x00\x00'
                )
                print(f'iTXt chunk: {chunk_data[22:].decode()}')
            case b'gAMA':
                assert len(chunk_data) == 4
                # gamma = int.from_bytes(chunk_data, 'big')
                # print(f'gAMA chunk: Gamma: {gamma}')
            case b'cHRM':
                # print('cHRM chunk.')
                pass
            case b'bKGD':
                bg_colour = chunk_data
                print(f'bKGD chunk: Explicit background colour set: {bg_colour}')
            case b'tIME':
                # print('tIME chunk.')
                pass
            case b'tEXt':
                print(f'tEXt chunk: {chunk_data.decode()}')
            case _:
                print(f'Unknown chunk type {chunk_type}')

        chunk_type, chunk_data, offset = parse_chunk(data, offset)

    # After last chunk
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
