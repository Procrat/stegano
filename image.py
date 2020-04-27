#!/usr/bin/env python
"""
Find hidden information in images.
"""

import collections
import io
import math
import sys

import matplotlib.pyplot as plt
import PIL.Image

import gif
import png


def is_image(data):
    try:
        PIL.Image.open(io.BytesIO(data))
        return True
    except Exception:
        return False


def try_decode(data):
    image = PIL.Image.open(io.BytesIO(data))
    image.verify()

    # Verify closes the internal file pointer, so we have to open it again
    image = PIL.Image.open(io.BytesIO(data))
    print(f'{image.format} image.')

    assert image.format in ('PNG', 'GIF')
    if image.format == 'PNG':
        png.check_normal_format(data)
    elif image.format == 'GIF':
        gif.check_normal_format(data)

    check_pixels(image)

    if image.is_animated:
        print(f'Animated image, {image.n_frames} frames')
        yield from check_first_palette_colors(image)


def check_pixels(image):
    print(f'Mode: {image.mode} ({"".join(image.getbands())})')
    print(f'Extrema: {image.getextrema()}')

    if image.mode == 'RGBA' and image.getextrema()[3] == (0, 0):
        print("It's a transparent image, but there's something there.")
        image.convert('RGB').show()

    print('Showing image per channel')
    for channel in image.split():
        channel.show()

    print('Showing histogram per channel')
    show_histogram(image)


def show_histogram(image):
    histogram = image.histogram()
    figure_count = 0
    offset = 0
    for band in image.getbands():
        channel_histogram = histogram[offset:offset + 256]
        plt.figure(figure_count)

        for i in range(0, 256):
            shade = {
                'R': '#%02x%02x%02x' % (i, 0, 0),
                'G': '#%02x%02x%02x' % (0, i, 0),
                'B': '#%02x%02x%02x' % (0, 0, i),
            }.get(band)
            kwargs = {'color': shade, 'edgecolor': shade} if shade else {}
            plt.bar(i, channel_histogram[i], alpha=0.7, **kwargs)

        offset += 256
        figure_count += 1
    plt.show()


def check_first_palette_colors(image):
    colors = []
    for frame_idx in range(image.n_frames):
        image.seek(frame_idx)
        colors.append(image.getpalette()[:3])

    rs = [color[0] for color in colors]
    gs = [color[1] for color in colors]
    bs = [color[2] for color in colors]

    print('Trying to find patterns in R values')
    yield bytes(rs)
    print('Trying to find patterns in G values')
    yield bytes(gs)
    print('Trying to find patterns in B values')
    yield bytes(bs)

    print('Creating image from first colors in palettes')
    bytes_ = bytes(x for color in colors for x in color)
    dimensions = _factorize(image.n_frames)
    image = PIL.Image.frombytes('RGB', dimensions, bytes_)
    check_pixels(image)


def _factorize(n):
    ds = []
    for d in (2, 3, 5, 7, 11, 13, 17, 19):
        while n % d == 0:
            ds.append(d)
            n //= d
    ds.append(n)
    ds.sort()
    w = ds.pop()
    while math.prod(ds) > w:
        w *= ds.pop()
    return w, math.prod(ds)
