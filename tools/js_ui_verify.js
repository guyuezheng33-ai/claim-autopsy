/* Used by A20: execute the REAL front-end rendering functions in Node with a
 * minimal DOM stub. This checks behaviour, not the presence of a string.
 * Usage: node tools/js_ui_verify.js web/index.html
 */
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error('NO_SCRIPT'); process.exit(2); }
const js = m[1].replace(/window\.addEventListener[\s\S]*$/, '');

function el(){
  return {
    innerHTML:'', textContent:'', value:'', style:{}, _children:[],
    classList:{add(){},remove(){},toggle(){}},
    querySelectorAll(){return [];}, querySelector(){return null;},
    addEventListener(){}, getAttribute(){return '';},
    appendChild(x){this._children.push(x);}, scrollIntoView(){}, focus(){}
  };
}
const nodes = {};
global.document = {
  getElementById(id){ if(!nodes[id]) nodes[id]=el(); return nodes[id]; },
  querySelectorAll(){return [];},
  createElement(){return el();}
};
global.location = {protocol:'file:'};
global.window = global;

eval(js + `
initMetrics();
initReplay();
initCorpus();
const refusalTexts = [
  'The new iPhone battery lasts three days.',
  'Coffee stunts your growth.',
  'A certain water purifier can cure diabetes, and drinking water can make you ten centimetres taller in a week.'
];
const cases = refusalTexts.map(t => {
  const r = analyze(t);
  const box = document.getElementById('claims');
  box._children = [];
  render(r, 'Local deterministic core');
  const h = box._children.map(c => c.innerHTML).join('');
  return {text:t, verdicts:r.verdicts.map(v=>v.verdict),
          cov_hints:(h.match(/class="cov-hint"/g)||[]).length,
          anatomies:(h.match(/class="anatomy"/g)||[]).length,
          qchips:(h.match(/class="qchip"/g)||[]).length,
          has_browse_button: h.indexOf('jumpToCorpus(') >= 0};
});
const gateInputs = ["\u5730\u7403\u4e0d\u662f\u5706\u7684", "", "Why is the sky blue?"];
const gates = gateInputs.map(t => {
  const r = analyze(t);
  render(r, 'Local deterministic core');
  const h = nodes['claims'].innerHTML;
  const u = r.unsupported_input || {};
  return {input_kind:u.kind, claims:r.summary.claims, verdicts:r.verdicts.length,
          notice:(h.indexOf('class="notcheck"') >= 0), title:(u.title||''),
          action:(u.action||'')};
});
const control_verdicts = analyze('Antibiotics can treat a common cold.').verdicts.map(v => v.verdict);
const outcomeInputs = [
  'the lack of Vitamin D make you more susceptible to the Covid-19 coronavirus',
  'Vitamin supplements can cure COVID-19',
  'Vitamin D prevents COVID-19',
  'Several recent studies have looked at the impact of vitamin D on COVID-19'
];
const outcome_cases = outcomeInputs.map(t => {
  const r = analyze(t), v = r.verdicts[0] || {};
  return {text:t, verdict:v.verdict || 'gated',
          near:(v.near_miss||[]).map(x => ({card_id:x.card_id, reasons:x.reasons}))
            .filter(x => (x.reasons||[]).some(q => q==='different_outcome'))};
});
const trapInputs = [
  'The Earth is round and flat.',
  'Antibiotics can cure a common cold and flu.',
  'Coffee prevents cancer.',
  'Vitamin C cures the flu.',
  'Carrots cure blindness.',
  'MSG causes headaches in everyone.',
  'The Earth is round.'
];
const trap_cases = trapInputs.map(t => {
  const r = analyze(t);
  return {text:t, claims:r.verdicts.map(v=>v.claim), verdicts:r.verdicts.map(v=>v.verdict)};
});
const scopeInputs = [
  'Coffee causes cancer in children.',
  'Vitamin C cures the flu in pregnant women.',
  'MSG causes headaches in pregnant women.',
  'Getting a flu vaccine gives you the flu in infants.',
  'Antibiotics can treat a common cold in adults.',
  'Flu vaccination is unsafe for pregnant women.',
  "Vaccines overwhelm an infant's immune system.",
  'Vitamin C 500 mg prevents a cold.'
];
const scope_cases = scopeInputs.map(t => {
  const r = analyze(t);
  return {text:t, claims:r.verdicts.map(v=>v.claim), verdicts:r.verdicts.map(v=>v.verdict)};
});
const anchorInputs = [
  'Getting a flu vaccine gives you the flu.',
  'Antibiotics cure viral infections.',
  'Eating carrots supports eye health.'
];
const anchor_cases = anchorInputs.map(t => {
  const r = analyze(t);
  return {text:t, anchors:r.verdicts.map(v => v.citations.map(c => c.matched || []))};
});
const anchorBox = document.getElementById('claims');
anchorBox._children = [];
render(analyze(anchorInputs[0]), 'Local deterministic core');
const anchor_html = anchorBox._children.map(c => c.innerHTML).join('');
const nearInputs = [
  'Coffee causes cancer in children.',
  'Vitamin C cures the flu in pregnant women.',
  'MSG causes headaches in pregnant women.',
  'Coffee stunts your growth.',
  'The iPhone battery lasts three days.'
];
const near_cases = nearInputs.map(t => {
  const r = analyze(t), v = r.verdicts[0] || {};
  return {text:t, verdict:v.verdict,
          near:(v.near_miss||[]).map(x => ({card_id:x.card_id, reasons:x.reasons}))};
});
const qtyInputs = [
  'Folic acid 400 mcg daily prevents neural tube defects.',
  'Folic acid 40 mcg daily prevents neural tube defects.',
  'Folic acid 4000 mcg daily prevents neural tube defects.',
  'Hand sanitizer with 60% alcohol works well.',
  'Hand sanitizer with 40% alcohol works well.',
  'Washing hands with soap prevents the spread of respiratory infections.'
];
const qty_cases = qtyInputs.map(t => {
  const r = analyze(t), v = r.verdicts[0] || {};
  return {text:t, verdict:v.verdict,
          near:(v.near_miss||[]).map(x => ({card_id:x.card_id, reasons:x.reasons}))};
});
const consInputs = [
  'The Earth is round and the Earth is flat.',
  'Flu vaccines are safe. Flu vaccines are not safe.',
  'The Earth is round. The Earth is spherical.',
  'Coffee causes cancer. Coffee prevents cancer.',
  'Getting a flu vaccine gives you the flu. Antibiotics can treat a common cold.'
];
const relation_cases = consInputs.map(t => {
  const r = analyze(t);
  const claims = r.verdicts.map(v => v.claim);
  return {text:t, claims:claims,
          relations:consRelations(claims).map(x => ({atoms:x.atoms, basis:x.basis}))};
});
const stanceInputs = [
  'Taking more than 4,000 IU of vitamin D per day is not recommended.',
  'Rubbing hands with alcohol gel prevents the spread of flu.',
  'Vitamin D 10,000 IU a day is safe.',
  'Flu vaccination is unsafe for pregnant women.'
];
const stance_cases = stanceInputs.map(t => {
  const r = analyze(t);
  const v = r.verdicts[0] || {};
  return {text:t, claims:r.verdicts.map(x => x.claim), verdict:v.verdict,
          cards:(v.citations||[]).map(c => c.card_id)};
});
const chainInputs = [
  'Coffee causes cancer. Cancer causes death. Coffee prevents death.',
  'Coffee causes cancer. Cancer causes death.',
  'Coffee causes cancer. Cancer causes death. Coffee causes death.',
  'Coffee prevents cancer. Cancer causes death. Coffee prevents death.',
  'Coffee causes cancer. Water causes death.'
];
const chain_cases = chainInputs.map(t => {
  const r = analyze(t);
  return {text:t, chains:(r.chains||[]).map(x => ({atoms:x.atoms, derived:x.derived, basis:x.basis, conflict:!!x.conflict}))};
});
const guardFile = require('path').join(__dirname, '..', 'data', 'guard_set.json');
const guard_cases = JSON.parse(fs.readFileSync(guardFile,'utf8')).probes.map(p => {
  const r = analyze(p.text), v = r.verdicts[0] || {};
  return {id:p.id, text:p.text, atoms:r.verdicts.length, verdict:v.verdict,
          cards:(v.citations||[]).map(c => c.card_id)};
});
const snapInputs = [
  'Getting a flu vaccine gives you the flu.',
  'A common cold can resolve on its own.',
  'Vaccines cause autism.'
];
const snapshot_cases = snapInputs.map(t => {
  const r = analyze(t), v = r.verdicts[0] || {};
  const c = (v.citations||[])[0] || {};
  return {text:t, verdict:v.verdict, card:c.card_id || null,
          status:(c.snap||{}).st || null, paragraph:(c.snap||{}).p == null ? null : (c.snap||{}).p,
          hash:((c.snap||{}).h || '').slice(0,12), excerpt:((c.snap||{}).x || '').slice(0,60)};
});
const snapBox = document.getElementById('claims');
snapBox._children = [];
render(analyze(snapInputs[0]), 'Local deterministic core');
const snap_html = snapBox._children.map(c => c.innerHTML).join('');
const page_snap_counts = Object.keys(DATA.snaps || {}).reduce((acc, k) => {
  const st = (DATA.snaps[k] || {}).st || 'unknown';
  acc[st] = (acc[st] || 0) + 1;
  return acc;
}, {});
const corpus_snap_badges = (document.getElementById('corpusList').innerHTML.match(/snap-badge/g) || []).length;
const spInputs = [
  'Getting a flu vaccine gives you the flu.',
  'Antibiotics can treat a common cold.',
  'Coffee causes cancer in children.',
  'A certain water purifier can cure diabetes, and drinking water can make you ten centimetres taller in a week.',
  'The new iPhone battery lasts three days.',
  'Vitamin D prevents COVID-19',
  'Coffee causes cancer. Cancer causes death. Coffee prevents death.',
  'Getting a flu vaccine gives you the flu in infants.',
  'The Earth is flat.',
  'Folic acid 40 mcg daily prevents neural tube defects.',
  'MSG causes headaches in pregnant women.',
  'Vitamin C cures the flu.'
];
const sp_cases = spInputs.map(t => {
  const r = analyze(t), v = r.verdicts[0] || {};
  return {text:t, verdict:v.verdict || 'gated', scope:v.scope || null, plan:v.plan || null};
});
const batch_cases = analyzeBatch(spInputs);
const batch_mapped = {n:batch_cases.n, dropped:batch_cases.dropped, limit:batch_cases.limit,
  counts:batch_cases.counts,
  items:batch_cases.items.map(x => ({input:x.input, claims:x.claims, supported:x.supported,
    refuted:x.refuted, undetermined:x.undetermined, verdict:x.verdict, sources:x.sources}))};
renderBatch(batch_cases);
const batch_html = nodes['batchOut'].innerHTML;
const batch_rendered = {rows:(batch_html.match(/<tr>/g)||[]).length,
  badges:(batch_html.match(/class="badge /g)||[]).length,
  count_text:nodes['batchCount'].textContent};
const citCases = JSON.parse(fs.readFileSync(__dirname + '/../data/citation_cases.json', 'utf8')).cases;
const citation_cases = citCases.map(c => {
  const r = citationAudit(c.claim, c.source);
  return {id:c.id, verdicts:(r.verdicts||[]).map(v => v.verdict), expected:c.expected,
          summary:r.summary, sentences:(r.source||{}).sentences};
});
const citBox = document.getElementById('claims');
citBox._children = [];
const firstCit = citationAudit(citCases[0].claim, citCases[0].source);
if (typeof renderCitation === 'function') renderCitation(firstCit);
const cit_html = citBox._children.map(c => c.innerHTML).join('');
const citation_rendered = {badges:(cit_html.match(/class="badge /g)||[]).length,
  quotes:(cit_html.match(/class="cit-quote"/g)||[]).length,
  meta:document.getElementById('runmeta').textContent};
console.log(JSON.stringify({
  metrics: nodes['metrics'].innerHTML,
  replay_chips: (nodes['replayChips'].innerHTML.match(/class="chip/g)||[]).length,
  replay_offline: nodes['replayOffline'].innerHTML,
  replay_ai: nodes['replayAi'].innerHTML,
  replay_foot: nodes['replayFoot'].innerHTML,
  corpus_count: nodes['corpusCount'].textContent,
  corpus_items: (nodes['corpusList'].innerHTML.match(/class="corpus-item"/g)||[]).length,
  cases: cases,
  gates: gates,
  trap_cases: trap_cases,
  scope_cases: scope_cases,
  anchor_cases: anchor_cases,
  anchor_rendered: (anchor_html.match(/Matched on:/g) || []).length,
  near_cases: near_cases,
  qty_cases: qty_cases,
  relation_cases: relation_cases,
  stance_cases: stance_cases,
  guard_cases: guard_cases,
  chain_cases: chain_cases,
  snapshot_cases: snapshot_cases,
  snapshot_rendered: (snap_html.match(/Archived snapshot verified/g) || []).length,
  snapshot_quote_rendered: (snap_html.match(/snap-quote/g) || []).length,
  corpus_snap_badges: corpus_snap_badges,
  page_snap_counts: page_snap_counts,
  control_verdicts: control_verdicts,
  outcome_cases: outcome_cases,
  scope_plan_cases: sp_cases,
  batch_cases: batch_mapped,
  batch_rendered: batch_rendered,
  citation_cases: citation_cases,
  citation_rendered: citation_rendered
}));
`);
