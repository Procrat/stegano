"""
See:
    https://www.w3.org/Graphics/JPEG/itu-t81.pdf
      - Especially pages 48 & 49
    https://www.w3.org/Graphics/JPEG/jfif3.pdf
    https://en.wikipedia.org/wiki/JPEG#Syntax_and_structure
"""


def check_normal_format(data):
    offset = parse_image(data, offset=0)
    assert offset == len(data), 'Trailing data'


def parse_image(data, offset):
    marker_type, _, offset = parse_marker_type(data, offset)
    assert marker_type == 'SOI', f'Expected SOI, but got {marker_type}'

    offset = parse_frame(data, offset)

    marker_type, _, offset = parse_marker_type(data, offset)
    if marker_type != 'EOI':  # End Of Image
        raise NotImplementedError(
            f'Expected marker EOI but got {marker_type}.'
            ' Only single-frame and single-scan mode is supported.'
        )

    return offset


def parse_marker_type(data, offset):
    data = data[offset:offset + 2]
    offset += 2

    assert data[0] == 0xff, f'Expected marker, but got {data}'

    marker_type = {
        0xd8: 'SOI',
        0xc4: 'DHT',
        0xdb: 'DQT',
        0xdd: 'DRI',
        0xda: 'SOS',
        0xd9: 'EOI',
    }.get(data[1])
    if marker_type is not None:
        return marker_type, None, offset

    if data[1] >> 4 == 0xe:
        n = data[1] & 0xf
        return 'APP', n, offset

    if data[1] >> 4 == 0xc and data[1] not in (0xc4, 0xcc):
        n = data[1] & 0xf
        return 'SOF', n, offset

    if data[1] & 0xf8 == 0xd0:
        n = data[1] & 0x07
        return 'RST', n, offset

    raise NotImplementedError(f'Marker type {hex(data[1])}')


def parse_frame(data, offset):
    offset = parse_tables_misc(data, offset)

    marker_type, _n, offset = parse_marker_type(data, offset)
    if marker_type != 'SOF':  # Start Of Frame
        raise NotImplementedError(
            f'Expected marker SOF but got {marker_type}.'
            ' Only non-hierarchical mode is supported.'
        )

    offset = parse_frame_header(data, offset)

    offset = parse_scan(data, offset)

    return offset


def parse_tables_misc(data, offset):
    while True:
        new_offset = parse_single_tables_misc(data, offset)
        if new_offset == offset:
            return offset
        offset = new_offset


def parse_single_tables_misc(data, offset):
    initial_offset = offset

    marker_type, marker_n, offset = parse_marker_type(data, offset)
    if marker_type not in ('DQT', 'DHT', 'DAC', 'DRI', 'COM', 'APP'):
        return initial_offset

    match marker_type:
        case 'APP':
            return parse_application(data, offset)
        case 'DHT':
            return parse_huffman_table(data, offset)
        case 'DQT':
            return parse_quantization_table(data, offset)
        case 'DRI':
            return parse_restart_interval(data, offset)
        case _:
            raise NotImplementedError(f'Marker type {marker_type}')


def parse_application(data, offset):
    length = parse_int(data[offset:offset + 2])
    _log('Contains APP data:', data[offset + 2: offset + length])
    # TODO yield somehow
    return offset + length


def parse_huffman_table(data, offset):
    length = parse_int(data[offset:offset + 2])
    _log('<Skipping Huffman table>')
    return offset + length


def parse_quantization_table(data, offset):
    length = parse_int(data[offset:offset + 2])
    _log('<Skipping quantization table>')
    return offset + length


def parse_restart_interval(data, offset):
    length = parse_int(data[offset:offset + 2])
    assert length == 4
    restart_interval = parse_int(data[offset + 2:offset + 4])
    _log(f'Restart interval = {restart_interval} MCUs')
    return offset + length


def parse_frame_header(data, offset):
    length = parse_int(data[offset:offset + 2])
    sample_precision = data[offset + 2]
    n_lines = parse_int(data[offset + 3:offset + 5])
    samples_per_line = parse_int(data[offset + 5:offset + 7])
    n_image_components = data[offset + 7]
    _log('Frame header:')
    _log2('Sample precision:', sample_precision)
    _log2('Number of lines:', n_lines)
    _log2('Samples per line:', samples_per_line)
    _log2('Number of image components:', n_image_components)
    _log2('<Skipping frame component parameters>')
    return offset + length


def parse_scan(data, offset):
    offset = parse_tables_misc(data, offset)

    marker_type, _, offset = parse_marker_type(data, offset)
    assert marker_type == 'SOS', f'Expected SOS, but got {marker_type}'

    offset = parse_scan_header(data, offset)

    offset = parse_ecs(data, offset)

    while True:
        marker_type, n, new_offset = parse_marker_type(data, offset)
        if marker_type != 'RST':
            break

        _log(f'<Restart {n}>')
        offset = parse_ecs(data, new_offset)

    return offset


def parse_scan_header(data, offset):
    length = parse_int(data[offset:offset + 2])
    n_image_components = data[offset + 2]
    _log('Scan header:')
    _log2('Number of image components:', n_image_components)
    _log2('<Skipping other scan parameters>')
    return offset + length


def parse_ecs(data, offset):
    _log('<Skipping entropy-code segment (ECS). Will look at pixels later.>')

    # We don't know the length of the ECS segment up front, but we should be
    # able to look for the next marker. 0xff is encoded as 0xff00 in the ECS,
    # so we can look for the next 0xff that isn't followed by 0x00.
    while data[offset] != 0xff or data[offset + 1] == 0x00:
        offset += 1
        try:
            offset = data.index(0xff, offset)
        except ValueError:
            raise Exception(
                'JPEG: No end of the entropy-coded segment was found'
            )

    return offset


def parse_int(data):
    return int.from_bytes(data, 'big')


def _log(*args):
    print('JPEG:', *args)


def _log2(*args):
    print(' ', *args)
