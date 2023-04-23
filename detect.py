#!/usr/bin/env python

from collections import deque
import shutil
import sys

import image
import text


def keep_decoding(data):
    derived_data = deque([data])
    while len(derived_data) > 0:
        data = derived_data.pop()
        print(f'Handling {pprint_data(data)}')
        for data in decode(data):
            print(f'Putting on the queue: {pprint_data(data)}')
            derived_data.appendleft(data)
        if len(derived_data) > 0:
            print('-' * shutil.get_terminal_size().columns)


def decode(data):
    n_unique = len(set(data))
    print(f'Length {len(data)}, {n_unique} unique,'
          f' min {min(data)}, max {max(data)}, range {max(data) - min(data)}')

    if n_unique == 2:
        print('Only two unique values; converting to bitstring.')
        val0 = data[0]
        bit_str1 = b''.join(b'0' if bit == val0 else b'1' for bit in data)
        yield bit_str1
        print('Trying reversed.')
        bit_str2 = b''.join(b'1' if bit == val0 else b'0' for bit in data)
        yield bit_str2
    elif image.is_image(data):
        print('Image detected.')
        yield from image.try_decode(data)
    else:
        print('Trying to decode as text.')
        yield from text.try_decode_bytes(data)


def pprint_data(data):
    s = repr(data)
    return s[:200] + ('<snip>' if len(s) > 200 else '')


def main(filename_or_data):
    try:
        with open(filename_or_data, 'rb') as file:
            data = file.read()
    except Exception:
        data = filename_or_data.encode()
    return keep_decoding(data)


if __name__ == "__main__":
    main(sys.argv[1])
