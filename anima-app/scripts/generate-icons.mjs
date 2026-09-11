import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const publicDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'public');
const svg = readFileSync(join(publicDir, 'icon.svg'));

let sharp;
try {
  sharp = (await import('sharp')).default;
} catch (e) {
  console.warn('⚠ sharp not available — skipping PNG icons (SVG-only PWA still installs on Chrome).');
  console.warn('  To enable PNGs later: npm install -D sharp  then re-run this script.');
  process.exit(0);
}

const targets = [['icon-192.png', 192], ['icon-512.png', 512], ['apple-touch-icon.png', 180]];
for (const [name, size] of targets) {
  try {
    await sharp(svg, { density: 384 }).resize(size, size).png().toFile(join(publicDir, name));
    console.log(`  generated ${name}`);
  } catch (e) {
    console.warn(`  ⚠ could not render ${name}: ${e.message}`);
  }
}
console.log('Icon step done.');
