/* Used by A14: execute the real front-end kernel in Node and emit verdict JSON for the golden set. */
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error('NO_SCRIPT'); process.exit(2); }
const js = m[1].replace(/window\.addEventListener[\s\S]*$/, '');
const tail = `
const gold = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = {
  cases: gold.cases.map(c => analyze(c.text).verdicts.map(v => v.verdict)),
  pairs: gold.paraphrase_pairs.map(p => [
    analyze(p.a).verdicts.map(v => v.verdict),
    analyze(p.b).verdicts.map(v => v.verdict)
  ])
};
console.log(JSON.stringify(out));
`;
eval(js + tail);
