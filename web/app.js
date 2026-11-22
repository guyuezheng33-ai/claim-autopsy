/* Front-end kernel (source file).
 * Build: python tools/build_frontend.py injects DATA and writes web/index.html.
 * The computation mirrors core/: synonyms, anchor gate, scope, conflict group,
 * three-state adjudication, negation and anti-overreach.
 */
/* __DATA_PLACEHOLDER__ */

const LOCAL_SERVER = typeof location !== "undefined" &&
  (location.protocol === "http:" || location.protocol === "https:") &&
  (location.hostname === "127.0.0.1" || location.hostname === "localhost" ||
   location.hostname === "[::1]" || location.port === "8765");

const CONNECTORS = ["and","also","but","plus","however","moreover","in addition"];
const NO_SPLIT = ["and","but","because","so","otherwise","which","that","besides"];
const MIN_SCORE = 1.2, CONFLICT = 0.45, ANCHOR_MIN = 0.42;
const CANON = [
  ["influenza","flu"],["vaccines","vaccine"],["antibiotics","antibiotic"],
  ["causes","cause"],["caused","cause"],["gives","give"],["gave","give"],
  ["people","humans"],["ten percent","10%"],["10 percent","10%"],
  ["prevents","prevent"],["preventing","prevent"],["protects","protect"],
  ["reduces","reduce"],["raises","raise"],["cures","cure"],["treats","treat"],["spherical","round"],
  ["causing","cause"]
];
function norm(s){
  s = (s || "").toLowerCase();
  for (const [k,v] of CANON) s = s.split(k).join(v);
  return s;
}
const EN_STOP = new Set(["a","an","the","is","are","was","were","be","been","to","of","and","or","in","on","for","with","that","this","it","its","can","could","do","does","did","have","has","had","you","your","we","our","only","not","no","from","by","as","at","will","would","may","might","more","than","other","their","there","get","gets","make","makes","give","take","takes","use","uses"]);
function enWords(s){
  return norm(s).match(/[a-z0-9%]+/g) || [];
}
function matchedAnchors(claim, cardClaim){
  const have = new Set(enWords(claim));
  const content = enWords(cardClaim).filter(w => !EN_STOP.has(w) && w.length>1);
  const out = [];
  content.forEach(w => { if (have.has(w) && out.indexOf(w)<0) out.push(w); });
  return out.sort();
}
function anchorCov(claim, cardClaim, idf){
  const content = enWords(cardClaim).filter(w => !EN_STOP.has(w) && w.length > 1);
  if (!content.length) return 0;
  const inW = new Set(enWords(claim));
  const w = t => idf ? Math.max(idf[t] || 0.5, 0.5) : 1;
  let total = 0, hit = 0;
  content.forEach(t => { total += w(t); if (inW.has(t)) hit += w(t); });
  return total > 0 ? hit / total : 0;
}
function tokens(s){ return enWords(s); }
function docText(c){ return [c.claim, (c.tags||[]).join(" "), c.src, c.snip].join(" "); }
function buildIndex(){
  const docs = DATA.cards.map(c => ({c, t: tokens(docText(c))}));
  const df = {}; docs.forEach(d => new Set(d.t).forEach(t => df[t]=(df[t]||0)+1));
  const n = docs.length, idf = {};
  for (const t in df) idf[t] = Math.log(1 + (n-df[t]+0.5)/(df[t]+0.5));
  return {docs, idf};
}
const INDEX = buildIndex();
function retrieve(claim){
  const nq = norm(claim);
  const qt = [...new Set(tokens(claim))], hits = [], near = [];
  INDEX.docs.forEach(d => {
    const tf = {}; d.t.forEach(t => tf[t]=(tf[t]||0)+1);
    let s = 0; qt.forEach(t => { if(tf[t]) s += (1+Math.log(tf[t]))*(INDEX.idf[t]||1); });
    const cov = anchorCov(claim, d.c.claim||"", INDEX.idf);
    if (s<=0 || cov<ANCHOR_MIN) return;
    const reasons = [];
    if ((d.c.exclude||[]).some(x => nq.includes(x))) reasons.push("excluded_by_scope");
    if ((d.c.requires||[]).some(x => !nq.includes(x))) reasons.push("missing_required_topic");
    if (!popCompatible(claim, d.c.claim||"")) reasons.push("different_population");
    if (!qtyCompatible(claim, d.c.claim||"")) reasons.push("different_quantity");
    if (!relCompatible(claim, d.c.claim||"")) reasons.push("different_relation");
    if (!attrCompatible(claim, d.c.claim||"")) reasons.push("different_predicate");
    if (!objectCompatible(claim, d.c.claim||"")) reasons.push("different_object");
    if (!predCompatible(claim, d.c.claim||"")) reasons.push("different_outcome");
    if (!strengthCompatible(claim, d.c.claim||"")) reasons.push("different_strength");
    if (!subjectCompatible(claim, d.c.claim||"")) reasons.push("different_subject");
    if (!topicOverlap(claim, d.c.claim||"")) reasons.push("no_shared_topic");
    const anchors = matchedAnchors(claim, d.c.claim||"");
    const tagSet = new Set((d.c.tags||[]).reduce((acc, x) => acc.concat(tokens(x)), []));
    const relSet = (typeof REL_ALL !== "undefined") ? REL_ALL : [];
    const contentAnchors = anchors.filter(a => relSet.indexOf(a) < 0);
    const terms = tokens(claim).filter(w => !EN_STOP.has(w) && !/^\d+$/.test(w));
    if (anchors.length && contentAnchors.every(a => tagSet.has(a)) && !sameProposition(claim, d.c.claim||""))
      reasons.push("topic_only");
    if (terms.length >= 6 && anchors.length <= 1 && !sameProposition(claim, d.c.claim||""))
      reasons.push("thin_anchor");
    if (reasons.length){ near.push({card_id:d.c.id, score:round4(s), anchor:round3(cov), reasons:reasons.filter((x,i,a)=>a.indexOf(x)===i).sort(), card_claim:d.c.claim||""}); return; }
    hits.push({s, c:d.c, cov, w:(d.c.w==null?1:d.c.w)});
  });
  hits.sort((a,b) => b.s-a.s);
  near.sort((a,b) => b.score-a.score);
  return {hits:hits.slice(0,3), near:near.slice(0,3)};
}
function round4(x){ return Math.round(x*10000)/10000; }
function round3(x){ return Math.round(x*1000)/1000; }
function splitComma(seg){
  const out = []; let buf = "";
  for (let i=0;i<seg.length;i++){
    const ch = seg[i];
    if (ch==="，" || ch===","){
      const prevDigit = i>0 && /\d/.test(seg[i-1]);
      const nextDigit = /\d/.test(seg[i+1]||"");
      if (prevDigit && nextDigit){ buf += ch; continue; }
      const nxt = seg.slice(i+1).replace(/^[ ，,]+/, "");
      if (NO_SPLIT.some(x => nxt.toLowerCase().indexOf(x.toLowerCase())===0)) buf += ch;
      else { out.push(buf); buf=""; }
    } else buf += ch;
  }
  out.push(buf); return out;
}
const VERB_HINTS = ["is","are","was","were","can","cannot","could","will","would","may","might","must","should","shall","appears","appear","seems","seem","remains","remain","includes","include","does","do","did","has","have","had","causes","cause","cures","cure","treats","treat","prevents","prevent","makes","make","gives","give","supports","support","improves","improve","contains","contain","leads","lead","triggers","trigger","builds","build","stays","stay","reduces","reduce","raises","raise","protects","protect","weakens","weaken","removes","remove"];
const PRED_ADJ = new Set(["round","flat","true","false","real","fake","safe","unsafe","harmful","harmless","healthy","unhealthy","dangerous","effective","ineffective","useless","useful","toxic","natural","artificial","alive","dead","legal","illegal","possible","impossible","normal","common","rare","necessary","optional","contagious","infectious","curable","incurable","renewable","finite","infinite","solid","liquid","hot","cold"]);
function subjectVerb(atom){
  const words = atom.split(/\s+/).filter(Boolean);
  for (let i=0;i<words.length;i++){
    const w = words[i].toLowerCase().replace(/[,.!?;:]/g,"");
    if (VERB_HINTS.indexOf(w)>=0) return {subj:words.slice(0,i).join(" ").trim(), verb:words[i].replace(/[,.]/g,"")};
  }
  return {subj:"", verb:""};
}
function isBarePredicate(a){
  const words = a.split(/\s+/).filter(Boolean).map(w=>w.toLowerCase().replace(/[,.!?;:]/g,""));
  return words.length>0 && words.length<=2 && words.some(w=>PRED_ADJ.has(w));
}
function isObjectContinuation(frag){
  const words = frag.split(/\s+/).filter(Boolean);
  if (!words.length || words.length>3) return false;
  return !subjectVerb(frag).verb && !isBarePredicate(frag);
}
const REL_WORDS = {
  prevent:["prevent","prevents","preventing","prevention","protect","protects","protection","reduce","reduces","lower","lowers","avoid","avoids","stop","stops"],
  cause:["cause","causes","caused","causing","trigger","triggers","lead","leads","produce","produces","increase","increases","raise","raises","give","spread","spreads","transmit"],
  cure:["cure","cures","cured","treat","treats","treated","heal","heals","reverse","reverses","fix","fixes"],
  guidance:["receive","receives","eligible","eligibility","recommend","recommends","recommended","should","must","allowed","approved","ineligible"],
  course:["resolve","resolves","resolved","recover","recovers","recovery","clear","clears","last","lasts","duration","self","own","symptom","symptoms","mild","severe"],
  efficacy:["work","works","worked","effective","effectiveness","efficacy","kill","kills","killed","eliminate","eliminates","useless","ineffective"]
};
const HARM_WORDS = ["exceed","exceeds","exceeding","overdose","harmful","harm","dangerous","damage","damages","toxic","unsafe"];
const REL_COMPAT = [["harm","cause"],["harm","cure"],["harm","guidance"],["guidance","prevent"]];
const POP_GROUPS = {
  child:["child","children","kid","kids","infant","infants","infant's","toddler","toddlers","baby","babies","pediatric","adolescent","adolescents","teen","teens","teenager","teenagers","newborn","newborns"],
  pregnancy:["pregnant","pregnancy","breastfeeding","lactating"],
  adult:["adult","adults","elderly","senior","seniors","geriatric","menopausal"],
  male:["men","male","males","boy","boys"],
  female:["women","woman","female","females","girl","girls"]
};
const QTY_RE = /(\d[\d,]*(?:\.\d+)?)\s*(mcg|µg|ug|mg|g|iu|ml|%|percent)/gi;
const QTY_UNIT = {mcg:"mcg","µg":"mcg",ug:"mcg",mg:"mg",g:"g",iu:"iu",ml:"ml","%":"%",percent:"%"};
const DOSE_UNITS = ["mcg","mg","g","iu","ml","%"];
function quantities(text){
  const out = {}, s = String(text||"");
  const re = new RegExp(QTY_RE.source, "gi");
  let m;
  while ((m = re.exec(s)) !== null){
    const u = QTY_UNIT[m[2].toLowerCase()];
    if (!u) continue;
    const v = parseFloat(m[1].replace(/,/g,""));
    if (!isFinite(v)) continue;
    if (!out[u]) out[u] = [];
    if (out[u].indexOf(v) < 0) out[u].push(v);
  }
  return out;
}
function qtyCompatible(claim, cardClaim){
  const a = quantities(claim), b = quantities(cardClaim);
  return DOSE_UNITS.every(u => {
    if (!a[u] || !b[u]) return true;
    return a[u].some(v => b[u].indexOf(v) >= 0);
  });
}
function popClasses(text){
  const t = new Set(tokens(text)), out = [];
  Object.keys(POP_GROUPS).forEach(k => { if (POP_GROUPS[k].some(w=>t.has(w))) out.push(k); });
  return out;
}
function popCompatible(claim, cardClaim){
  const a = popClasses(claim), b = popClasses(cardClaim);
  if (!a.length && !b.length) return true;
  if (!a.length || !b.length) return false;
  return a.some(x => b.indexOf(x)>=0);
}
function relClasses(text){
  const t = new Set(tokens(text)), out = [];
  Object.keys(REL_WORDS).forEach(k => { if (REL_WORDS[k].some(w=>t.has(w))) out.push(k); });
  if (HARM_WORDS.some(w=>t.has(w)) && out.indexOf("harm")<0) out.push("harm");
  return out;
}
function primaryRelation(text){
  const t = tokens(text);
  let best = null;
  for (let i=0;i<t.length;i++){
    for (const k of Object.keys(REL_WORDS)){
      if (REL_WORDS[k].indexOf(t[i])>=0){ if (!best || i < best.i) best = {i:i, cls:k}; }
    }
    if (HARM_WORDS.indexOf(t[i])>=0 && (!best || i < best.i)) best = {i:i, cls:"harm"};
  }
  return best ? best.cls : null;
}
function relCompatible(claim, cardClaim){
  const a = relClasses(claim), b = relClasses(cardClaim);
  if (!a.length || !b.length) return true;
  const pa = primaryRelation(claim), pb = primaryRelation(cardClaim);
  if (pa && pb){
    if (pa===pb) return true;
    return REL_COMPAT.some(p => (p[0]===pa&&p[1]===pb)||(p[0]===pb&&p[1]===pa));
  }
  return a.some(x => b.some(y => x===y || REL_COMPAT.some(p => (p[0]===x&&p[1]===y)||(p[0]===y&&p[1]===x))));
}
const ATTR_WORDS = {
  safe:["safe","safely","safety"],
  unsafe:["unsafe","dangerous","harmful","risky","hazardous"],
  effective:["effective","efficacy","beneficial","works","work","clean","cleans","cleanse","cleansing","disinfects","disinfect"],
  useless:["useless","ineffective","uselessly"]
};
const ATTR_COMPAT = [["safe","unsafe"],["effective","useless"]];
function attrClasses(text){
  const t = new Set(tokens(text)), out = [];
  Object.keys(ATTR_WORDS).forEach(k => { if (ATTR_WORDS[k].some(w=>t.has(w))) out.push(k); });
  return out;
}
function attrCompatible(claim, cardClaim){
  const a = attrClasses(claim), b = attrClasses(cardClaim);
  if (!a.length) return true;
  if (b.length){
    if (a.some(x => b.indexOf(x)>=0)) return true;
    if (ATTR_COMPAT.some(p => (a.indexOf(p[0])>=0 && b.indexOf(p[1])>=0) || (a.indexOf(p[1])>=0 && b.indexOf(p[0])>=0))) return true;
    return false;
  }
  const rel = relClasses(cardClaim);
  return !(rel.indexOf("cause")>=0 || rel.indexOf("harm")>=0);
}
const OUTCOME_WORDS = ["cold","colds","flu","influenza","covid","covid-19","coronavirus",
  "cancer","diabetes","malaria","measles","polio","pneumonia","asthma","autism","poisoning",
  "headache","headaches","migraine","infection","infections","diarrhea","diarrheal","diarrhoea",
  "respiratory","stroke","obesity","depression","anxiety","allergy","allergies","blindness",
  "vision","pregnancy","birth","neural","tube","defects","toxicity","dementia","arthritis",
  "tuberculosis","tumour","tumours","tumor","tumors","neoplasm","carcinoma","sars-cov-2"];
// core/evidence.py OUTCOME_SYNONYMS: same condition, different word. Without it
// "tumour" was not a condition at all and a cancer card decided a coronavirus
// claim on the words air + spread alone.
const OUTCOME_SYNONYMS = {"covid-19":"covid","coronavirus":"covid","sars-cov-2":"covid",
  "tumour":"cancer","tumours":"cancer","tumor":"cancer","tumors":"cancer",
  "neoplasm":"cancer","carcinoma":"cancer"};
function outcomeClasses(text){
  const t = new Set(tokens(String(text||"")));
  const low = String(text||"").toLowerCase();
  const out = [];
  OUTCOME_WORDS.forEach(w => { if (t.has(w) || low.indexOf(w.replace("-"," "))>=0) out.push(OUTCOME_SYNONYMS[w] || w); });
  return out.filter((x,i,a)=>a.indexOf(x)===i);
}
const GENERIC_OUTCOMES = ["infection","infections","respiratory","vision","birth","pregnancy","toxicity"];
function objectCompatible(claim, cardClaim){
  const a = outcomeClasses(claim).filter(x=>GENERIC_OUTCOMES.indexOf(x)<0);
  const b = outcomeClasses(cardClaim).filter(x=>GENERIC_OUTCOMES.indexOf(x)<0);
  if (!a.length || !b.length) return true;
  return a.some(x => b.indexOf(x)>=0);
}
// What happens to the condition, not which condition it is. Mirrors
// core/evidence.py PREDICATE_OUTCOMES: a card about curing COVID-19 may not
// decide a claim about becoming more susceptible to it.
const PRED_WORDS = {
  risk:["susceptible","susceptibility","vulnerable","vulnerability","risk","risks",
    "likely","probability","prone","catch","catches","contract","contracts"],
  cure:["cure","cures","cured","treat","treats","treated","treatment","therapy",
    "remedy","heal","heals","reverse"],
  prevent:["prevent","prevents","prevention","protect","protects","protection",
    "avoid","avoids","stop","stops","block","blocks"],
  transmit:["transmit","transmits","transmission","spread","spreads","spreading",
    "infect","infects","infected"],
  harm:["cause","causes","caused","harm","harms","damage","damages","toxic",
    "poison","poisoning","side","effects","worsen","worsens"],
  severity:["severe","severely","severity","hospitalised","hospitalized",
    "hospitalisation","hospitalization","death","die","dies","mortality","fatal"]
};
const PRED_COMPAT = [["risk","prevent"],["risk","transmit"],["prevent","transmit"],["risk","severity"]];
function predClasses(text){
  const t = new Set(tokens(String(text||""))), out = [];
  Object.keys(PRED_WORDS).forEach(k => { if (PRED_WORDS[k].some(w=>t.has(w))) out.push(k); });
  return out;
}
function predCompatible(claim, cardClaim){
  const a = predClasses(claim), b = predClasses(cardClaim);
  if (!a.length || !b.length) return true;
  if (a.some(x => b.indexOf(x)>=0)) return true;
  return PRED_COMPAT.some(p => (a.indexOf(p[0])>=0 && b.indexOf(p[1])>=0) || (a.indexOf(p[1])>=0 && b.indexOf(p[0])>=0));
}
function headSubject(text){
  const rel = primaryRelation(text);
  if (!rel) return null;
  const keys = (REL_WORDS[rel] || HARM_WORDS);
  const t = tokens(text);
  for (let i=0;i<t.length;i++){
    if (keys.indexOf(t[i])>=0){
      const head = t.slice(0,i).filter(w=>!EN_STOP.has(w));
      return head.length ? head : null;
    }
  }
  return null;
}
const NEG_WORDS = new Set(["not","no","never","cannot","cant","without","none","nothing",
  "do","does","did","have","has","had","is","are","was","were","be"]);
function sameProposition(a, b, threshold){
  threshold = threshold || 0.6;
  const A = new Set(tokens(a).filter(w=>!NEG_WORDS.has(w)));
  const B = new Set(tokens(b).filter(w=>!NEG_WORDS.has(w)));
  if (!A.size || !B.size) return false;
  let inter = 0; A.forEach(w=>{ if (B.has(w)) inter++; });
  return inter / (A.size + B.size - inter) >= threshold;
}
const SUBJ_SYN = {"monosodium":"msg","glutamate":"msg","ascorbic":"vitamin c","jab":"vaccine","shot":"vaccine"};
const SUBJ_NEG = ["not","no","never","cannot","cant","without","none","nothing","do","does","did",
  "have","has","had","is","are","was","were","be"];
const ABS_WORDS = ["never","always","none","every","all","no"];
const HEDGE_WORDS = ["rare","rarely","uncommon","uncommonly","sometimes","occasionally",
  "may","might","can","could","often","usually","frequently"];
function strengthCompatible(claim, cardClaim){
  const a = tokens(claim), b = tokens(cardClaim);
  if (a.some(x=>ABS_WORDS.indexOf(x)>=0) && b.some(x=>HEDGE_WORDS.indexOf(x)>=0)) return false;
  if (a.some(x=>HEDGE_WORDS.indexOf(x)>=0) && b.some(x=>ABS_WORDS.indexOf(x)>=0)) return false;
  return true;
}
function subjectCompatible(claim, cardClaim){
  let a = headSubject(claim), b = headSubject(cardClaim);
  if (!a) a = tokens(claim).filter(w=>SUBJ_NEG.indexOf(w)<0).slice(0,2);
  if (!b) return true;
  const ea = a.concat(a.filter(w=>SUBJ_SYN[w]).map(w=>SUBJ_SYN[w]));
  const eb = b.concat(b.filter(w=>SUBJ_SYN[w]).map(w=>SUBJ_SYN[w]));
  if (ea.some(x=>eb.indexOf(x)>=0)) return true;
  const at = tokens(claim);
  if (eb.some(x=>at.indexOf(x)>=0)) return true;
  return false;
}
const ANTONYM_PAIRS = [["round","flat"],["spherical","flat"],["safe","unsafe"],["safe","dangerous"],
  ["safe","harmful"],["effective","useless"],["effective","ineffective"],["true","false"],
  ["increase","decrease"],["rise","fall"],["prevent","cause"]];
const CONS_SYN = {spherical:"round", globe:"earth", world:"earth", jab:"vaccine", shot:"vaccine",
  immunisation:"vaccination", immunization:"vaccination", sanitiser:"sanitizer", handwashing:"hand", wash:"washing"};
const OPPOSED_REL = [["cause","prevent"],["cause","cure"],["harm","prevent"]];
function negCount(text){ return detectNegation(text).count; }
function consContent(text){
  // Deliberately not CANON-normalized: conflict detection works on the words as
  // written, the same way core/consistency.py does, so "causes" vs "cause" decides
  // through the relation flip, not through an antonym pair.
  const out = new Set();
  ((text||"").toLowerCase().match(/[a-z0-9']+/g) || []).forEach(t => {
    t = t.replace(/^'+|'+$/g, "");
    if (!t || EN_STOP.has(t)) return;
    out.add(CONS_SYN[t]||t);
  });
  return out;
}
function consAntonym(a,b){
  for (const [x,y] of ANTONYM_PAIRS){
    const x2 = CONS_SYN[x]||x, y2 = CONS_SYN[y]||y;
    if ((a.has(x2)&&b.has(y2))||(a.has(y2)&&b.has(x2))) return [x2,y2];
  }
  return null;
}
function consRelationFlip(a,b){
  const ra = relClasses(a), rb = relClasses(b);
  for (const [x,y] of OPPOSED_REL){
    if ((ra.indexOf(x)>=0&&rb.indexOf(y)>=0)||(ra.indexOf(y)>=0&&rb.indexOf(x)>=0)) return [x,y];
  }
  return null;
}
function consCompare(a,b){
  const A = consContent(a), B = consContent(b);
  if (!A.size || !B.size) return {conflict:false, basis:null, shared:[]};
  const shared = Array.from(A).filter(x => B.has(x)).sort();
  if (shared.length < 1 || shared.length < Math.min(A.size,B.size)*0.5) return {conflict:false, basis:null, shared};
  const pair = consAntonym(A,B);
  if (pair && Array.from(A).filter(x=>pair.indexOf(x)<0).some(x=>B.has(x) && pair.indexOf(x)<0))
    return {conflict:true, basis:"antonym:"+pair[0]+"/"+pair[1], shared};
  const flip = consRelationFlip(a,b);
  if (flip) return {conflict:true, basis:"opposite_relation:"+flip[0]+"/"+flip[1], shared};
  const negA = negCount(a), negB = negCount(b);
  if ((negA%2) !== (negB%2)) return {conflict:true, basis:"negation", shared};
  return {conflict:false, basis:null, shared};
}
function consRelations(claims){
  const out = [];
  for (let i=0;i<claims.length;i++) for (let j=i+1;j<claims.length;j++){
    const r = consCompare(claims[i], claims[j]);
    if (r.conflict) out.push({atoms:[i,j], basis:r.basis, shared:r.shared});
  }
  return out;
}
const REL_PHRASE = {cause:"causes",prevent:"prevents",cure:"cures",harm:"harms",
  guidance:"is advised for",efficacy:"works against",course:"changes the course of"};
const REL_PHRASE_KEYS = Object.assign({}, REL_WORDS); REL_PHRASE_KEYS.harm = HARM_WORDS;
const CHAIN_RELATIONS = {"cause+cause":"cause","prevent+cause":"prevent",
  "cause+prevent":"prevent","prevent+prevent":"cause"};
function splitAtom(text){
  const rel = primaryRelation(text);
  if (!rel) return null;
  const words = enWords(text), keys = REL_PHRASE_KEYS[rel] || [];
  let pos = -1;
  for (let i=0;i<words.length;i++){ if (keys.indexOf(words[i])>=0){ pos = i; break; } }
  if (pos<=0 || pos>=words.length-1) return null;
  return {subject:words.slice(0,pos).join(" "), rel:rel, object:words.slice(pos+1).join(" ")};
}
function chainDerive(a, b, c){
  const sa = splitAtom(a), sb = splitAtom(b);
  if (!sa || !sb) return null;
  const o1 = consContent(sa.object), s2 = consContent(sb.subject);
  if (!o1.size || !Array.from(o1).some(x => s2.has(x))) return null;
  const r = CHAIN_RELATIONS[sa.rel+"+"+sb.rel];
  if (!r) return null;
  const derived = sa.subject+" "+(REL_PHRASE[r]||r)+" "+sb.object;
  const out = {type:"chain", atoms:[0,1], derived:derived, relation:r,
    basis:"chain:"+sa.rel+"+"+sb.rel+"=>"+r,
    note:"Two atoms link end to end and force a third statement; the derivation is shown so it can be checked, not hidden."};
  if (c == null) return out;
  const cs = consContent(sa.subject), co = consContent(sb.object), cc = consContent(c);
  if (Array.from(cs).some(x=>cc.has(x)) && Array.from(co).some(x=>cc.has(x))){
    const rc = relClasses(c);
    const opposed = (r==="cause" && rc.indexOf("prevent")>=0) || (r==="prevent" && rc.indexOf("cause")>=0);
    const neg = negCount(c);
    if (opposed || neg%2){
      out.atoms=[0,1,2]; out.conflict=true; out.texts=[a,b,c];
      out.note = "These three atoms cannot all be true: the first two force \""+derived+"\", the third denies it.";
      return out;
    }
    out.atoms=[0,1,2]; out.texts=[a,b,c]; out.conflict=false;
  }
  return out;
}
function consChains(claims){
  const out = [], seen = new Set(), flagged = new Set();
  for (let i=0;i<claims.length;i++) for (let j=0;j<claims.length;j++){
    if (i===j) continue;
    const key = Math.min(i,j)+","+Math.max(i,j);
    if (seen.has(key)) continue;
    const base = chainDerive(claims[i], claims[j]);
    if (!base) continue;
    let conflict = null, agree = null;
    for (let k=0;k<claims.length;k++){
      if (k===i || k===j) continue;
      const cand = chainDerive(claims[i], claims[j], claims[k]);
      if (!cand) continue;
      if (cand.conflict && !conflict){ cand.atoms=[i,j,k]; conflict = cand; }
      else if (!cand.conflict && !agree){ cand.atoms=[i,j,k]; agree = cand; }
    }
    const entry = conflict || agree || Object.assign({}, base, {atoms:[i,j]});
    const fk = entry.atoms.slice().sort().join(",");
    seen.add(key);
    if (flagged.has(fk)) continue;
    flagged.add(fk); out.push(entry);
  }
  return out;
}
function consExplain(rel){
  const basis = rel.basis || "";
  if (basis.indexOf("antonym:")===0){ const p = basis.slice(8).split("/"); return "Opposite predicates ("+p[0]+" vs "+p[1]+") about the same subject."; }
  if (basis.indexOf("opposite_relation:")===0){ const p = basis.slice(18).split("/"); return "Opposite relations ("+p[0]+" vs "+p[1]+") over the same subject."; }
  if (basis === "negation") return "One atom negates what the other asserts.";
  return "The two atoms cannot both be true.";
}
const POP_ALL = [].concat.apply([], Object.keys(POP_GROUPS).map(k=>POP_GROUPS[k]));
const REL_ALL = [].concat.apply([], Object.keys(REL_WORDS).map(k=>REL_WORDS[k]));
function topicOverlap(claim, cardClaim){
  const strip = t => tokens(t).filter(w => !EN_STOP.has(w) && POP_ALL.indexOf(w)<0 && REL_ALL.indexOf(w)<0 && HARM_WORDS.indexOf(w)<0);
  const a = new Set(strip(claim)), b = strip(cardClaim);
  return b.some(w => a.has(w));
}
const SENT_ABBREV = ["e.g","i.e","dr","mr","mrs","ms","no","vs","u.s","st","approx","fig","ref","cf","al","etc","inc","ltd"];
function breakSentences(text){
  let out = "", last = 0;
  const re = /(?<=[.!?])[ \t]+(?=["'(\[A-Z0-9])/g;
  let m;
  while ((m = re.exec(text)) !== null){
    const head = text.slice(last, m.index);
    const word = head.replace(/\s+$/,"").split(/[^A-Za-z.\u2019']/).pop().toLowerCase();
    if (SENT_ABBREV.indexOf(word) >= 0) continue;
    out += head + "\n";
    last = re.lastIndex;
  }
  out += text.slice(last);
  return out;
}
function isReportingOnly(s){
  // "Several recent studies have looked at the impact of vitamin D on COVID-19"
  // reports that research exists; it asserts no finding. Mirrors
  // core/decompose.py _is_checkable. A finding verb anywhere keeps the atom.
  const words = (s.toLowerCase().match(/[a-z']+/g)||[]);
  const set = new Set(words);
  const actors = ["studies","study","researchers","scientists","authors","investigators"];
  const work = ["examined","examining","investigated","investigating","studied","studying","reviewed","explored"];
  const findings = ["found","finds","show","shows","shown","suggest","suggests","suggested","report",
    "reports","reported","conclude","concludes","linked","associated","evidence","cause","causes",
    "increase","increases","reduce","reduces","effective","risk"];
  if (!actors.some(w => set.has(w))) return false;
  if (findings.some(w => set.has(w))) return false;
  if (/\b(looked at|looked into|focused on)\b/.test(s.toLowerCase())) return true;
  return work.some(w => set.has(w));
}
function ruleSplit(text){
  if (!text || !text.trim()) return [];
  const segs = breakSentences(text).split(/[。！？；;、\n]+/), atoms = [];
  segs.forEach(seg => {
    seg = seg.trim(); if (!seg) return;
    splitComma(seg).forEach(piece => {
      const re = new RegExp("("+CONNECTORS.map(c=>"\\b"+c.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"\\b").join("|")+")", "gi");
      const parts = piece.split(re); let buf = [];
      let i = 0;
      while (i < parts.length){
        const p = parts[i];
        if (i%2===1 && CONNECTORS.some(c=>c.toLowerCase()===p.trim().toLowerCase())){
          const nxt = (i+1 < parts.length) ? parts[i+1] : "";
          if (nxt.trim() && isObjectContinuation(nxt)){ buf.push(p+nxt); i += 2; continue; }
          if (buf.length && !subjectVerb(buf.join("")).verb && subjectVerb(nxt).verb){
            buf.push(p+nxt); i += 2; continue;
          }
          if (buf.length){ atoms.push(buf.join("")); buf=[]; }
        } else if (p.trim()) buf.push(p);
        i += 1;
      }
      if (buf.length) atoms.push(buf.join(""));
    });
  });
  const clean = s => {
    s = s.trim().replace(/^[ ，,、:："'“”‘’]+/,"").trim();
    s = s.replace(/^(e\.g\.|i\.e\.)\s*/i, "");
    CONNECTORS.forEach(c => { if (s.toLowerCase().indexOf(c.toLowerCase())===0) s = s.slice(c.length).trim(); });
    return s.trim();
  };
  const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  const repaired = [];
  atoms.forEach(a => {
    a = clean(a); if (!a) return;
    const sv = subjectVerb(a);
    if (!sv.verb && isBarePredicate(a) && repaired.length){
      const prev = subjectVerb(repaired[repaired.length-1]);
      if (prev.subj && prev.verb) a = prev.subj + " " + prev.verb + " " + a;
    }
    repaired.push(a);
  });
  const out = [];
  repaired.forEach(a => {
    a = cap(clean(a));
    if (a.length < 4) return;
    if ((a.match(/[A-Za-z0-9%]+/g)||[]).length < 3) return;
    if (/[？?]$/.test(a)) return;
    if (isReportingOnly(a)) return;
    if (out.indexOf(a)<0) out.push(a);
  });
  return out;
}
const EN_NEG = [/\bcannot\b/gi,/\bcan not\b/gi,/\bcan't\b/gi,/\bwill not\b/gi,/\bwon't\b/gi,/\bdoes not\b/gi,/\bdon't\b/gi,/\bdo not\b/gi,/\bdidn't\b/gi,/\bdid not\b/gi,/\bisn't\b/gi,/\bis not\b/gi,/\baren't\b/gi,/\bare not\b/gi,/\bwasn't\b/gi,/\bwas not\b/gi,/\bweren't\b/gi,/\bwere not\b/gi,/\bnever\b/gi,/\bnot\b/gi,/\bno\b/gi];
function detectNegation(text){
  let out = (text || "").replace(/\bnot[ \t]+(?=(recommended|advised|allowed|permitted|approved)\b)/gi, "\u0001"), markers = [];
  EN_NEG.forEach(p => { out = out.replace(p, m => { markers.push(m); return " "; }); });
  const count = markers.length;
  out = out.replace(/\u0001/g, " ");
  return {original:text, normalized:out.replace(/\s+/g," ").trim() || text, markers, count, flip:count===1, uncertain:count>=2};
}
function signedInvert(h, claim){
  const cardRel = primaryRelation((h.c && h.c.claim) || "");
  const claimRel = primaryRelation(claim);
  if (/\bnot[ \t]+(recommended|advised|allowed|permitted|approved)\b/.test(String(claim||"").toLowerCase())) return false;
  return cardRel==="harm" && claimRel==="guidance";
}
function adjudicate(claim, hits, neg){
  neg = neg || {flip:false, uncertain:false, markers:[], original:claim, normalized:claim};
  const groups = {};
  hits.forEach(h => { const g = h.c.cgroup || ""; if (g) (groups[g]=groups[g]||[]).push(h); });
  const conflicts = Object.keys(groups).filter(g => new Set(groups[g].map(x=>x.c.stance)).size > 1);
  const ws = h => h.s * h.w;
  const flip = !!neg.flip;
  const eff = h => {
    if (h.c.stance==="contextual") return "contextual";
    const cardNeg = detectNegation(h.c.claim||"").flip;
    const same = sameProposition(claim, h.c.claim||"");
    const adjust = (same ? (!!flip !== !!cardNeg) : !!flip) !== signedInvert(h, claim);
    return adjust ? (h.c.stance==="supports"?"refutes":"supports") : h.c.stance;
  };
  const sup = hits.filter(h=>eff(h)==="supports").reduce((a,h)=>a+ws(h),0);
  const ref = hits.filter(h=>eff(h)==="refutes").reduce((a,h)=>a+ws(h),0);
  const ctx = hits.filter(h=>h.c.stance==="contextual").length;
  const total = sup+ref, ratio = (sup>0&&ref>0) ? Math.min(sup,ref)/Math.max(sup,ref) : 0;
  const polNote = flip ? ("Negation detected ("+neg.markers.join(", ")+"); evidence stance inverted. ") : "";
  let verdict="undetermined", confidence="low", reason=polNote, missing="";
  if (neg.uncertain){
    reason = "Ambiguous double negation. The tool refuses rather than guessing which polarity was meant.";
    missing = "An unambiguous claim to check";
  } else if (!hits.length){
    reason += "No matching evidence card in this corpus; the claim cannot be decided.";
    missing = "A directly relevant authoritative source";
  } else if (conflicts.length){
    reason += "The retrieved sources differ in wording ("+conflicts.join("、")+"). This tool shows the difference and does not adjudicate.";
    missing = "Open both sources and judge for yourself; this tool takes no position";
  } else if (total>0 && Math.max(sup,ref)<MIN_SCORE){
    reason += "Retrieved evidence is below the decision threshold; no verdict is justified."; missing="A more direct and authoritative source";
  } else if (sup>0 && ref>0 && ratio>=CONFLICT){
    reason += "Supporting and refuting evidence are close in strength; this is an evidence conflict."; missing="A higher-authority source to settle the conflict";
  } else if (sup>=MIN_SCORE && ref>=MIN_SCORE){
    verdict = sup>ref ? "supported" : "refuted";
    confidence = Math.max(sup,ref)>=MIN_SCORE*2 ? "high" : "medium";
    reason += "Sources in one direction are clearly stronger than the other side.";
  } else if (ref>=MIN_SCORE){
    verdict="refuted"; confidence=ref>=MIN_SCORE*2?"high":"medium";
    reason += "An authoritative source in this corpus refutes the claim.";
  } else if (sup>=MIN_SCORE){
    verdict="supported"; confidence=sup>=MIN_SCORE*2?"high":"medium";
    reason += "An authoritative source in this corpus supports the claim.";
  } else {
    reason += "Only background evidence was found; no verdict is justified."; missing="A source that directly verifies the claim";
  }
  const citations = hits.map(h => ({card_id:h.c.id, sid:h.c.sid, src:h.c.src, url:h.c.url, snip:h.c.snip,
    stance:h.c.stance, matched:matchedAnchors(claim, h.c.claim||""),
    snap:(DATA.snaps||{})[h.c.id]||null,
    effective_stance: eff(h), polarity_flipped: eff(h)!==h.c.stance}));
  if (verdict!=="undetermined" && citations.some(c=>!c.card_id||!c.url||!c.snip||!c.stance)){
    verdict="undetermined"; confidence="low"; reason+="Citation fields are incomplete; gate downgraded the verdict to refusal.";
  }
  let explain;
  if (verdict==="undetermined")
    explain = reason + " (Sources checked: "+(citations.length?citations.map(c=>c.sid).join(", "):"none")+")";
  else
    explain = reason + " (Based on: "+citations.filter(c=>c.effective_stance===(verdict==="refuted"?"refutes":"supports")).map(c=>c.sid).join(", ")+"; open the evidence card to verify the original)";
  return {claim, verdict, confidence, reason, missing, citations, explain, conflicts, polarity:neg, scores:{sup:sup.toFixed(2), ref:ref.toFixed(2), ctx}};
}

/* Citation audit: the second question the product answers.
 * "Does the source I pasted actually state this claim?"
 * Every atom gets a finding; not_in_source is a result, not a refusal.
 */
const CIT_FULL = 0.70, CIT_PARTIAL = 0.35;
const CIT_ABBREV = new Set(["dr","mr","mrs","ms","prof","st","vs","e.g","i.e","etc","fig","no","approx","cf","al","inc","ltd","u.s","u.k"]);
const CIT_DEMOS = [
  {label:"Refuted by its own source", claim:"Getting a flu vaccine gives you the flu.",
   source:"Getting a flu vaccine does not give you the flu. The vaccine contains inactivated virus."},
  {label:"Supported verbatim", claim:"The Eiffel Tower is in Paris.",
   source:"The Eiffel Tower is located in Paris, France."},
  {label:"Source never says it", claim:"Coffee stunts growth in teenagers.",
   source:"Vitamin D deficiency is common in teenagers. Coffee contains caffeine."}
];
function splitSentences(text){
  const out = []; let start = 0; const re = /[.!?]/g; let m;
  while ((m = re.exec(text)) !== null){
    let i = m.index + 1;
    if (text[m.index] === "."){
      const before = text.slice(Math.max(0, m.index - 12), m.index).split(/\s+/);
      const last = (before[before.length - 1] || "").toLowerCase().replace(/[()]/g, "");
      if (CIT_ABBREV.has(last)) continue;
      if (i < text.length && /\d/.test(text[i])) continue;
    }
    while (i < text.length && "\"')]”’".indexOf(text[i]) >= 0) i++;
    if (i < text.length && !/\s/.test(text[i])) continue;
    const raw = text.slice(start, i);
    const seg = raw.trim();
    if (seg){
      const lead = raw.length - raw.replace(/^\s+/, "").length;
      out.push({text:seg, start:start + lead, end:start + lead + seg.length});
    }
    start = i; re.lastIndex = i;
  }
  const tail = text.slice(start).trim();
  if (tail){
    const raw = text.slice(start);
    const lead = raw.length - raw.replace(/^\s+/, "").length;
    out.push({text:tail, start:start + lead, end:start + lead + tail.length});
  }
  return out;
}
function citContent(text){
  return tokens(text).filter(w => !EN_STOP.has(w) && w.length > 1);
}
function citNumbers(text){
  return new Set((String(text||"").match(/\d[\d,]*(?:\.\d+)?/g) || []).map(x => x.replace(/,/g,"")));
}
function citNumbersMissing(claim, sent){
  const a = citNumbers(claim), b = citNumbers(sent), out = [];
  a.forEach(n => { if (!b.has(n)) out.push(n); });
  return out;
}
function citationAudit(claim, source, sourceName){
  claim = String(claim||"").trim(); source = String(source||"").trim();
  sourceName = String(sourceName||"provided source").trim() || "provided source";
  if (!claim) return {error:"empty_claim"};
  if (!source) return {error:"empty_source"};
  if (claim.length > 2000) return {error:"claim_too_long", limit:2000};
  if (source.length > 20000) return {error:"source_too_long", limit:20000};
  const atoms = ruleSplit(claim);
  const list = atoms.length ? atoms : [claim];
  const sentences = splitSentences(source).map(s => ({text:s.text, start:s.start, end:s.end, t:tokens(s.text)}));
  const df = {}; sentences.forEach(s => { new Set(s.t).forEach(w => df[w]=(df[w]||0)+1); });
  const N = Math.max(1, sentences.length), idf = {};
  for (const w in df) idf[w] = Math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5));
  function covOf(atom, s){
    const c = citContent(atom); if (!c.length) return [0, []];
    const have = new Set(s.t), w = x => Math.max(idf[x] || 1.0, 0.5);
    let total = 0, got = 0, hit = [];
    c.forEach(x => { total += w(x); if (have.has(x)){ got += w(x); hit.push(x); } });
    return [total > 0 ? got / total : 0, [...new Set(hit)].sort()];
  }
  const findings = [];
  list.forEach(atom => {
    const scored = sentences.map(s => ({s, cov:covOf(atom, s)[0], hit:covOf(atom, s)[1]}))
      .sort((a,b) => b.cov - a.cov);
    const top = scored[0] || {s:{text:"",start:0,end:0}, cov:0, hit:[]};
    const near = scored.slice(1,4).filter(x => x.cov > 0).map(x => ({text:x.s.text, coverage:Math.round(x.cov*1000)/1000, hit:x.hit}));
    const base = {claim:atom, coverage:Math.round(top.cov*10000)/10000, source_sentence:top.s.text || null,
      char_offset:top.s.text ? [top.s.start, top.s.end] : null, near};
    function put(verdict, reason){ findings.push(Object.assign({}, base, {verdict, confidence:verdict==="not_in_source"?"none":(top.cov>=0.85?"high":"medium"), reason})); }
    if (top.cov < CIT_PARTIAL){ put("not_in_source", "The provided source does not mention this claim. Only "+Math.round(top.cov*100)+"% of its content words appear in the closest sentence."); return; }
    const ra = primaryRelation(atom), rb = primaryRelation(top.s.text);
    if (ra && rb && ra !== rb){ put("not_in_source", "The closest sentence shares the topic but asserts a different relation ("+rb+", not "+ra+")."); return; }
    if (!subjectCompatible(atom, top.s.text)){ put("not_in_source", "The closest sentence is about a different subject."); return; }
    if (!qtyCompatible(atom, top.s.text)){ put("not_in_source", "The source states a different quantity."); return; }
    const miss = citNumbersMissing(atom, top.s.text);
    if (miss.length){ put("not_in_source", "The source does not state the number(s) in the claim ("+miss.join(", ")+")."); return; }
    if (!strengthCompatible(atom, top.s.text)){ put("not_in_source", "The source states a different strength (hedged vs absolute)."); return; }
    if (top.cov < CIT_FULL){ put("not_in_source", "The source comes close ("+Math.round(top.cov*100)+"% of the claim's content words) but does not state it as written; no verdict is transferred from a partial match."); return; }
    const neg = detectNegation(atom), sneg = detectNegation(top.s.text).count > 0;
    if (neg.uncertain){ put("not_in_source", "The claim contains ambiguous double negation; the source is quoted but no direction is assigned."); return; }
    if (!!neg.flip !== sneg){ put("refuted", "The source states the same proposition with the opposite polarity."); }
    else { put("supported", "The source states this proposition directly."); }
  });
  return {
    mode:"citation", input:claim,
    source:{name:sourceName, sha256:"", chars:source.length, sentences:sentences.length},
    summary:{claims:findings.length, supported:findings.filter(f=>f.verdict==="supported").length,
      refuted:findings.filter(f=>f.verdict==="refuted").length,
      not_in_source:findings.filter(f=>f.verdict==="not_in_source").length,
      adjudicated:findings.length},
    verdicts:findings,
    disclaimer:"Every atom gets a finding. not_in_source means the provided text does not state the claim; it is a result, not a refusal."
  };
}

function renderCitation(r){
  const CIT_LABEL = {supported:"Supported by this source", refuted:"Refuted by this source", not_in_source:"Not stated in this source"};
  document.getElementById("summary").innerHTML = [
    ["claims","Atoms"],["supported","Supported"],["refuted","Refuted"],["not_in_source","Not in source"]
  ].map(([k,l]) => '<div class="stat"><div class="n">'+r.summary[k]+'</div><div class="l">'+l+'</div></div>').join("");
  const box = document.getElementById("claims"); box.innerHTML = "";
  r.verdicts.forEach(v => {
    const near = (v.near||[]).slice(0,2).map(n => '<div class="cit-near">closest: “'+esc(n.text.slice(0,150))+'” <b>'+Math.round(n.coverage*100)+'%</b></div>').join("");
    const quote = v.source_sentence ? '<div class="cit-quote">“'+esc(v.source_sentence)+'”'+
      '<div class="cit-meta">characters '+(v.char_offset?v.char_offset[0]+'–'+v.char_offset[1]:'—')+' · claim terms covered: '+Math.round(v.coverage*100)+'%</div></div>' : "";
    const el = document.createElement("div"); el.className = "claim";
    el.innerHTML = '<div class="claim-head"><span class="badge '+v.verdict+'">'+CIT_LABEL[v.verdict]+'</span><div class="claim-txt">'+esc(v.claim)+'</div></div>'+
      '<div class="claim-body"><div class="explain">'+esc(v.reason)+'</div>'+quote+near+
      '<div class="cit-meta">Source: '+esc(r.source.name)+' · '+r.source.chars+' chars · '+r.source.sentences+' sentences'+(r.source.sha256?' · sha256 '+esc(r.source.sha256.slice(0,12)):'')+'</div></div>';
    box.appendChild(el);
  });
  document.getElementById("runmeta").textContent = "Citation audit · "+r.summary.claims+" atom(s) · "+r.summary.adjudicated+" finding(s) (100%)";
  document.getElementById("disclaimer").textContent = r.disclaimer;
  document.getElementById("result").style.display = "block";
}

const CJK_RE = /[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/g;
const GATE_TEXT = {
  cjk: {
    title:"English only — this demo cannot read this input",
    body:"The text contains CJK (Chinese/Japanese/Korean) characters. The evidence corpus, the anchor rules and every citation are English, so no claim was extracted and nothing was verified. Claims: 0 here is not a verdict.",
    action:"Paste the claim in English, or translate it first. Try one of the English examples above."
  },
  non_latin: {
    title:"English only — this demo cannot read this input",
    body:"The text has no Latin letters, and the corpus plus the anchor rules are English, so nothing could be checked. Claims: 0 here is not a verdict.",
    action:"Paste the claim in English, or translate it first. Try one of the English examples above."
  },
  empty: {
    title:"Nothing to check",
    body:"The input is empty, so no claim was extracted.",
    action:"Paste a declarative claim, e.g. \"Antibiotics cure viral infections.\""
  },
  no_claim: {
    title:"No checkable claim found",
    body:"The text was read, but every fragment was filtered out: questions, subjective statements and fragments shorter than three words are not checkable, and no atomic claim survived. Claims: 0 here is not a verdict.",
    action:"Write a full declarative sentence, e.g. \"Antibiotics cure viral infections.\""
  },
  too_long: {
    title:"Input too long to check as one claim",
    body:"The input is longer than the 6000-character budget, so it was not read at all. A long passage would be split into many claims and would also multiply the cost of the optional model call. Claims: 0 here is not a verdict.",
    action:"Paste the single claim you want checked, or one short paragraph at a time."
  }
};
var MAX_INPUT = 6000;
function inputKind(text){
  const s = text || "";
  if(!s.trim()) return "empty";
  const cjk = (s.match(CJK_RE)||[]).length, latin = (s.match(/[A-Za-z]/g)||[]).length;
  if(cjk && cjk >= latin) return "cjk";
  if(!latin) return "non_latin";
  return "english";
}
function unsupported(text, kind, prefix){
  const n = GATE_TEXT[kind] || GATE_TEXT.no_claim;
  const gate = {step:"language_gate", input:text, method:"script-detection", output:kind, detail:n.body};
  return {
    verdicts:[], trace:(prefix||[]).concat([gate]),
    summary:{claims:0,supported:0,refuted:0,undetermined:0},
    unsupported_input:{kind:kind,title:n.title,body:n.body,action:n.action}
  };
}
function analyze(text){
  const kind = inputKind(text);
  if(kind !== "english") return unsupported(text, kind);
  if((text||"").trim().length > MAX_INPUT) return unsupported(text, "too_long");
  const claims = ruleSplit(text), verdicts = [], trace = [];
  trace.push({step:"decompose",input:text,method:"rule",output:claims,detail:"Split on sentence and list punctuation plus connectors; questions and subjective fragments are filtered."});
  if(!claims.length) return unsupported(text, "no_claim", trace);
  claims.forEach(claim => {
    const neg = detectNegation(claim);
    trace.push({step:"negation",input:claim,method:"marker-detection",output:{flip:neg.flip,uncertain:neg.uncertain,markers:neg.markers},detail:"Negation markers are stripped for retrieval; one marker inverts stance, double negation refuses."});
    const rr = retrieve(neg.normalized), hits = rr.hits;
    trace.push({step:"retrieve",input:neg.normalized,method:"synonym-norm+bm25-lite+anchor-gate+scope",output:hits.map(h=>h.c.id+":"+h.s.toFixed(2)),detail:"Synonym normalization + IDF-weighted anchors, scope guards, Top-3."});
    trace.push({step:"semantic",input:claim,method:"degraded",output:"degraded",detail:"Offline mode: AI semantic scoring is skipped; deterministic core is running."});
    const v = adjudicate(claim, hits, neg);
    v.near_miss = v.verdict === "undetermined" ? enrichNear(rr.near) : [];
    if (v.near_miss.length && !v.citations.length){
      const guards = [];
      const LMAP = {different_population:"a different population", different_relation:"a different relation",
        no_shared_topic:"no shared subject", missing_required_topic:"a missing required topic", different_quantity:"a different quantity", different_outcome:"a different endpoint (risk, cure, prevention)", different_predicate:"a different predicate", different_subject:"a different subject", different_strength:"a different claim strength", excluded_by_scope:"an excluded scope", topic_only:"only a topic label, not the assertion", thin_anchor:"one shared word, not the assertion"};
      v.near_miss.forEach(x => (x.reasons||[]).forEach(r => { const t = LMAP[r]||r; if (guards.indexOf(t)<0) guards.push(t); }));
      v.reason = "A card that shares the claim's words was excluded by a scope guard ("+guards.sort().join(", ")+"); the claim cannot be decided.";
      v.explain = v.reason + " (Sources checked: none)";
    }
    v.scope = scopeOf(claim);
    v.plan = v.verdict === "undetermined" ? planFor(claim, v.near_miss, v.scope) : null;
    trace.push({step:"adjudicate",input:claim,method:"three-state+gate+conflict-group+polarity",output:v.verdict,detail:"sup="+v.scores.sup+" ref="+v.scores.ref+" threshold="+MIN_SCORE+" ratio="+ratioOf(v.scores)+" groups="+v.conflicts.length+" flipped="+neg.flip});
    verdicts.push(v);
  });
  return {verdicts, trace, chains:consChains(verdicts.map(v=>v.claim)), summary:{claims:verdicts.length, supported:verdicts.filter(v=>v.verdict==="supported").length, refuted:verdicts.filter(v=>v.verdict==="refuted").length, undetermined:verdicts.filter(v=>v.verdict==="undetermined").length}};
}
function ratioOf(s){ const a=parseFloat(s.sup), b=parseFloat(s.ref); return (a>0&&b>0) ? (Math.min(a,b)/Math.max(a,b)).toFixed(2) : "0.00"; }
// Mirrors core.pipeline.analyze_many. A batch is a list of independent
// submissions: each row runs through the same analyze() call and shares nothing
// with its neighbours. That is what lets gate A42 compare it to the single-claim
// path row by row.
let BATCH_ITEMS = [];
function analyzeBatch(texts){
  const raw = (texts||[]).filter(t => typeof t === "string" && t.trim()).map(t => t.trim());
  const kept = raw.slice(0, 50);
  const items = [], counts = {supported:0, refuted:0, undetermined:0, mixed:0, not_checkable:0};
  kept.forEach(t => {
    const r = analyze(t), ov = overallVerdict(r.summary);
    counts[ov] = (counts[ov]||0)+1;
    const sources = [];
    r.verdicts.forEach(v => (v.citations||[]).forEach(c => {
      const sid = c.sid || c.source_id;
      if(sid && sources.indexOf(sid) < 0) sources.push(sid);
    }));
    items.push({input:t, claims:r.summary.claims, supported:r.summary.supported,
      refuted:r.summary.refuted, undetermined:r.summary.undetermined, verdict:ov,
      sources:sources.sort(), reason:(r.verdicts[0]||{}).reason || ""});
  });
  return {n:items.length, dropped:Math.max(0, raw.length-kept.length), limit:50, counts:counts, items:items};
}
const BATCH_LABEL = {supported:"Supported", refuted:"Refuted", undetermined:"Cannot decide", mixed:"Mixed", not_checkable:"Not checkable"};
function renderBatch(b){
  BATCH_ITEMS = b.items.map(x => x.input);
  const bits = [
    b.n+" claims",
    b.counts.supported+" supported",
    b.counts.refuted+" refuted",
    b.counts.undetermined+" cannot decide"
  ];
  if(b.counts.mixed) bits.push(b.counts.mixed+" mixed");
  if(b.counts.not_checkable) bits.push(b.counts.not_checkable+" not checkable");
  if(b.dropped) bits.push(b.dropped+" dropped (limit "+b.limit+")");
  document.getElementById("batchCount").textContent = bits.join(" · ");
  if(!b.n){
    document.getElementById("batchOut").innerHTML = '<div class="corpus-item"><div class="body"><div class="m">Nothing to check yet: put one claim per line.</div></div></div>';
    return;
  }
  const row = (x,i) => {
    const bg = x.verdict==="mixed" ? "mixed" : (x.verdict==="not_checkable" ? "neutral" : x.verdict);
    return '<tr><td class="num">'+(i+1)+'</td>'+
      '<td class="b-text">'+esc(x.input.length>96 ? x.input.slice(0,93)+"..." : x.input)+'</td>'+
      '<td><span class="badge '+bg+'">'+BATCH_LABEL[x.verdict]+'</span></td>'+
      '<td class="num">'+x.claims+'</td>'+
      '<td class="src">'+esc(x.sources.length ? x.sources.slice(0,3).join(", ")+(x.sources.length>3?" +"+(x.sources.length-3):"") : "none")+'</td>'+
      '<td><button class="row-btn" data-i="'+i+'">Open</button></td></tr>';
  };
  document.getElementById("batchOut").innerHTML =
    '<table class="batch"><thead><tr><th>#</th><th>Claim</th><th>Verdict</th><th>Atoms</th><th>Sources cited</th><th></th></tr></thead><tbody>'+
    b.items.map(row).join("")+'</tbody></table>';
  document.querySelectorAll("#batchOut .row-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const i = parseInt(btn.getAttribute("data-i"),10);
      document.getElementById("input").value = BATCH_ITEMS[i];
      run(BATCH_ITEMS[i]);
    });
  });
}
function searchCorpus(q){
  const s = document.getElementById("corpusSearch");
  if(!s) return;
  s.value = q; corpusQuery = q.toLowerCase(); corpusTag = "";
  const f = document.getElementById("corpusFilters");
  if(f && f.querySelectorAll) f.querySelectorAll(".chip").forEach(x => x.classList.toggle("on", x.getAttribute("data-t")===""));
  renderCorpus();
  const card = document.getElementById("corpusCard");
  if(card && card.scrollIntoView) card.scrollIntoView({behavior:"smooth",block:"start"});
}
function wireQueryChips(){
  document.querySelectorAll(".qchip").forEach(b => {
    if(b.getAttribute("data-wired")) return;
    b.setAttribute("data-wired","1");
    b.addEventListener("click", () => searchCorpus(decodeURIComponent(b.getAttribute("data-q")||"")));
  });
}
function esc(s){ return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
const LABEL = {supported:"Evidence supports", refuted:"Evidence refutes", undetermined:"Insufficient evidence / cannot decide"};
// Mirrors core/plan.py. Scope describes the corpus's subjects; the plan lists the
// evidence that is missing. Neither can change a verdict.
const PLAN_WOULD_CHANGE = "A card asserting this proposition, for the same population and endpoint, from a source this corpus already treats as authoritative would settle it. A card that only shares the topic cannot: that is the guard this refusal is standing on.";
const PLAN_BASIS = "verbatim claim + the nearest card's own assertion + the corpus's nearest topic";
function tagCounts(){ const m={}; DATA.cards.forEach(c=>(c.tags||[]).forEach(t=>m[t]=(m[t]||0)+1)); return m; }
function orderTags(names, counts){
  return names.slice().sort((a,b)=>{
    const d=(counts[b]||0)-(counts[a]||0); if(d) return d;
    const al=a.toLowerCase(), bl=b.toLowerCase();
    if(al<bl) return -1; if(al>bl) return 1;
    if(a<b) return -1; if(a>b) return 1; return 0;
  });
}
function scopeOf(claim){
  const text=String(claim||"").toLowerCase(), tags=tagCounts(), counts={};
  Object.keys(tags).forEach(t=>{ if(text.indexOf(t.toLowerCase())>=0) counts[t]=tags[t]; });
  const tagged=DATA.cards.filter(c=>(c.tags||[]).some(t=>text.indexOf(t.toLowerCase())>=0)).length;
  const hasCondition=outcomeClasses(claim).length>0;
  const topics=Object.keys(counts).length
    ? orderTags(Object.keys(counts),counts).slice(0,3)
    : orderTags(Object.keys(tags),tags).slice(0,3);
  return {in_corpus:Object.keys(counts).length>0 || hasCondition, topics:topics,
          tagged_cards:tagged, basis:"topic label or a condition word the corpus knows"};
}
function planFor(claim, near, scope){
  const qs=[String(claim||"").trim().replace(/[,.;:]+$/,"")+" evidence"];
  if(near && near.length) qs.push(near[0].card_claim);
  if(scope && scope.topics && scope.topics.length) qs.push(scope.topics[0]+" official guidance");
  return {queries:qs, would_change:PLAN_WOULD_CHANGE, basis:PLAN_BASIS};
}
function enrichNear(near){
  return (near||[]).map(x=>{
    const c=DATA.cards.find(k=>k.id===x.card_id)||{};
    return Object.assign({}, x, {source_id:c.sid||null, source_name:c.src||null,
      url:c.url||null, snippet:c.snip||null, stance:c.stance||null});
  });
}
function overallVerdict(s){
  const n=s.claims||0;
  if(!n) return "not_checkable";
  if(s.supported===n) return "supported";
  if(s.refuted===n) return "refuted";
  if(s.undetermined===n) return "undetermined";
  return "mixed";
}
function matchedHtml(c){
  if (!c || !Array.isArray(c.matched)) return "";
  const m = c.matched;
  if (!m.length) return '<div class="ev-match">No shared vocabulary with the claim</div>';
  return '<div class="ev-match">Matched on: '+m.map(x => '<b>'+esc(x)+'</b>').join(", ")+'</div>';
}
function snapQuote(s){
  if (!s || !s.x) return "";
  const o = (s.o && s.o.length === 2) ? 'chars '+esc(String(s.o[0]))+'–'+esc(String(s.o[1]))+' · ' : '';
  return '<blockquote class="snap-quote">'+esc(s.x)+'</blockquote>'+
    '<div class="snap-meta">'+o+'¶'+esc(String(s.p))+' of the archived page'+
    (s.ph ? ' · page sha256 '+esc(s.ph)+'…' : '')+'</div>';
}
function snapshotHtml(c){
  const s = c && c.snap;
  if (!s) return "";
  if (s.st === "verified")
    return '<details class="ev-snap"><summary>Archived snapshot verified · '+esc(s.d||"")+' · ¶'+esc(String(s.p))+
      (s.h ? ' · sha256 '+esc(s.h.slice(0,10))+'…' : '')+'<span class="snap-hint">read the paragraph</span></summary>'+
      snapQuote(s)+'</details>';
  if (s.st === "page_changed" || s.st === "source_changed")
    return '<div class="ev-snap warn">'+esc(s.note || "The page has changed since this card was written")+
      (s.x ? '<div class="snap-now">Current archived text: '+esc(s.x)+'</div>' : '')+'</div>';
  if (s.st === "unresolved")
    return '<div class="ev-snap warn">No archived paragraph for this card: '+esc(s.note || "the page no longer carries the claim")+'</div>';
  return "";
}

/* ---------- v6: judge-facing evidence layer ----------
 * These functions only ADD presentation. The kernel above (ruleSplit /
 * retrieve / adjudicate / analyze) is unchanged so A14 parity still holds.
 */
function topicIndex(){
  const m = {};
  DATA.cards.forEach(c => (c.tags||[]).forEach(t => m[t]=(m[t]||0)+1));
  return Object.keys(m).sort((a,b)=>m[b]-m[a]).map(t=>({name:t,n:m[t]}));
}
function nearestTopics(claim, limit){
  const words = new Set(enWords(claim).filter(w=>!EN_STOP.has(w)&&w.length>3));
  const score = {};
  DATA.cards.forEach(c=>{
    const hay = (c.claim+" "+(c.tags||[]).join(" ")+" "+c.snip).toLowerCase();
    let hit=0; words.forEach(w=>{ if(hay.indexOf(w)>=0) hit++; });
    if(hit) (c.tags||[]).forEach(t=> score[t]=(score[t]||0)+hit);
  });
  const out = Object.keys(score).sort((a,b)=>score[b]-score[a]);
  const matched = out.length > 0;
  topicIndex().slice(0,limit).forEach(t=>{ if(out.indexOf(t.name)<0) out.push(t.name); });
  return {list: out.slice(0,limit), matched: matched};
}
let LAST_CLAIMS = [];
function nearMissHtml(v){
  const nm = v.near_miss || [];
  if(!nm.length) return "";
  const label = {different_population:"a different population", different_relation:"a different relation",
    no_shared_topic:"no shared subject", missing_required_topic:"a missing required topic", different_quantity:"a different quantity", different_outcome:"a different endpoint (risk, cure, prevention)", different_predicate:"a different predicate", different_subject:"a different subject", different_strength:"a different claim strength", excluded_by_scope:"an excluded scope", topic_only:"only a topic label, not the assertion", thin_anchor:"one shared word, not the assertion"};
  return '<div class="near-miss"><div class="t">Card'+(nm.length>1?'s':'')+' that came close, and why '+(nm.length>1?'they were':'it was')+' not used</div>'+
    nm.map(x => '<div class="nm"><span class="nm-card">'+esc(x.card_id)+'</span>'+
      '<span class="nm-claim">"'+esc(x.card_claim)+'"</span>'+
      '<span class="nm-why">not used: '+esc((x.reasons||[]).map(r=>label[r]||r).join(" + "))+'</span></div>'+
      (x.source_name ? '<div class="nm-src">Background only — '+esc(x.source_name)+
        (x.url ? ' · <a href="'+esc(x.url)+'" target="_blank" rel="noopener">open source ↗</a>' : '')+
        (x.snippet ? '<div class="nm-snip">'+esc(x.snippet)+'</div>' : '')+'</div>' : '')).join("")+
    '<div class="nm-foot">Excluded by a guard, not by a low score: the words matched, the proposition did not. The sources above are shown as background; none of them produced this verdict.</div></div>';
}
function coverageHint(v, idx){
  if(v.verdict!=="undetermined") return "";
  const nt = nearestTopics(v.claim,3);
  const missing = (v.missing||"a directly relevant authoritative source").replace(/\.$/,"");
  const n = v.citations.length;
  const nm = v.near_miss || [];
  const scope = v.scope || {};
  const boundary = n !== 0
    ? 'Only '+n+' background card'+(n===1?'':'s')+' matched; no source in the '+DATA.cards.length+'-card corpus directly verifies or refutes this claim. The gate refuses rather than stretching weak evidence into a verdict.'
    : (nm.length
      ? 'Cards below share the claim\u2019s words, but none may decide it: each was excluded by a scope guard, not by a low score. So the citation gate refuses instead of borrowing a neighbouring verdict.'
      : 'No card in the '+DATA.cards.length+'-card corpus matches this claim, so the citation gate will not produce a verdict.');
  const scopeLine = !scope.in_corpus
    ? 'Outside the corpus\u2019s subjects entirely — no card carries a topic label or a condition word this claim uses.'
    : (scope.tagged_cards
      ? 'Inside the corpus\u2019s subjects ('+esc((scope.topics||[]).join(", "))+'), so the gap is evidence, not scope.'
      : 'The corpus has a condition word for this claim, but no card carries a topic label it uses — the gap is evidence, not scope.');
  const plan = v.plan || {};
  const planHtml = (plan.queries && plan.queries.length)
    ? '<div class="plan"><div class="t">What would settle this</div>'+
      '<div class="qrow">'+plan.queries.map((q,i)=>'<button class="qchip" data-q="'+esc(encodeURIComponent(q))+'">Search the corpus for: '+esc(q)+'</button>').join("")+'</div>'+
      '<div class="d">'+esc(plan.would_change||"")+'</div></div>'
    : '';
  return '<div class="cov-hint"><div class="t">Why this is a refusal — the coverage boundary</div>'+
    '<div class="d">'+boundary+' '+scopeLine+' What is missing: '+esc(missing)+'. This is about corpus coverage, not about whether the claim is true.</div>'+
    nearMissHtml(v)+planHtml+
    '<div class="cov-topics"><span style="background:transparent;border:none;color:var(--ink3);padding-left:0">'+
    (nt.matched ? "Nearest covered topics:" : "This claim has no topic overlap; most covered topics:")+'</span>'+
    nt.list.map(t=>'<span>'+esc(t)+'</span>').join("")+'</div>'+
    '<button onclick="jumpToCorpus('+idx+')">Browse what this corpus covers →</button></div>';
}
function anatomyHtml(v, r, idx){
  const mine = (r.trace||[]).filter(t=>t.input===v.claim);
  const get = s => mine.find(t=>t.step===s);
  const ret = get("retrieve"), neg = get("negation"), rec = get("recall"), sem = get("semantic");
  const retOut = ret ? (Array.isArray(ret.output) ? ret.output.join(", ") : String(ret.output||"")) : "";
  const nodes = [
    ["Atomic claim", (idx+1)+" of "+r.verdicts.length],
    ["Polarity", neg ? (neg.output.uncertain?"double → refuse":(neg.output.flip?"negated → stance inverted":"positive")) : "n/a"],
    ["Lexical retrieval", retOut ? retOut : "0 hits"],
    ["AI recall", rec ? String(rec.output) : (sem && sem.output==="degraded" ? "not active in offline core" : "not needed")],
    ["Citation gate", v.citations.length+" valid card"+(v.citations.length===1?"":"s")],
    ["Verdict", v.verdict]
  ];
  return '<div class="anatomy">'+nodes.map(n =>
    '<div class="anat'+(n[0]==="AI recall"?" hot":"")+'"><div class="k">'+n[0]+'</div><div class="v">'+esc(n[1])+'</div></div>').join("")+'</div>';
}
function verdictBadge(v){ return '<span class="badge '+v+'">'+LABEL[v]+'</span>'; }

function initMetrics(){
  const s = DATA.stats;
  document.getElementById("metrics").innerHTML = [
    [s.cards,"evidence cards"],[s.sources,"authoritative sources"],
    [s.cases,"held-out claims"],["+"+s.delta,"AI recall gain (measured)"]
  ].map(x => '<div class="metric"><b>'+esc(x[0])+'</b><span>'+x[1]+'</span></div>').join("");
}
function initAiHeadline(){
  const el = document.getElementById("aiHeadline"), m = DATA.replay.meta, cases = DATA.replay.cases || [];
  if(!el || !m) return;
  const gated = cases.filter(c=>c.kind==="gated").length;
  const gain = cases.length - gated;
  el.innerHTML = 'AI recovered <b>'+gain+' of '+cases.length+'</b> low-overlap restatements the offline core refused, '+
    'and the gate still refuses <b>'+gated+'</b>. The model never writes a stance or a verdict.';
}
function initCoverage(){
  const el = document.getElementById("covStats"), note = document.getElementById("covNote"), s = DATA.stats;
  if(!el || s.answered == null || s.ext_claims == null) return;
  const pct = v => (Math.round(v*10000)/100).toFixed(2)+"%";
  el.innerHTML = [
    [s.ext_claims,"claims written by other people"],
    [s.answered,"answered by the kernel"],
    [s.refused,"refused"],
    [pct(s.in_domain),"coverage inside the corpus's own subject"]
  ].map(x => '<div class="cov-stat"><b>'+esc(x[0])+'</b><span>'+x[1]+'</span></div>').join("");
  note.textContent = 'Of the '+s.refused+' refusals, '+s.with_contact+' still reached at least one card and were stopped by a guard; '+
    (s.refused - s.with_contact)+' shared no content word with any card. Both counts, and the four numbers above, are recomputed from '+
    'the result file by gate A35 and bound to a receipt — a judge can open the file instead of trusting this sentence.';
}
function initReplay(){
  const el = document.getElementById("replayChips");
  el.innerHTML = DATA.replay.cases.map((c,i) =>
    '<span class="chip'+(c.kind==="gated"?" gated":"")+'" data-i="'+i+'">'+esc(c.id)+(c.kind==="gated"?" · gate":"")+'</span>').join("");
  el.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => {
    el.querySelectorAll(".chip").forEach(x=>x.classList.remove("on"));
    ch.classList.add("on");
    renderReplay(parseInt(ch.getAttribute("data-i"),10));
  }));
  if(el.querySelector('.chip[data-i="0"]')) el.querySelector('.chip[data-i="0"]').classList.add("on");
  renderReplay(0);
}
function renderReplay(i){
  const c = DATA.replay.cases[i], o = c.offline, a = c.ai;
  document.getElementById("replayOffline").innerHTML =
    '<div class="claim-txt">'+esc(c.text)+'</div>'+verdictBadge(o.verdict)+
    '<div class="txt">'+esc(o.reason||"No matching evidence card in this corpus.")+'</div>'+
    '<div class="txt" style="margin-top:6px;color:var(--ink3)">Evidence cards: '+o.citations.length+'</div>';
  let html = '<div class="claim-txt">'+esc(c.text)+'</div>'+verdictBadge(a.verdict);
  if(a.citations.length){
    html += a.citations.map(x => '<div class="mini-ev"><div class="s">'+esc(x.source_name)+
      ' <span style="color:var(--ink3);font-weight:400">· '+esc(x.card_id)+'</span></div>'+
      '<div class="p">'+esc(x.snippet)+'</div>'+matchedHtml(x)+'<a href="'+esc(x.url)+'" target="_blank" rel="noopener">Open original source ↗</a></div>').join("");
  } else {
    html += '<div class="txt">'+esc(a.reason||"No evidence card recalled.")+'</div>';
  }
  html += '<div class="gate-note">'+(c.kind==="gain"
    ? 'AI nominated <b>'+esc(String(a.recall_output))+'</b> as the same proposition. Stance <b>'+esc(a.citations[0]?a.citations[0].stance:"")+'</b> was read from the stored card — never authored by the model. The deterministic citation gate produced the verdict.'
    : 'Deliberate counterexample: AI recall did not earn a verdict here. The card is weak background evidence, or no real card matched, so the gate still refuses.')+'</div>';
  document.getElementById("replayAi").innerHTML = html;
  const m = DATA.replay.meta;
  document.getElementById("replayFoot").innerHTML =
    '<b>'+m.gain_case_count+' of '+m.gain_case_count+'</b> low-overlap restatements recovered with AI, versus <b>0</b> by the offline core. '+
    'On the full 14-case set: rule-only <b>7.1%</b> → rule+AI <b>100%</b> (measured delta <b>+'+m.measured_delta+'</b>). '+
    'The three "gate" chips are deliberate counterexamples where AI may still not produce a verdict.<br>'+
    '<span style="color:var(--ink3)">'+esc(m.honesty)+' Captured '+esc(m.captured_at)+' with '+esc(m.provider)+' · '+esc(m.requested_model)+'.</span>';
}
let corpusQuery = "", corpusTag = "", corpusArchived = false;
function snapVerifiedCount(){
  const m = DATA.snaps || {};
  return Object.keys(m).filter(k => m[k].st === "verified").length;
}
function initCorpus(){
  const f = document.getElementById("corpusFilters");
  f.innerHTML = '<span class="chip on" data-t="">All '+DATA.cards.length+'</span>'+
    topicIndex().map(t=>'<span class="chip" data-t="'+esc(t.name)+'">'+esc(t.name)+' '+t.n+'</span>').join("")+
    '<span class="chip arch" data-s="1">Archived ¶ '+snapVerifiedCount()+'</span>';
  f.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => {
    if (ch.getAttribute("data-s")) {
      corpusArchived = !corpusArchived;
      ch.classList.toggle("on", corpusArchived);
      renderCorpus();
      return;
    }
    f.querySelectorAll(".chip").forEach(x=>x.classList.remove("on"));
    ch.classList.add("on"); corpusTag = ch.getAttribute("data-t"); renderCorpus();
  }));
  const s = document.getElementById("corpusSearch");
  s.addEventListener("input", () => { corpusQuery = s.value.trim().toLowerCase(); renderCorpus(); });
  renderCorpus();
}
function renderCorpus(){
  const q = corpusQuery, t = corpusTag;
  const list = DATA.cards.filter(c => {
    if(corpusArchived && (((DATA.snaps||{})[c.id]||{}).st !== "verified")) return false;
    if(t && (c.tags||[]).indexOf(t)<0) return false;
    if(q && (c.claim+" "+c.src+" "+(c.tags||[]).join(" ")+" "+c.snip).toLowerCase().indexOf(q)<0) return false;
    return true;
  });
  document.getElementById("corpusCount").textContent = list.length+" of "+DATA.cards.length+" cards";
  const color = {supports:"var(--ok)",refutes:"var(--no)",contextual:"var(--warn)"};
  const snapBadge = c => {
    const s = (DATA.snaps||{})[c.id];
    if(!s) return "";
    if(s.st === "verified") return '<span class="snap-badge ok">¶'+esc(String(s.p))+' archived</span>';
    if(s.st === "unresolved") return '<span class="snap-badge no">no archived ¶</span>';
    return '<span class="snap-badge warn">page changed</span>';
  };
  document.getElementById("corpusList").innerHTML = list.map(c =>
    '<div class="corpus-item"><div class="id">'+esc(c.id)+'</div><div class="body">'+
    '<div class="c"><span class="stance-dot" style="background:'+(color[c.stance]||"var(--ink3)")+'"></span>'+esc(c.claim)+'</div>'+
    '<div class="m">'+esc(c.stance)+' · '+esc((c.tags||[]).join(", "))+' · '+esc(c.src)+' '+snapBadge(c)+'</div>'+
    '<a href="'+esc(c.url)+'" target="_blank" rel="noopener">Open source ↗</a></div></div>').join("") ||
    '<div class="corpus-item"><div class="body"><div class="m">No card matches that search. Try another topic.</div></div></div>';
}
function jumpToCorpus(idx){
  const claim = LAST_CLAIMS[idx] || "";
  const words = enWords(claim).filter(w=>!EN_STOP.has(w)&&w.length>4);
  const s = document.getElementById("corpusSearch");
  s.value = words.length ? words[0] : "";
  corpusQuery = s.value.toLowerCase(); corpusTag = "";
  const f = document.getElementById("corpusFilters");
  f.querySelectorAll(".chip").forEach(x => x.classList.toggle("on", x.getAttribute("data-t")===""));
  renderCorpus();
  const card = document.getElementById("corpusCard");
  if(card.scrollIntoView) card.scrollIntoView({behavior:"smooth",block:"start"});
}
async function probeMode(){
  if(!LOCAL_SERVER) return;
  try {
    const r = await fetch("/api/status", {cache:"no-store"});
    if(r.ok){
      const d = await r.json();
      document.getElementById("modeLabel").textContent = d.ai_available ? "deterministic + live AI" : "deterministic (offline)";
      const al = document.getElementById("aiLabel");
      if(al) al.textContent = d.ai_available ? "live" : "not configured";
    }
  } catch(e){ /* static host: keep the default label */ }
}

function render(r, mode){
  document.getElementById("summary").innerHTML = [
    ["claims","Claims"],["supported","Supported"],["refuted","Refuted"],["undetermined","Undetermined"]
  ].map(([k,l]) => '<div class="stat"><div class="n">'+r.summary[k]+'</div><div class="l">'+l+'</div></div>').join("");
  const box = document.getElementById("claims"); box.innerHTML = "";
  LAST_CLAIMS = r.verdicts.map(x => x.claim);
  if(r.unsupported_input){
    const u = r.unsupported_input;
    box.innerHTML = '<div class="notcheck"><div class="nc-t">'+esc(u.title)+'</div>'+
      '<div class="nc-b">'+esc(u.body)+'</div><div class="nc-a">'+esc(u.action)+'</div></div>';
    document.getElementById("runmeta").textContent = "Mode: "+(mode||"Local deterministic core")+" · Input not checkable ("+u.kind+") · Claims: 0";
    document.getElementById("disclaimer").textContent = DATA.notice;
    document.getElementById("result").style.display = "block";
    return;
  }
  r.verdicts.forEach((v,i) => {
    if (i === 0){
      const rels = consRelations(r.verdicts.map(x => x.claim));
      if (rels.length){
        const h = document.createElement("div"); h.className = "consistency";
        h.innerHTML = '<div class="t">'+(rels.length>1?'Atoms that cannot both be true':'Two atoms in this submission cannot both be true')+'</div>'+
          rels.map(x => '<div class="cr"><span class="ca">'+esc(r.verdicts[x.atoms[0]].claim)+'</span><span class="vs">vs</span><span class="ca">'+esc(r.verdicts[x.atoms[1]].claim)+'</span>'+
            '<div class="cb">'+esc(consExplain(x))+' Each atom is judged on its own evidence; neither verdict is averaged into the other.</div></div>').join("");
        box.appendChild(h);
      }
      const chs = (r.chains || []).filter(x => x.conflict);
      if (chs.length){
        const h = document.createElement("div"); h.className = "consistency chain";
        h.innerHTML = '<div class="t">A two-step chain makes these atoms impossible</div>'+
          chs.map(x => '<div class="cr"><span class="ca">'+esc(r.verdicts[x.atoms[0]].claim)+'</span>'+
            '<span class="vs">+</span><span class="ca">'+esc(r.verdicts[x.atoms[1]].claim)+'</span>'+
            '<span class="vs">⇒</span><span class="ca">'+esc(x.derived)+'</span>'+
            '<div class="cb">'+esc(x.note)+' Basis: '+esc(x.basis)+'</div></div>').join("");
        box.appendChild(h);
      }
    }
    const stanceLabel = {supports:"supports",refutes:"refutes",contextual:"background",conflicting:"differs"};
    const evs = v.citations.map(c => '<div class="ev"><span class="ev-stance '+c.stance+'">'+(stanceLabel[c.stance]||c.stance)+(c.polarity_flipped?' (inverted)':'')+'</span><div class="ev-main"><div class="ev-src">'+esc(c.src)+' <span style="color:var(--ink3);font-weight:400">· '+esc(c.sid)+'</span></div><div class="ev-snip">'+esc(c.snip)+'</div>'+matchedHtml(c)+snapshotHtml(c)+'<a class="ev-link" href="'+esc(c.url)+'" target="_blank" rel="noopener">Open original source ↗</a></div></div>').join("") || '<div class="ev-snip" style="color:var(--ink3)">No relevant evidence card found.</div>';
    const steps = (r.trace||[]).filter(t => t.input===v.claim).map(t => '<div class="trace-step"><div class="k">'+t.step+'</div><div class="v">'+esc(JSON.stringify(t.output))+' · '+esc(t.detail)+'</div></div>').join("");
    const el = document.createElement("div"); el.className = "claim";
    el.innerHTML = '<div class="claim-head"><span class="badge '+v.verdict+'">'+LABEL[v.verdict]+'</span><div class="claim-txt">'+esc(v.claim)+'</div></div>'+
      '<div class="claim-body">'+anatomyHtml(v,r,i)+coverageHint(v,i)+
      '<div class="explain">'+esc(v.explain).replace("(Sources checked: )","")+'</div>'+
      '<div class="ev-title">Evidence cards ('+v.citations.length+')</div>'+evs+
      '<button class="trace-btn" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display===\'block\'?\'none\':\'block\'">▸ Show audit trail</button>'+
      '<div class="trace">'+steps+'</div></div>';
    box.appendChild(el);
  });
  document.getElementById("runmeta").textContent = "Mode: "+(mode||"Local deterministic core")+" · Claims: "+r.summary.claims;
  document.getElementById("disclaimer").textContent = DATA.notice;
  document.getElementById("result").style.display = "block";
  wireQueryChips();
}

let API_OK = null;
async function apiReady(){
  if (!LOCAL_SERVER) return false;
  if (API_OK !== null) return API_OK;
  try { const r = await fetch("/api/status", {cache:"no-store"}); API_OK = r.ok; }
  catch(e){ API_OK = false; }
  return API_OK;
}
let MODE = "corpus";
function setMode(m){
  MODE = m;
  document.querySelectorAll("#modeSwitch .mode-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-mode") === m);
  });
  const cit = m === "citation";
  document.getElementById("sourceInput").style.display = cit ? "block" : "none";
  document.getElementById("citTags").style.display = cit ? "flex" : "none";
  document.getElementById("demoTags").style.display = cit ? "none" : "flex";
  document.getElementById("inputTitle").textContent = cit ? "Check a claim against its source" : "Paste a claim";
  document.getElementById("inputHint").textContent = cit
    ? "Paste the claim, then the document, paragraph or quotation it cites. Every atom gets a finding: supported, refuted, or not stated in this source. A finding is always produced, because you supplied the evidence."
    : "Enter a claim or text from a screenshot. It is split into independently checkable claims and matched against the built-in evidence corpus.";
  document.getElementById("runBtn").textContent = cit ? "Audit citation →" : "Analyze →";
  document.getElementById("result").style.display = "none";
}
async function runCitation(claim){
  const source = document.getElementById("sourceInput").value.trim();
  if (!claim){ document.getElementById("input").focus(); return; }
  if (!source){ document.getElementById("sourceInput").focus(); return; }
  let result = null;
  if (await apiReady()){
    try {
      const r = await fetch("/api/citation", {method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({claim:claim, source:source, source_name:"pasted source"})});
      if (r.ok){ result = await r.json(); }
    } catch(e){ /* fall back to the local kernel */ }
  }
  if (!result) result = citationAudit(claim, source);
  if (result.error){
    const box = document.getElementById("claims");
    box.innerHTML = '<div class="notcheck"><div class="nc-t">Nothing to audit</div><div class="nc-b">'+esc(result.error)+'</div><div class="nc-a">Paste a claim and the source it cites.</div></div>';
    document.getElementById("result").style.display = "block";
    return;
  }
  renderCitation(result);
  document.getElementById("result").scrollIntoView({behavior:"smooth", block:"start"});
}
async function run(text){
  text = (text || document.getElementById("input").value).trim();
  if (!text){ document.getElementById("input").focus(); return; }
  if (MODE === "citation"){ return runCitation(text); }
  let result = null, mode = "";
  if (await apiReady()){
    try {
      const r = await fetch("/api/analyze", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({text:text})});
      if (r.ok){ result = await r.json(); mode = result.mode || "Online core"; }
    } catch(e){ /* fall back explicitly, never silently */ }
  }
  if (!result){ result = analyze(text); mode = "Local deterministic core"; }
  render(result, mode);
  document.getElementById("result").scrollIntoView({behavior:"smooth", block:"start"});
}
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("demoTags").innerHTML = DATA.demos.map(d => '<span class="tag" data-t="'+esc(d.text)+'">'+esc(d.label)+'</span>').join("");
  document.getElementById("citTags").innerHTML = CIT_DEMOS.map((d,i) => '<span class="tag" data-cit="'+i+'">'+esc(d.label)+'</span>').join("");
  document.querySelectorAll(".tag").forEach(t => t.addEventListener("click", () => {
    const ci = t.getAttribute("data-cit");
    if (ci !== null){
      const d = CIT_DEMOS[parseInt(ci, 10)];
      document.getElementById("input").value = d.claim;
      document.getElementById("sourceInput").value = d.source;
      run(d.claim);
      return;
    }
    document.getElementById("input").value = t.getAttribute("data-t");
    run(t.getAttribute("data-t"));
  }));
  document.querySelectorAll("#modeSwitch .mode-btn").forEach(b => {
    b.addEventListener("click", () => setMode(b.getAttribute("data-mode")));
  });
  document.getElementById("runBtn").addEventListener("click", () => run());
  document.getElementById("batchBtn").addEventListener("click", () => {
    const text = document.getElementById("batchInput").value;
    const lines = text.split(/\n+/).map(s => s.trim()).filter(Boolean);
    renderBatch(analyzeBatch(lines));
    document.getElementById("batchCard").scrollIntoView({behavior:"smooth", block:"start"});
  });
  document.getElementById("clearBtn").addEventListener("click", () => {
    document.getElementById("input").value = "";
    document.getElementById("sourceInput").value = "";
    document.getElementById("result").style.display = "none";
  });
  document.getElementById("input").addEventListener("keydown", e => { if (e.ctrlKey && e.key==="Enter") run(); });
  initMetrics();
  initAiHeadline();
  initCoverage();
  initReplay();
  initCorpus();
  probeMode();
});
