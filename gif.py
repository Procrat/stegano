"""
See:
    https://www.w3.org/Graphics/GIF/spec-gif89a.txt

Grammar:
    <GIF Data Stream> ::= Header <Logical Screen> <Data>* Trailer
    <Logical Screen> ::= Logical Screen Descriptor [Global Color Table]
    <Data> ::= <Graphic Block> | <Special-Purpose Block>
    <Graphic Block> ::= [Graphic Control Extension] <Graphic-Rendering Block>
    <Graphic-Rendering Block> ::= <Table-Based Image> | Plain Text Extension
    <Table-Based Image> ::= Image Descriptor [Local Color Table] Image Data
    <Special-Purpose Block> ::= Application Extension | Comment Extension

Not all GIFs follow that grammar though: some have standalone graphic control
extensions, not followed by a Graphic-Rendering Block.
"""


def check_normal_format(data):
    header = data[:6]
    assert header == b'GIF89a'

    offset = parse_logical_screen(data, 6)

    while True:
        if data[offset:offset + 1] == b';':
            break
        offset = parse_chunk(data, offset)
        print('---')

    assert len(data) == offset + 1


def parse_logical_screen(data, offset):
    width = parse_int(data[offset:offset + 2])
    height = parse_int(data[offset + 2:offset + 4])
    print(f'Dimensions: {width}x{height}')

    flags = data[offset + 4]
    global_color_table_size = flags & 0b111
    sort_flag = (flags >> 3) & 0b1
    color_resolution = (flags >> 4) & 0b111
    global_color_table_flag = flags >> 7
    if global_color_table_flag == 0:
        print('No global color table')
    else:
        print('Global color table:'
              f' {"" if sort_flag else "not "}sorted,'
              f' {color_resolution + 1} bits per channel,'
              f' table size {2 ** (global_color_table_size + 1)}')

    background_color_idx = data[offset + 5]
    print('Background color index:', background_color_idx)

    pixel_aspect_ratio = data[offset + 6]
    if pixel_aspect_ratio != 0:
        print('Pixel aspect ratio:', pixel_aspect_ratio)

    offset += 7
    if global_color_table_flag != 0:
        # Can't do much wrong with the table itself, I guess?
        # You could potentially hide some data in unused colors
        offset += 3 * 2 ** (global_color_table_size + 1)
    return offset


def parse_chunk(data, offset):
    assert data[offset:offset + 1] in b',!'
    if data[offset:offset + 1] == b',':
        print('Image.')
        return parse_table_based_image(data, offset + 1)
    elif data[offset:offset + 1] == b'!':
        offset += 1
        if data[offset] == 0xf9:
            print('Graphic control extension.')
            offset = parse_graphic_control_extension(data, offset + 1)
            assert data[offset:offset + 1] in b',!'
            if data[offset:offset + 1] == b',':
                return parse_table_based_image(data, offset + 1)
            elif data[offset:offset + 1] == b'!':
                offset += 1
                if data[offset] != 0x01:
                    print('Standalone graphic control extension: doesn\'t follow spec')
                    return offset - 1
                print('Plain text extension.')
                return parse_plain_text_extension(data, offset + 1)
        elif data[offset] == 0x01:
            print('Plain text extension.')
            return parse_plain_text_extension(data, offset + 1)
        elif data[offset] == 0xff:
            print('Application extension.')
            return parse_application_extension(data, offset + 1)
        elif data[offset] == 0xfe:
            print('Comment extension.')
            return parse_comment_extension(data, offset + 1)


def parse_table_based_image(data, offset):
    # Image descriptor
    left_pos = parse_int(data[offset:offset + 2])
    top_pos = parse_int(data[offset + 2:offset + 4])
    if left_pos != 0 or top_pos != 0:
        print(f'Position: left={left_pos}, top={top_pos}')
    width = parse_int(data[offset + 4:offset + 6])
    height = parse_int(data[offset + 6:offset + 8])
    print(f'Dimensions: {width}x{height}')
    flags = data[offset + 8]
    color_table_size = flags & 0b111
    reserved = (flags >> 3) & 0b11
    sort_flag = (flags >> 5) & 0b1
    interlace_flag = (flags >> 6) & 0b1
    color_table_flag = flags >> 7
    if color_table_flag == 0:
        assert color_table_size == 0
    else:
        print(f'Local color table of size {color_table_size}'
              f', {"" if sort_flag else "not "}sorted')
    print(f'Interlaced: {"yes" if interlace_flag else "no"}')
    assert reserved == 0
    offset += 9

    # Optional local color table
    if color_table_flag != 0:
        # Can't do much wrong with the table itself, I guess?
        # You could potentially hide some data in unused colors
        offset += 3 * 2 ** (color_table_size + 1)

    # Image data
    lzw_minimum_code_size = data[offset]
    offset, _subdata = parse_subblocks(data, offset + 1)

    block_terminator = data[offset]
    assert block_terminator == 0
    return offset + 1


def parse_graphic_control_extension(data, offset):
    block_size = data[offset]
    assert block_size == 4
    flags = data[offset + 1]
    transparent_color_flag = flags & 0b1
    user_input_flag = (flags >> 1) & 0b1
    assert user_input_flag == 0
    disposal_method = (flags >> 2) & 0b111
    print(f'Disposal method: {disposal_method}')
    reserved = flags >> 5
    assert reserved == 0
    delay_time = parse_int(data[offset + 2:offset + 4])
    print(f'Delay time: {delay_time} * 10ms')
    if transparent_color_flag:
        transparent_color_index = data[offset + 4]
        print(f'Transparent color index: {transparent_color_index}')
    else:
        print(f'No transparent color')
    block_terminator = data[offset + 5]
    assert block_terminator == 0
    return offset + 6


def parse_comment_extension(data, offset):
    offset, subdata = parse_subblocks(data, offset)
    print(f'Comment: "{subdata.decode("ascii")}"')
    block_terminator = data[offset]
    assert block_terminator == 0
    return offset + 1


def parse_subblocks(data, offset):
    subdata = b''
    last_block_size = 254
    while data[offset] != 0:
        block_size = data[offset]
        if block_size < 254 and last_block_size < 254:
            print(f'Encountered sub-block size < 254 before last:',
                  last_block_size)
        subdata += data[offset + 1: offset + 1 + block_size]
        offset += block_size + 1
        last_block_size = block_size
    return offset, subdata


def parse_application_extension(data, offset):
    block_size = data[offset]
    assert block_size == 11
    application_identifier = data[offset + 1:offset + 9]
    print(f'Application identifier: {application_identifier.decode("ascii")}')
    auth_code = data[offset + 9:offset + 12]
    print(f'Application authentication code: {auth_code}')
    offset, subdata = parse_subblocks(data, offset + 12)
    print('Application data:', subdata)
    block_terminator = data[offset]
    assert block_terminator == 0
    return offset + 1


def parse_plain_text_extension(data, offset):
    raise NotImplementedError


def parse_int(data):
    return int.from_bytes(data, 'little')
