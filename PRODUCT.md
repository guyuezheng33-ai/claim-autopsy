# Claim Autopsy — product brief

Claim Autopsy is a CLI citation-audit tool: each atom gets supported/refuted/not_in_source with exact quote; accepted only at 100% of 48 gates, 840 claims, 11 answered, 10 correct.

This file exists because the engineering is documented everywhere else and the commercial
argument is documented nowhere. It is deliberately short and deliberately unfashionable: no
market-size estimate, no traction claim, no roadmap slide. Everything below is either a fact
about the shipped build or a stated assumption that a reader can argue with.

## 1. What is being sold

Not "an AI fact-checker". A fact-checker is asked *is this true*, and the honest answer is
usually *the evidence in front of me cannot say*. Claim Autopsy makes BOTH answers the product:

- **Corpus mode** — input: one sentence, a paragraph, or a list (one claim per line, returned as
  a table); output: `supported` / `refuted` / `undetermined`, each with the source, the matched
  words, the archived paragraph and its hash — or an explicit refusal that names why no card may
  decide it (different population, different dose, different endpoint, topic label only, one
  shared word in a long claim), shows the nearest sources as labelled background, and lists the
  searches that would settle it.
- **Citation mode** — input: a claim plus the document it cites; output: `supported` /
  `refuted` / `not_in_source` for every atom, with the exact sentence and character range in the
  supplied source. Here the evidence is part of the input, so there is no coverage gap to
  explain: every atom gets a finding, and `not_in_source` is the finding that says the source
  does not state the claim.

The claim it is built on: **most tooling fails not by being wrong, but by being confidently
wrong where evidence runs out.** The 840-claim external slice is the receipt for that claim —
before the guards the kernel answered 89 claims and got 58 wrong; after them it answers 11 and
gets 10 right. Precision bought with coverage, and the trade printed in the open. That trade
also exposed the ceiling of corpus mode: even handing the matcher the benchmark's own gold
sentence only lets 30.0% of claims clear the 0.6 lexical threshold. Citation mode exists
because the honest way to keep the product useful is not to inflate a corpus, but to accept
the source the reader already has and audit it.

## 2. Who has this problem, and what they do today

The buyer is not a curious reader; a curious reader will accept any answer. The buyer is
someone whose sentence will be repeated by others and who cannot afford an unsourced claim:

- **Institutional and health communications.** A clinic, a university press office or a
  consumer-health brand writes "vitamin D reduces severity" and needs to know whether its
  evidence says *severity*, *susceptibility* or *nothing*, before a journalist checks.
- **Science and medical writers / translators.** The recurring failure is the endpoint swap:
  the source says *risk*, the draft says *cure*, and no spell-checker sees it.
- **Content review at platforms and publishers.** Reviewers need a triage signal that is
  auditable after the fact, not a model score that cannot be defended to a regulator or a
  complainant.

What they do today: paste the claim into a chatbot and get a fluent yes; or search and
hand-check; or send it to a human fact-checker who has a two-week queue. The first option
produces confident errors, the second costs an hour per claim, the third is unavailable at the
volume these teams actually face.

## 3. Why the shipped build is the shape it is

- **Zero infrastructure.** Static page plus a Python standard library core; the public demo
  runs from `file://` or Pages with no server, no database, no key. Marginal cost per query
  is zero for the deterministic path, and one small model call for the optional AI path.
- **Refusal is a feature with a receipt.** A refusal that says "no card may decide this,
  E021 came close but speaks to curing, not susceptibility" is more useful to a comms team
  than a verdict, because it tells them what evidence to go and find.
- **The corpus is small on purpose.** 112 cards, 41 authoritative sources, every citation
  archived with a paragraph hash. A small corpus that cannot lie about its coverage beats a
  large one that can — and the coverage number is published (1.96% of in-domain dev claims)
  rather than papered over.
- **Citation mode makes "useful" independent of corpus size.** The reader supplies the source;
  the kernel decomposes the claim, aligns every atom to the supplied sentences, and returns
  support, refutation or `not_in_source` with the exact quoted span. Coverage is 100% by
  construction, and the measured question becomes precision on near-verbatim citations, not
  whether an unbounded proposition happens to be in a 112-card corpus.
- **Verification is part of the product, not of the pitch.** 44 acceptance gates, a run
  receipt binding the green run to 17 files by SHA-256, a second receipt binding the external
  evaluation to the sample files and the run that scored them, the shipped page clicked in a
  real browser on every run (including all three citation findings), an error review that must
  account for every wrong external decision, and an external benchmark that is a gate rather
  than a slide.

## 4. What evidence exists today, and what is still missing

The gap this section closes is specific: the rest of this file is argument, and until now there
was not one record of the product being used. There is a mechanism and one record, and both are
checkable.

- **A session record that cannot be a testimonial.** `tools/session_log.py` writes down every
  input, the atoms it produced, the verdicts, the cited source ids, the kernel and corpus
  fingerprints, and who ran it. `tools/verify_sessions.py` replays the inputs and requires the
  same atoms, verdicts and citations; gate A40 fails the build otherwise. Edits to a record are
  caught twice — the content id stops matching, and the replay reports the drift. A session by
  anyone other than the builder must also record what that person did with the output —
  `used`, `discarded`, `re_prompted` or `no_opinion`, one sentence of why, and whether they
  would pay — and the recorder refuses to write one without it, so the first outside opinion
  cannot arrive as a compliment with no outcome attached.
- **Four sessions exist, all the builder's own.** The three earlier ones (the first with 6 inputs,
  5 atoms, 2 answered, 3 refused and 1 input that produced no checkable claim) belong to previous
  kernels and are labelled `historical:kernel_changed`; the newest was recorded after the
  outcome-class fix and replays on the current kernel, documenting the one refusal and the two
  refutations that change had to preserve. None is a customer session, and A40 prints the
  external-operator count as 0 rather than letting the sentence blur. `tools/run_external_session.py`
  turns the next one into a guided ten-minute conversation: three fixed claims in a named scenario
  (paper abstract, news brief or customer-service reply), the real verdict
  printed first, then the reviewer block.
- **What that means for the commercial argument.** None of the three buyer classes below has
  touched the tool; every claim in section 6 is still a hypothesis. What has changed is the
  cost of testing it: three sessions with outsiders turn the paragraph into evidence, and the
  recorder and replay check already exist, so the test is a ten-minute task rather than a
  study. Until those exist, this file says "no customer" and means it.

## 5. Where money would come from (three options, none proven)

Stated as options, not as a forecast. There is no customer, no pilot and no revenue today.

1. **Verification desk (seat licence).** A comms or medical-writing team pays per seat for
   "can we say this", with the audit trail exported as evidence of diligence. Value is
   measured in avoided corrections, which is exactly the kind of value that is hard to sell
   until something goes wrong once.
2. **Publisher API (usage).** A CMS or press-office tool calls the core before publish and
   receives `supported` / `refuted` / `undetermined` plus a citation or a refusal reason.
   Priced per 1,000 checks; the deterministic path costs almost nothing to serve.
3. **Audit trail for regulated speech (compliance).** The receipt — claim, card, matched
   words, archived paragraph, hash, date — is the product; the verdict is incidental. This
   is the option with the clearest budget line, and the one the current build is closest to
   being able to serve.

## 6. What has to be true for this to matter, and what would falsify it

Assumptions, each falsifiable:

- A refusal with a reason is worth more than a confident guess to at least one class of
  professional user. **Falsified if** trial users discard refusals and re-prompt a chatbot
  until they get an answer — a behaviour this product cannot beat on convenience.
- Coverage, not precision, is the binding constraint. **Falsified if** a 10× corpus does not
  move the answer rate on externally written claims. The constraint is now measured, not
  assumed: on the dev slice the kernel answers 11 of 840 (1.3%), 1.96% of the claims that share
  subject matter with the corpus, and 280 of 829 refusals share no content word with any card —
  while a perfect matcher with every guard off would still find no card restating 80% of a
  refused claim. The gap is missing propositions, which is the cheapest thing a corpus can fix
  and the most expensive thing a threshold cannot.
- Auditable evidence is a buying criterion rather than a nice-to-have. **Falsified if** the
  first ten conversations end at "just tell me true or false".

## 7. Roadmap, in the order the evidence supports

1. **Coverage.** Retrieval over the archived paragraphs rather than 112 curated cards, with
   the same citation gate. The external slice says this is the binding constraint.
2. **Claim shape.** Modal and hedged claims ("may slow", "is being studied") currently look
   like assertions to the matcher; the hold-back errors are all shape errors.
3. **Multi-source disagreement, kept visible.** Today two CDC pages that disagree produce
   `undetermined` side by side; the next step is to make that a first-class output rather
   than a refusal.
4. **Non-English input.** The corpus is English; Chinese input currently gets an explicit
   notice. Chinese sources are already in the whitelist but not in the corpus.

## 8. Honest summary

A small, auditable, zero-infrastructure evidence engine whose most valuable behaviour is
saying *no* with a reason and a receipt. It is a demonstration of a discipline — verify what
you claim, refuse what you cannot, publish the numbers that hurt — packaged so that a
professional team could adopt the discipline. It is not yet a business, and the file you are
reading is the shortest honest version of why it could become one.


