#!/usr/bin/env node
// Optional fallback rasterization. Install sharp from npm, or set SHARP_MODULE
// to an existing sharp module directory. SVG generation needs only Python.
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { copyFile, readFile, readdir, unlink } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

const require = createRequire(import.meta.url);
const sharp = require(process.env.SHARP_MODULE || 'sharp');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
for (const name of ['hacker-desktop', 'hacker-desktop-mobile']) {
  const target = resolve(root, 'assets', `${name}.png`);
  await sharp(resolve(root, 'assets', `${name}.svg`)).png().toFile(target);
  const digest = createHash('sha256').update(await readFile(resolve(root, 'assets', `${name}.svg`))).digest('hex').slice(0, 10);
  const versionedName = `${name}-${digest}.png`;
  await copyFile(target, resolve(root, 'assets', versionedName));
  for (const old of await readdir(resolve(root, 'assets'))) {
    if (new RegExp(`^${name}-[a-f0-9]{10}\\.png$`).test(old) && old !== versionedName) {
      await unlink(resolve(root, 'assets', old));
    }
  }
  console.log(target);
}
