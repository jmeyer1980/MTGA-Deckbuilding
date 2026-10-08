const fs = require('fs');
const snap = fs.readFileSync('mulligan-patch-v2.txt', 'utf8');
// extract the landVal function from the patch (between 'const landVal' and the closing '};')
const landValMatch = snap.match(/const landVal = .*?\};/s);
if (!landValMatch) { console.error('landVal not found'); process.exit(1); }
const landValSrc = landValMatch[0];
console.log('--- landVal source ---');
console.log(landValSrc);

// Fabled Passage deck entry (as built by drill_build_v2.py)
const entry = { n: 'Fabled Passage', q: 1, l: true, c: 0, t: ['half'] };

let landVal;
eval(landValSrc.replace('const landVal', 'let landVal'));
console.log('landVal(entry) =', landVal(entry));

// Sanity: Nykthos half (tag only) and a normal land
const nyk = { n: 'Nykthos, Shrine to Nyx', q: 1, l: true, c: 0, t: ['half'] };
console.log('landVal(Nykthos) =', landVal(nyk));
const plains = { n: 'Plains', q: 1, l: true, c: 0, t: [] };
console.log('landVal(Plains) =', landVal(plains));
const hare = { n: 'Hare Apparent', q: 1, l: false, c: 2, t: [] };
console.log('landVal(Hare Apparent) =', landVal(hare));
