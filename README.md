Stegano automation
==================

A forever-WIP library intent to find hidden messages.
Currently supports
- PNG & (animated) GIF images, and
- Binary, base32, base58, base64, base85 and morse encoded text.

More specifically for images, we look at
- any place in the format where data can be hidden that an image viewer wouldn't
  show, and
- the image and its histogram per channel (R, G, B, and A).

Usage
=====

```sh
./detect.py 'c2VjcmV0IG1lc3NhZ2UK'
```
or
```sh
./detect.py some-file.png
```
