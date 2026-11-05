#!/usr/bin/env python3
"""Render NULL/X, a self-contained fictional workstation. Python 3, no packages."""
from __future__ import annotations

import argparse
import base64
from hashlib import sha256
from html import escape
import math
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]
P = dict(paper='#e7e2d4', light='#f3efe4', deep='#d8d1bf', ink='#20231d',
         soft='#383c32', olive='#696650', brass='#c8b991', line='#b8b4a5',
         black='#111411', text='#deddd0', dim='#8e9486', teal='#375c59', rust='#8b4939')
MONO = 'DejaVu Sans Mono, Liberation Mono, Consolas, monospace'
SANS = 'DejaVu Sans, Arial, sans-serif'


class Canvas:
    def __init__(self):
        self.parts = []

    def add(self, markup):
        self.parts.append(markup)

    def rect(self, x, y, w, h, fill, stroke=None, **attrs):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
                 + (f' stroke="{stroke}"' if stroke else '')
                 + ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items()) + '/>')

    def path(self, d, stroke=P['ink'], width=1, fill='none', **attrs):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'
                 + ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items()) + '/>')

    def text(self, x, y, value, size=16, fill=P['ink'], anchor=None, mono=True,
             weight=None, spacing=None, opacity=None, fit=False, **attrs):
        options = {'font-family': MONO if mono else SANS, 'font-size': size,
                   'fill': fill, 'xml:space': 'preserve'}
        if anchor: options['text-anchor'] = anchor
        if weight: options['font-weight'] = weight
        if spacing is not None: options['letter-spacing'] = spacing
        if opacity is not None: options['opacity'] = opacity
        if fit and value:
            options['textLength'] = round(len(value) * size * .60205, 3)
            options['lengthAdjust'] = 'spacingAndGlyphs'
        options.update({k.replace('_', '-'): v for k, v in attrs.items()})
        self.add(f'<text x="{x}" y="{y}" ' + ' '.join(
            f'{k}="{escape(str(v), quote=True)}"' for k, v in options.items())
            + f'>{escape(value)}</text>')

    def circle(self, cx, cy, r, fill='none', stroke=None, width=1, **attrs):
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'
                 + (f' stroke="{stroke}" stroke-width="{width}"' if stroke else '')
                 + ''.join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items()) + '/>')


def definitions(c):
    c.add('''<defs>
      <linearGradient id="paper" x2="1" y2="1">
        <stop stop-color="#f1ede1"/><stop offset=".58" stop-color="#dfd8c8"/>
        <stop offset="1" stop-color="#c7c0ae"/>
      </linearGradient>
      <radialGradient id="light" cx=".5" cy="0" r=".76">
        <stop stop-color="#ffffff" stop-opacity=".72"/>
        <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="vignette" r=".75">
        <stop offset=".46" stop-color="#20231d" stop-opacity="0"/>
        <stop offset="1" stop-color="#20231d" stop-opacity=".17"/>
      </radialGradient>
      <linearGradient id="metal" x2="0" y2="1">
        <stop stop-color="#f3efe4"/><stop offset="1" stop-color="#cec6b3"/>
      </linearGradient>
      <pattern id="scan" width="4" height="5" patternUnits="userSpaceOnUse">
        <path d="M0 .5H4" stroke="#20231d" stroke-opacity=".018"/>
        <path d="M0 2.5H4" stroke="#ffffff" stroke-opacity=".025"/>
      </pattern>
      <pattern id="crt" width="4" height="4" patternUnits="userSpaceOnUse">
        <path d="M0 .5H4" stroke="#000000" stroke-opacity=".09"/>
      </pattern>
      <pattern id="grid" width="192" height="192" patternUnits="userSpaceOnUse">
        <path d="M0 32H62L94 0M192 128H154L122 160V192M29 96H35M32 93V99"
          stroke="#696650" stroke-opacity=".085" fill="none"/>
        <rect x="127" y="31" width="2" height="2" fill="#696650" opacity=".18"/>
      </pattern>
    </defs>''')


def emblem(c, x, y, scale=1, color=P['ink']):
    c.add(f'<g transform="translate({x} {y}) scale({scale})">')
    c.path('M0 8V0H8M22 0H30V8M30 22V30H22M8 30H0V22', color, 2)
    c.path('M8 21L21 8M10 8H21V19', color, 2.5)
    c.add('</g>')


def frame(c, x, y, w, h, title, dark=False, active=False, number=''):
    for offset, opacity in [(10, .045), (6, .07), (3, .10)]:
        c.rect(x + offset, y + offset, w, h, P['ink'], opacity=opacity)
    c.rect(x, y, w, h, P['black'] if dark else P['deep'], P['ink'])
    c.rect(x + 1, y + 1, w - 2, 42, P['ink'] if active else 'url(#metal)')
    c.path(f'M{x+1} {y+43}H{x+w-1}', P['ink'])
    emblem(c, x + 13, y + 12, .6, P['brass'] if active else P['ink'])
    c.text(x + 44, y + 27, title, 16, P['light'] if active else P['ink'], fit=True)
    if number:
        c.text(x + w - 104, y + 27, number, 12, P['brass'] if active else P['olive'])
    for k in range(2):
        bx = x + w - 58 + k * 26
        c.rect(bx, y + 12, 17, 17, 'none', P['olive'] if active else P['line'])
        c.path(f'M{bx+4} {y+24}H{bx+13}' if k == 0 else
               f'M{bx+5} {y+17}L{bx+12} {y+24}M{bx+12} {y+17}L{bx+5} {y+24}',
               P['light'] if active else P['ink'])


def wallpaper(c, width, height, mobile):
    c.rect(0, 0, width, height, P['paper'])
    for fill in ['url(#paper)', 'url(#light)', 'url(#grid)', 'url(#scan)', 'url(#vignette)']:
        c.rect(0, 0, width, height, fill)
    c.rect(11, 11, width - 22, height - 22, 'none', P['line'], stroke_opacity='.6')
    for x, sign in [(24, 1), (width - 24, -1)]:
        c.path(f'M{x} 85V109H{x+20*sign}M{x} {height-99}V{height-75}H{x+20*sign}', P['olive'])
    if not mobile:
        c.path(f'M172 131V{height-165}M154 131H190M154 {height-165}H190', P['line'], .7)
        for y in range(160, height - 165, 80):
            c.path(f'M167 {y}H177', P['line'])
        c.text(49, height - 150, 'NULL', 13, P['olive'], spacing=5)
        c.text(49, height - 126, '/ X', 13, P['olive'], spacing=5)


def menu(c, width, mobile):
    c.rect(0, 0, width, 62, P['light'])
    c.path(f'M0 61H{width}M0 64H{width}', P['ink'], 1)
    emblem(c, 24, 16, .9)
    c.text(69, 39, 'NULL / X', 20, weight='bold', spacing=1)
    labels = ['SYSTEM', 'FILE', 'SIGNAL'] if mobile else ['SYSTEM', 'FILE', 'EDIT', 'VIEW', 'SIGNAL', 'SESSION']
    x = 227
    for label in labels:
        c.text(x, 38, label, 14, weight='bold')
        x += len(label) * 9 + 29
    if not mobile:
        c.circle(width - 260, 30, 3, P['olive'])
        c.text(width - 247, 36, 'LOCAL SESSION', 12)
        c.path(f'M{width-111} 20V41', P['line'])
        c.text(width - 28, 38, '01 : 08', 15, anchor='end')


def icon(c, x, y, kind, label, scale=1):
    c.add(f'<g aria-label="{label}" transform="translate({x} {y}) scale({scale})">')
    c.rect(4, 6, 68, 66, P['ink'], opacity='.10')
    if kind != 'netscape':
        c.path('M0 8V0H59L70 11V66H0Z', P['ink'], 1.3, 'url(#metal)')
        c.path('M3 63V3H57', '#fffaf0', 1)
    if kind == 'netscape':
        # Use the owner's exact supplied artwork, resampled without redrawing.
        png = (ROOT / 'assets/icons/netscape-128.png').read_bytes()
        data = base64.b64encode(png).decode('ascii')
        c.add(f'<image id="netscape-reference" x="0" y="0" width="70" height="70" '
              f'preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
        c.rect(0, 0, 70, 70, 'none', P['ink'], stroke_width='.8')
    elif kind == 'audio':
        c.rect(10, 12, 50, 32, P['ink'])
        for i, v in enumerate([8, 17, 11, 23, 15, 6, 19]):
            c.rect(16 + i * 6, 38 - v, 3, v, P['brass'])
        c.path('M15 55H45M26 51V59', P['ink'], 2)
        c.circle(54, 55, 4, P['olive'])
    elif kind == 'files':
        c.path('M10 24V14H29L36 21H59V53H10Z', P['ink'], 1.4, P['brass'])
        c.path('M10 28H62L56 54H6Z', P['ink'], 1.4, P['light'])
        c.path('M18 37H46M18 43H35', P['olive'])
    elif kind == 'terminal':
        c.rect(9, 12, 53, 42, P['ink'], P['olive'])
        c.path('M10 19H61', P['brass'])
        c.path('M18 28L26 34L18 40M31 42H42', P['light'], 2)
    elif kind == 'irc':
        c.path('M8 15H61V44H33L21 54V44H8Z', P['ink'], 1.4, P['light'])
        c.text(35, 37, '#', 28, P['teal'], anchor='middle', weight='bold')
    elif kind == 'packet':
        for px, py in [(17, 17), (50, 18), (35, 48)]:
            c.path(f'M35 31L{px} {py}', P['ink'], 1.5)
            c.rect(px - 6, py - 5, 12, 10, P['brass'], P['ink'])
        c.circle(35, 31, 6, P['ink'])
    c.text(35, 91, label, 15, P['light'], anchor='middle', weight='bold', stroke=P['light'], stroke_width='3', paint_order='stroke')
    c.text(35, 91, label, 15, P['ink'], anchor='middle', weight='bold')
    c.add('</g>')


def clock(c, x, y, w=270):
    h = w + 56
    frame(c, x, y, w, h, 'xclock / analog')
    cx, cy, r = x + w / 2, y + 44 + (h - 68) / 2, w * .36
    c.circle(cx, cy, r + 7, P['light'], P['line'])
    c.circle(cx, cy, r, 'none', P['olive'])
    for i in range(60):
        a = math.radians(i * 6 - 90)
        inner = r - (12 if i % 5 == 0 else 5)
        c.path(f'M{cx+math.cos(a)*inner:.2f} {cy+math.sin(a)*inner:.2f}'
               f'L{cx+math.cos(a)*(r-3):.2f} {cy+math.sin(a)*(r-3):.2f}',
               P['ink'] if i % 5 == 0 else P['olive'], 1.6 if i % 5 == 0 else .7)
    for digit, dx, dy in [('12', 0, -r*.64), ('3', r*.69, 6), ('6', 0, r*.77), ('9', -r*.7, 6)]:
        c.text(cx + dx, cy + dy, digit, 13, anchor='middle')
    for angle, length, weight in [(304, r * .48, 5), (48, r * .73, 3)]:
        a = math.radians(angle - 90)
        c.path(f'M{cx} {cy}L{cx+math.sin(a+math.pi/2)*length:.2f} {cy+math.sin(a)*length:.2f}',
               P['ink'], weight, stroke_linecap='square')
    c.circle(cx, cy, 5, P['ink'])
    c.circle(cx, cy, 1.8, P['brass'])
    c.text(cx, y + h - 12, 'TIME IS A CONSTRUCT', 10, P['olive'], anchor='middle', spacing=1)


def legacy_terminal(c, x, y, w, mobile):
    frame(c, x, y, w, 302, 'xterm / tty01', dark=True, number='03')
    fs = 16 if mobile else 20
    prompt = '[hacker@localhost hacker]$'
    lines = [
        ('Red Hat Linux release 6.2 (Zoot)', P['text']),
        ('Kernel 2.2.14-5.0 on an i686', P['dim']),
        ('', P['text']),
        (f'{prompt} uname -r', P['text']),
        ('2.2.14-5.0', P['brass']),
        (prompt, P['text']),
    ]
    for i, (value, fill) in enumerate(lines):
        c.text(x + 22, y + 86 + i * 31, value, fs, fill, fit=True)
    c.rect(x + 22 + (len(prompt) + 1) * fs * .60205,
           y + 86 + 5 * 31 - fs + 2, fs * .60205, fs + 3, P['brass'])
    c.rect(x + 1, y + 44, w - 2, 257, 'url(#crt)')
    c.text(x + 22, y + 283, 'i686 / 2000 / XFree86 3.3.6', 11, P['dim'])


def amp(c, x, y, w=328, mobile=False):
    c.add('<g id="amp-player" aria-label="AMP playing Break Stuff by Limp Bizkit">')
    frame(c, x, y, w, 218, 'AMP / side b', number='04')
    c.rect(x + 14, y + 57, w - 28, 94, P['ink'])
    c.text(x + 27, y + 79, 'LIMP BIZKIT', 18 if mobile else 12, P['dim'], spacing=1)
    c.text(x + 27, y + 103, 'BREAK STUFF', 20 if mobile else 15, P['brass'], weight='bold', spacing=1)
    levels = [3, 9, 5, 17, 7, 24, 14, 5, 18, 9, 3, 15, 23, 8, 16, 6, 11, 4, 20, 7]
    for i in range(34 if mobile else 20):
        c.path(f'M{x+29+i*8} {y+135}v{-levels[i % len(levels)]}', P['brass'], 3)
    c.text(x + w - 23, y + 136, '01:08', 20 if mobile else 16, P['light'], anchor='end')
    for i in range(5):
        c.rect(x + 15 + i * 36, y + 166, 28, 25, P['brass'] if i == 0 else 'url(#metal)', P['olive'] if i == 0 else P['line'])
    c.path(f'M{x+26} {y+172}L{x+35} {y+179}L{x+26} {y+186}Z', P['ink'], 1, P['ink'])
    c.path(f'M{x+60} {y+172}V{y+186}M{x+66} {y+172}V{y+186}', P['ink'], 2)
    c.rect(x + 95, y + 174, 10, 10, P['ink'])
    c.text(x + w - 20, y + 183, '44.1 kHz', 12, P['olive'], anchor='end')
    c.text(x + 16, y + 207, 'PLAYING / PCM / STEREO', 10 if mobile else 9, P['olive'], spacing=1)
    c.add('</g>')


def desktop_motto(c, x, y, mobile=False):
    c.add('<g id="desktop-motto" aria-label="Desktop wallpaper slogans">')
    c.text(x, y, 'NO OWNER. NO MASTER.', 11, P['olive'], spacing=1 if mobile else 2)
    c.text(x, y + 34, 'FUCK SOCIETY.', 15, P['soft'], weight='bold', spacing=1.5)
    c.text(x, y + 62, 'HACK THE WORLD.', 15, P['soft'], weight='bold', spacing=1.5)
    c.add('</g>')


def display_rows(source, mobile):
    if not mobile:
        return source.rstrip('\n').split('\n')
    rows = []
    for line in source.rstrip('\n').split('\n'):
        if not line.strip():
            rows.append('')
            continue
        if set(line.strip()) <= set('=-_'):
            rows.append(line.strip())
            continue
        prefix = '  ' if line.startswith('        ') and not line.startswith('                    ') else ''
        rows.extend(textwrap.wrap(line.strip(), width=36, initial_indent=prefix,
                                  subsequent_indent='', break_on_hyphens=False,
                                  replace_whitespace=False, drop_whitespace=True))
    return rows


def vim(c, x, y, w, rows, mobile):
    fs, leading = (22, 31) if mobile else (20.5, 29)
    total = len(rows)
    text_top = y + 124
    content_bottom = text_top + total * leading + 16
    h = content_bottom - y + 92
    c.add('<g id="vim-window" aria-label="Historical manifesto in vim">')
    frame(c, x, y, w, h, 'Hacker Manifesto.txt — vim' if not mobile else 'Hacker Manifesto.txt / vim', dark=True, active=True, number='' if mobile else '01')
    c.rect(x + 1, y + 44, w - 2, 34, '#1d211c')
    c.text(x + 19, y + 67, 'PHRACK 01:07:03', 12, P['brass'])
    c.text(x + w - 20, y + 67, 'READ ONLY / UTF-8', 11, P['dim'], anchor='end')
    gutter = 56 if mobile else 76
    c.path(f'M{x+gutter-14} {y+92}V{content_bottom}', '#2d332b')
    c.add('<g id="manifesto-text" aria-label="Original Phrack text">')
    for i, line in enumerate(rows):
        is_header = i < (15 if not mobile else 22)
        fill = P['brass'] if is_header or line.strip() == '+++The Mentor+++' else P['text']
        row_fs = min(fs, (w - gutter - 27) / (max(len(line), 1) * .60205))
        c.text(x + gutter, text_top + i * leading, line, row_fs, fill, fit=True, data_source_line=i+1)
    c.add('</g>')
    for i in range(total):
        c.text(x + gutter - 27, text_top + i * leading, str(i + 1), 12,
               '#727b6c', anchor='end', fit=True)
    # Place the normal-mode cursor on the original closing signature.
    cursor_line = max((i for i, line in enumerate(rows) if line.strip() == '+++The Mentor+++'), default=total-1)
    cursor_col = len(rows[cursor_line]) - len(rows[cursor_line].lstrip())
    c.rect(x + gutter + cursor_col * fs * .60205,
           text_top + cursor_line * leading - fs + 2, fs * .60205, fs + 3,
           P['brass'], opacity='.45')
    c.rect(x + 1, y + 79, w - 2, content_bottom - y - 79, 'url(#crt)')
    sy = content_bottom + 12
    c.rect(x + 1, sy, w - 2, 32, '#333a2f')
    c.rect(x + 1, sy, 104, 32, P['brass'])
    c.text(x + 16, sy + 22, 'NORMAL', 16, P['ink'], weight='bold')
    c.text(x + 119, sy + 22, 'manifesto.txt', 14, P['text'])
    c.text(x + w - 18, sy + 22, f'{cursor_line+1},{cursor_col+1}  All', 13, P['text'], anchor='end')
    c.text(x + 17, sy + 62, '"manifesto.txt" [readonly]', 12, P['dim'])
    if not mobile:
        c.text(x + w - 18, sy + 62, f'{total}L / unix / text', 12, P['dim'], anchor='end')
    c.add('</g>')
    return h


def draw(source, mobile=False):
    c = Canvas()
    width = 640 if mobile else 1440
    rows = display_rows(source, mobile)
    main_x, main_y, main_w = (26, 1465, 588) if mobile else (240, 865, 1104)
    leading = 31 if mobile else 29
    main_h = 124 + len(rows) * leading + 16 + 92
    height = main_y + main_h + (242 if mobile else 300)
    c.add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">')
    c.add('<title id="title">NULL/X — an independent hacker workstation</title>')
    c.add('<desc id="desc">A paper-beige futuristic Unix desktop with Netscape, AMP playing Break Stuff by Limp Bizkit, Files, xterm, IRC and Packet icons, an analog clock, a Red Hat Linux 6.2 terminal, and the full original The Conscience of a Hacker by The Mentor in vim. The wallpaper reads NO OWNER. NO MASTER. FUCK SOCIETY. HACK THE WORLD. Read the linked text for an accessible copy of the original manifesto.</desc>')
    definitions(c)
    wallpaper(c, width, height, mobile)
    menu(c, width, mobile)
    if mobile:
        c.text(35, 136, 'NULL', 56, P['olive'], mono=False, spacing=7, opacity='.28')
        c.text(37, 164, 'INDEPENDENT WINDOW SYSTEM', 10, P['olive'], spacing=1.1)
        desktop_motto(c, 37, 197, True)
        icon(c, 47, 321, 'netscape', 'Netscape')
        icon(c, 177, 321, 'audio', 'AMP')
        icon(c, 47, 466, 'files', 'Files')
        icon(c, 177, 466, 'terminal', 'xterm')
        icon(c, 47, 611, 'irc', 'IRC')
        icon(c, 177, 611, 'packet', 'Packet')
        clock(c, 322, 318, 270)
        c.text(54, 744, 'WORKSPACE / 01', 12, P['olive'], spacing=1)
        amp(c, 53, 776, 534, mobile=True)
        legacy_terminal(c, 53, 1046, 534, True)
        c.path('M54 1391H584', P['line'])
        c.text(54, 1419, '01 / CONSCIENCE', 12, P['olive'], spacing=2)
    else:
        c.text(271, 205, 'NULL', 84, P['olive'], mono=False, spacing=14, opacity='.25')
        c.text(277, 240, 'INDEPENDENT WINDOW SYSTEM', 14, P['olive'], spacing=2)
        desktop_motto(c, 278, 274)
        c.path('M700 150H948V294H788M700 157H744M941 250V287', P['line'])
        c.circle(824, 213, 38, 'none', P['line'])
        c.circle(824, 213, 20, 'none', P['line'])
        c.path('M765 213H883M824 154V272', P['line'], .7)
        for i, (kind, label) in enumerate([('netscape', 'Netscape'), ('audio', 'AMP'), ('files', 'Files'), ('terminal', 'xterm'), ('irc', 'IRC'), ('packet', 'Packet')]):
            icon(c, 61, 153 + i * 158, kind, label)
        clock(c, 1057, 151)
        legacy_terminal(c, 300, 423, 682, False)
        amp(c, 999, 540)
        c.text(300, 798, '01 / CONSCIENCE', 14, P['olive'], spacing=2)
        c.path('M548 793H1344', P['line'])
        c.text(1344, 823, 'THE MACHINE IS QUIET. THE MIND IS NOT.', 11, P['olive'], anchor='end', spacing=1)
    vim(c, main_x, main_y, main_w, rows, mobile)
    fy = height - (152 if mobile else 190)
    c.path(f'M{main_x} {fy-28}H{main_x+main_w}', P['line'])
    c.text(main_x, fy, 'THE CONSCIENCE OF A HACKER', 12 if mobile else 16, P['soft'], spacing=1)
    c.text(main_x, fy + 28, 'Loyd Blankenship / The Mentor / 08 Jan 1986', 10 if mobile else 13, P['olive'])
    c.text(main_x, fy + 52, 'Phrack Magazine / Vol. 1, Issue 7, Phile 3', 10 if mobile else 13, P['olive'])
    c.text(main_x, fy + 76, 'phrack.org / original text / copynow', 10 if mobile else 12, P['olive'])
    c.rect(0, height - 50, width, 50, P['ink'])
    emblem(c, 25, height - 39, .65, P['brass'])
    c.text(63, height - 20, 'SESSION 01', 12, P['paper'])
    if not mobile:
        c.text(274, height - 20, '[ 01 : vim ]    02 : XCLOCK    03 : XTERM    04 : AMP', 12, P['paper'])
    c.text(width - 23, height - 20, 'END OF TRANSMISSION', 10, P['brass'], anchor='end', spacing=1)
    c.add('</svg>')
    return '\n'.join(c.parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', type=Path, default=ROOT / 'assets/manifesto.txt', help='UTF-8 source; never fetched during builds')
    args = parser.parse_args()
    source = args.text.read_text(encoding='utf-8')
    assets = ROOT / 'assets'
    assets.mkdir(exist_ok=True)
    for mobile, name in [(False, 'hacker-desktop.svg'), (True, 'hacker-desktop-mobile.svg')]:
        result = draw(source, mobile)
        (assets / name).write_text(result, encoding='utf-8')
        digest = sha256(result.encode('utf-8')).hexdigest()[:10]
        versioned_name = f'{Path(name).stem}-{digest}.svg'
        (assets / versioned_name).write_text(result, encoding='utf-8')
        for old in assets.glob(f'{Path(name).stem}-*.svg'):
            if re.fullmatch(r'hacker-desktop(?:-mobile)?-[0-9a-f]{10}\.svg', old.name) and old.name != versioned_name:
                old.unlink()
        print(f'{name}: {len(result):,} characters')
    (assets / 'session.txt').write_text(source, encoding='utf-8')
    # GitHub's raw redirect drops query strings. Fingerprint filenames instead,
    # so a previous drawing cannot survive in the raw-image cache.
    readme = ROOT / 'README.md'
    if readme.exists():
        def versioned(match):
            path = ROOT / f'{match.group(1)}.svg'
            digest = sha256(path.read_bytes()).hexdigest()[:10]
            return f'{match.group(1)}-{digest}.{match.group(2)}'
        pattern = r'(assets/hacker-desktop(?:-mobile)?)(?:-[0-9a-f]{10})?\.(svg|png)(?:\?v=[A-Za-z0-9_-]+)?'
        readme.write_text(re.sub(pattern, versioned, readme.read_text()), encoding='utf-8')


if __name__ == '__main__':
    main()
