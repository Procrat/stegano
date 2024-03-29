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
                _log('eXIf chunk: Exif data detected. Run exiftool.')
            case b'sRGB':
                assert len(chunk_data) == 1
                # _log(f'sRGB chunk: sRGB colour space (rendering intent {chunk_data[0]}).')
            case b'pHYs':
                assert len(chunk_data) == 9
                ppu_x = parse_int(chunk_data[:4])
                ppu_y = parse_int(chunk_data[4:8])
                unit = chunk_data[8]
                assert unit == 1  # Metres
                # _log(f'pHYs chunk: Pixels per meter: {ppu_x}x{ppu_y}.')
            case b'iTXt':
                assert chunk_data.startswith(
                    b'XML:com.adobe.xmp\x00\x00\x00\x00\x00'
                )
                _log(f'iTXt chunk: {chunk_data[22:].decode()}')
            case b'gAMA':
                assert len(chunk_data) == 4
                # gamma = parse_int(chunk_data)
                # _log(f'gAMA chunk: Gamma: {gamma}')
            case b'cHRM':
                # _log('cHRM chunk.')
                pass
            case b'bKGD':
                bg_colour = chunk_data
                _log(f'bKGD chunk: Explicit background colour set: {bg_colour}')
            case b'tIME':
                # _log('tIME chunk.')
                pass
            case b'tEXt':
                _log(f'tEXt chunk: {chunk_data.decode()}')
            case _:
                _log(f'Unknown chunk type {chunk_type}')

        chunk_type, chunk_data, offset = parse_chunk(data, offset)

    # After last chunk
    assert len(chunk_data) == 0
    assert len(data) == offset


def parse_chunk(data, offset):
    length = parse_int(data[offset:offset + 4])
    chunk_type = data[offset + 4:offset + 8]
    chunk_data = data[offset + 8:offset + 8 + length]
    # NB: data may be hidden in CRC. We ignore it here.
    return chunk_type, chunk_data, offset + 8 + length + 4


def parse_ihdr_data(data):
    width = parse_int(data[:4])
    height = parse_int(data[4:8])
    bit_depth = parse_int(data[8:9])
    assert bit_depth in (1, 2, 4, 8, 16)
    colour_type = parse_int(data[9:10])
    assert colour_type in (0, 2, 3, 4, 6)
    colour_type_str = {
        0: 'greyscale',
        2: 'truecolour',
        3: 'indexed-colour',
        4: 'greyscale with alpha',
        6: 'truecolour with alpha',
    }[colour_type]
    _log(f'Dimensions: {width}x{height}, {bit_depth}-bit, {colour_type_str}')
    compression_method = parse_int(data[10:11])
    assert compression_method == 0
    filter_method = parse_int(data[11:12])
    assert filter_method == 0
    interlace_method = parse_int(data[13:14])
    assert interlace_method == 0
    assert len(data) == 13
    return width, height, bit_depth


def parse_int(data):
    return int.from_bytes(data, 'big')


def _log(*args):
    print('PNG:', *args)
