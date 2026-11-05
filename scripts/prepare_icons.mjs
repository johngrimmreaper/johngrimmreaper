#!/usr/bin/env node
// Scale the owner-supplied PNG; keep the complete image and its original colors.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

const require = createRequire(import.meta.url);
const sharp = require(process.env.SHARP_MODULE || 'sharp');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
await sharp(resolve(root, 'assets/icons/netscape-reference.png'))
  .resize(128, 128, { fit: 'contain', kernel: sharp.kernel.lanczos3 })
  .png()
  .toFile(resolve(root, 'assets/icons/netscape-128.png'));
console.log('Prepared 128 × 128 Netscape icon from the supplied image');
