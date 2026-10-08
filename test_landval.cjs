const fs = require('fs');
const patchFile = 'C:\\Users\\jerio\\RiderProjects\\MTGA Deckbuilding\\mulligan-patch-v2.txt';
const snap = fs.readFileSync(patchFile, 'utf8');
const landValMatch = snap.match(/const landVal = .*?\};/s);
if (!landValMatch) { console.error('landVal not found'); process.exit(1); }
let body = landValMatch[0]
  .replace('const landVal = c => {', '(c) => {')
  .replace(/}\s*;$/, '}'); // drop the `;` (empty stmt) after the block close, keep the `}`
console.log('--- landVal body ---');
console.log(body);
const landVal = eval('(' + body + ')');
console.log('landVal(Fabled Passage) =', landVal({ n: 'Fabled Passage', q: 1, l: true, c: 0, t: ['half'] }));
console.log('landVal(Nykthos) =', landVal({ n: 'Nykthos, Shrine to Nyx', q: 1, l: true, c: 0, t: ['half'] }));
console.log('landVal(Plains) =', landVal({ n: 'Plains', q: 1, l: true, c: 0, t: [] }));
console.log('landVal(Hare Apparent) =', landVal({ n: 'Hare Apparent', q: 1, l: false, c: 2, t: [] }));
console.log('landVal(Ojer Taq) =', landVal({ n: 'Ojer Taq, Deepest Foundation', q: 1, l: false, c: 6, t: ['stranded'] }));
