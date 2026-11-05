#!/usr/bin/env node
// Optional live browser QA. Uses an installed Playwright and Chromium.
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const output = resolve(process.env.PROFILE_QA_OUTPUT || '/tmp/null-x-profile-qa');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
});
try {
  for (const [name, width, height, expected] of [
    ['desktop', 1280, 1000, 'hacker-desktop'],
    ['mobile', 390, 844, 'hacker-desktop-mobile'],
  ]) {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    await page.goto('https://github.com/johngrimmreaper', { waitUntil: 'domcontentloaded' });
    const image = page.locator('article img[alt^="NULL/X:"]');
    await image.waitFor({ state: 'visible' });
    await page.waitForFunction(() => {
      const i = document.querySelector('article img[alt^="NULL/X:"]');
      return i?.complete && i.naturalWidth > 0;
    });
    const state = await image.evaluate(i => ({
      src: i.currentSrc, width: i.naturalWidth, height: i.naturalHeight,
      box: i.getBoundingClientRect().toJSON(), viewport: window.innerWidth,
      overflow: document.documentElement.scrollWidth > window.innerWidth,
    }));
    if (!new RegExp(`${expected}-[a-f0-9]{10}\\.svg$`).test(new URL(state.src).pathname)) throw Error(`${name}: wrong picture source`);
    if (state.overflow) throw Error(`${name}: horizontal page overflow`);
    if (state.viewport !== width) throw Error(`${name}: viewport was not applied`);
    await page.locator('article').screenshot({ path: resolve(output, `${name}-article.png`) });
    await page.screenshot({ path: resolve(output, `${name}-profile.png`) });
    // Inspect the icon in the README's SVG-as-image rendering context.
    // GitHub's standalone raw-SVG document has a different, restrictive CSP.
    const iconBox = await image.evaluate(i => {
      i.scrollIntoView({ block: 'start' });
      const box = i.getBoundingClientRect();
      const scale = box.width / i.naturalWidth;
      const mobile = window.innerWidth <= 700;
      return { x: box.x + (mobile ? 47 : 61) * scale,
               y: box.y + (mobile ? 321 : 153) * scale,
               width: 70 * scale, height: 70 * scale };
    });
    await page.screenshot({ path: resolve(output, `${name}-netscape-icon.png`), clip: iconBox, scale: 'css' });
    console.log(name, JSON.stringify(state));
    await page.goto(state.src, { waitUntil: 'load' });
    const geometry = await page.evaluate(mobile => {
      const bounds = mobile ? { left: 26, right: 614 } : { left: 240, right: 1344 };
      const texts = [...document.querySelectorAll('#manifesto-text text')];
      const overflow = texts.filter(t => {
        const b = t.getBBox();
        return b.width && (b.x < bounds.left || b.x + b.width > bounds.right - 20);
      }).map(t => t.textContent);
      return {
        lines: texts.length, overflow,
        normalUser: document.documentElement.textContent.includes('[hacker@localhost hacker]$'),
        rootUser: document.documentElement.textContent.includes('root@localhost'),
        lowercaseVim: !/\bVIM\b|\bVim\b/.test(document.documentElement.textContent),
        motto: [...document.querySelectorAll('#desktop-motto text')].map(e => e.textContent),
        terminalSlogans: /FUCK SOCIETY|HACK THE WORLD/.test(document.querySelector('#vim-window').textContent),
        playing: ['LIMP BIZKIT', 'BREAK STUFF', 'PLAYING', '01:08'].every(t => document.querySelector('#amp-player')?.textContent.includes(t)),
      };
    }, name === 'mobile');
    if (!geometry.lines || geometry.overflow.length) throw Error(`${name}: SVG glyph overflow: ${JSON.stringify(geometry)}`);
    if (!geometry.normalUser || geometry.rootUser) throw Error(`${name}: stale or incorrect shell prompt`);
    if (!geometry.lowercaseVim || geometry.terminalSlogans || !geometry.playing ||
        geometry.motto.join('|') !== 'NO OWNER. NO MASTER.|FUCK SOCIETY.|HACK THE WORLD.') {
      throw Error(`${name}: profile edits missing: ${JSON.stringify(geometry)}`);
    }
    const icon = page.locator('#netscape-reference');
    if (await icon.count() !== 1) throw Error(`${name}: supplied Netscape icon missing`);
    console.log(name, 'live SVG glyph bounds verified', geometry.lines, 'lines');
    await page.close();
  }
} finally {
  await browser.close();
}
