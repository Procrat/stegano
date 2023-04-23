#!/usr/bin/env python
"""
Find hidden information in images.
"""

import io
import math

import matplotlib.pyplot as plt
import PIL.Image

import gif
import jpeg
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
    _log(f'{image.format} image.')

    if image.format == 'PNG':
        png.check_normal_format(data)
    elif image.format == 'GIF':
        gif.check_normal_format(data)
    elif image.format == 'JPEG':
        jpeg.check_normal_format(data)
    else:
        raise NotImplementedError('Image format {image.format} not supported.')

    check_pixels(image)

    if getattr(image, 'is_animated', False):
        _log(f'Animated: {image.n_frames} frames')
        yield from check_first_palette_colors(image)


def check_pixels(image):
    _log(f'Mode: {image.mode} ({"".join(image.getbands())})')
    _log(f'Extrema: {image.getextrema()}')
    _log(f'Entropy: {image.entropy()}')

    if image.mode == 'RGBA' and image.getextrema()[3] == (0, 0):
        _log("It's a transparent image, but there's something there.")
        image.convert('RGB').show()

    if _prompt_bool('Show image per channel?'):
        for channel in image.split():
            channel.show()

    if _prompt_bool('Show histogram per channel?'):
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

    _log('Trying to find patterns in R values')
    yield bytes(rs)
    _log('Trying to find patterns in G values')
    yield bytes(gs)
    _log('Trying to find patterns in B values')
    yield bytes(bs)

    _log('Creating image from first colors in palettes')
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


def _prompt_bool(question, default='no'):
    answer_to_value = {'yes': True, 'y': True, 'no': False, 'n': False}
    options = {'yes': 'Y/n', 'no': 'y/N'}[default]

    while True:
        _log(f'{question} [{options}] ', end='')
        answer = input().lower()
        if answer == '':
            answer = default
        try:
            return answer_to_value[answer]
        except KeyError:
            print('Please respond with "yes", "no", "y" or "n".')


def _log(*args, **kwargs):
    print('Image:', *args, **kwargs)
