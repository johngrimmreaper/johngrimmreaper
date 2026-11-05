#!/usr/bin/env python3
"""Verify source fidelity, generated text, geometry and self-contained SVGs."""
import hashlib
import base64
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from generate_desktop import ROOT, draw

EXPECTED_SHA256 = 'f89a1f57a4f38b746a32f464ae680d5f9ba225941f14d46d65aef85e59a071cc'
NS = {'s': 'http://www.w3.org/2000/svg'}
source_bytes = (ROOT / 'assets/manifesto.txt').read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_SHA256, 'Historical source changed'
source = source_bytes.decode('utf-8')
compact = lambda value: re.sub(r'\s', '', value)
allowed_tags = {'svg', 'title', 'desc', 'defs', 'linearGradient', 'radialGradient',
                'stop', 'pattern', 'path', 'rect', 'text', 'circle', 'g', 'image'}
reference = (ROOT / 'assets/icons/netscape-reference.png').read_bytes()
assert hashlib.sha256(reference).hexdigest() == '4720594dfba04a5a013d126871c7a9722b704df106a4996a9fed1e2331fa36d0', 'Supplied icon changed'
scaled_icon = (ROOT / 'assets/icons/netscape-128.png').read_bytes()

for mobile, name in [(False, 'hacker-desktop.svg'), (True, 'hacker-desktop-mobile.svg')]:
    path = ROOT / 'assets' / name
    xml = path.read_text()
    root = ET.fromstring(xml)
    assert xml == draw(source, mobile), f'{name}: regenerate assets'
    assert '[hacker@localhost hacker]$' in xml, f'{name}: normal-user shell missing'
    assert 'root@localhost' not in xml, f'{name}: root shell must not appear'
    for el in root.iter():
        assert el.tag.split('}')[-1] in allowed_tags, f'{name}: unexpected SVG element'
        assert not any(k.lower().startswith('on') for k in el.attrib), 'Event attribute'
        for key, value in el.attrib.items():
            if key.split('}')[-1] == 'href':
                assert el.tag.endswith('}image') and value.startswith('data:image/png;base64,'), 'External dependency'
                assert base64.b64decode(value.split(',', 1)[1], validate=True) == scaled_icon, 'Icon does not match supplied artwork'
    icons = root.findall('.//s:image[@id="netscape-reference"]', NS)
    assert len(icons) == 1 and icons[0].get('width') == icons[0].get('height') == '70', 'Scaled Netscape icon missing'
    original = root.find('.//s:g[@id="manifesto-text"]', NS)
    rendered = ''.join(el.text or '' for el in original.findall('s:text', NS))
    assert compact(rendered) == compact(source), f'{name}: omitted or altered historical text'
    window = root.find('.//s:g[@id="vim-window"]', NS)
    window_text = ''.join(window.itertext())
    assert 'FUCK SOCIETY' not in window_text and 'HACK THE WORLD' not in window_text
    assert root.find('.//s:g[@id="local-addendum"]', NS) is None
    assert 'VIM' not in xml and 'Vim' not in xml, f'{name}: vim must be lowercase'
    motto = root.find('.//s:g[@id="desktop-motto"]', NS)
    motto_lines = [el.text for el in motto.findall('s:text', NS)]
    assert motto_lines == ['NO OWNER. NO MASTER.', 'FUCK SOCIETY.', 'HACK THE WORLD.']
    amp = root.find('.//s:g[@id="amp-player"]', NS)
    player_text = ''.join(amp.itertext())
    assert all(label in player_text for label in ['LIMP BIZKIT', 'BREAK STUFF', 'PLAYING', '01:08'])
    assert 'NO CARRIER' not in xml
    win_x, win_y, win_w = (26, 1465, 588) if mobile else (240, 865, 1104)
    for el in original.findall('s:text', NS):
        left = float(el.get('x'))
        right = left + float(el.get('textLength', '0'))
        assert win_x < left < right + 1 <= win_x + win_w - 20, f'{name}: text overflow'
        assert float(el.get('y')) > win_y + 80
        if el.text and set(el.text.strip()) - set('=-_'):
            assert float(el.get('font-size')) >= (21 if mobile else 20), 'Text shrunk to fit'
    if not mobile:
        height = float(root.get('height'))
        # More than 45% of the scene lies outside the vim window.
        win_h = 124 + len(original.findall('s:text', NS)) * 29 + 16 + 92
        ratio = win_w * win_h / (1440 * height)
        assert ratio < .55, 'Desktop breathing room lost'
        print(f'Desktop: vim occupies {ratio:.1%} of the scene')
    print(f'{name}: original text, wallpaper slogans, lowercase vim, AMP playing, no overflow')

assert (ROOT / 'assets/session.txt').read_bytes() == source_bytes, 'Text fallback must contain only the original manifesto'
print(f'Original source: {len(source_bytes)} bytes; pinned SHA-256 matches')
