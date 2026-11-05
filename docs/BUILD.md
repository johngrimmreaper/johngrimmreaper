# Building the desktop

The profile README embeds static assets only. `preview.html` is a local proof,
not a deployed app. No Actions, JavaScript, remote fonts, SVG `foreignObject`,
external resources, or runtime services are required. The supplied Netscape
PNG is embedded inside the SVG as a data URI; terminal text stays vector text.

Generate and verify with Python 3 (standard library only):

```sh
python3 scripts/generate_desktop.py
python3 scripts/verify_text.py
sh scripts/preview.sh
```

Generate the optional PNG fallback with Node.js and `sharp` installed from npm:

```sh
node scripts/render_png.mjs
```

`SHARP_MODULE` can point at an already installed sharp module. PNGs use system
DejaVu Sans / DejaVu Sans Mono. SVG text also has Liberation Mono, Consolas and
generic monospace fallbacks. Explicit text lengths retain terminal geometry
across fonts. Text remains real, accessible SVG text.

The owner's original Netscape artwork is preserved as
`assets/icons/netscape-reference.png`. Its checked-in 128-pixel derivative is
created with `node scripts/prepare_icons.mjs` using Lanczos downsampling only.
It keeps the complete image, background and colors and is displayed at 70 × 70
SVG units. SVG generation itself requires no image-processing dependencies.

The desktop is 1440 units wide. The mobile scene is 640 units wide, with the
same historical text rewrapped without changing its non-whitespace characters.
The README's `picture` selects mobile artwork below 700 CSS pixels; SVG-capable
clients use SVG first, while raster fallbacks are included for both layouts.
Select the artwork to read `assets/session.txt`, an exact copy of the original
manifesto. The owner's slogans belong to the wallpaper beneath the NULL system
heading and appear outside the vim window in both layouts. AMP displays
Limp Bizkit's "Break Stuff" with a playing indicator and elapsed time.
The generator creates copies with content fingerprints in their filenames and
updates the README references. This refreshes GitHub's raw-image cache when the
SVG changes. The PNG renderer creates corresponding raster copies. Regenerate
both SVG and PNG assets before publishing artwork changes.

The pinned `assets/manifesto.txt` is the original Phrack text, including source
line breaks, indentation and signature. Its bytes are never rewritten by the
generator. `--text /path/to/authorized-source.txt` accepts another source for
local rendering; the fidelity verifier intentionally pins the historical source.
The profile owner's slogans are generated only on the desktop wallpaper.

See [SOURCES.md](SOURCES.md) for palette, historical and reproduction provenance.

Optional live QA: `node scripts/inspect_profile.mjs` uses Playwright/Chromium to
check the actual public profile at 1280 and 390 CSS pixels, selected SVG sources,
horizontal overflow and rendered glyph bounds. `PLAYWRIGHT_MODULE` and
`CHROMIUM_PATH` can select existing installations. Screenshots go to
`/tmp/null-x-profile-qa` (override with `PROFILE_QA_OUTPUT`).
Icon screenshots use the README's actual image rendering context. GitHub's
separate raw-SVG document view blocks data images through its CSP.
