# Claim Autopsy — Data Dictionary

This file describes only the fields that `core/court.make_dossier()` actually returns. Every verdict is produced by the deterministic judge; the model may submit arguments but cannot write `verdict`.

## Top-level fields

| Field name | Type | Required | Meaning |
|---|---|---|---|
| `mode` | string | yes | Always `court`: this record came from the citation court. |
| `ai_mode` | string | yes | `rules` or `ai`, recording whether a model took part. |
| `input` | object | yes | User input: `claim`, `source_name`, `source_sha256`. |
| `source` | object | yes | Source stats: `source_id`, `name`, `sha256`, `chars`, `sentences`. |
| `atoms` | array | yes | Each independently checkable atom and its verdict, see below. |
| `arguments` | array | yes | Prosecution and defence arguments checked one by one. |
| `summary` | object | yes | Counts: `claims`, `supported`, `refuted`, `not_in_source`, `conflict`, `accepted_arguments`, `struck_arguments`, `ai_arguments`, `ai_accepted`, `ai_struck`, `ai_bridges`, `rule_arguments`. |
| `receipt` | object | yes | `run_id`, `generated_at`, `model`, `engine`. |
| `trace` | array | yes | Stage trace; an empty array when no model ran, never a fabricated stage. |
| `disclaimer` | string | yes | Boundary statement: this judges whether the supplied source states the claim, not whether the claim is true in the world. |

## `atoms[]` field names and types

| Field name | Type | Meaning |
|---|---|---|
| `atom_id` | string | Atom id, e.g. `A1`. |
| `claim` | string | The atom's claim sentence. |
| `verdict` | string | `supported` / `refuted` / `not_in_source` / `conflict`. |
| `reason` | string | Verdict rationale. |
| `accepted_argument_ids` | array | Argument ids the judge accepted. |
| `struck_argument_ids` | array | Argument ids the judge struck. |
| `bridge_argument_ids` | array | Accepted argument ids that used a semantic bridge. |
| `evidence_ids` | array | Source sentence ids supporting this verdict. |
| `nearest` | object/null | Closest source sentence: `quote`, `coverage`, `evidence_id`, `char_start`, `char_end`; null when none. |
| `what_would_change_it` | string | The source sentence shape that would flip this verdict. |

## `arguments[]` field names and types

| Field name | Type | Meaning |
|---|---|---|
| `argument_id` | string | Unique id containing side, atom, evidence and a quote-hash prefix. |
| `side` | string | `prosecution` or `defense`. |
| `origin` | string | `ai` or `rule`. |
| `atom_id` | string | The atom this argument addresses. |
| `relation` | string | `supports` / `contradicts` / `unknown`. |
| `evidence_id` | string | Source sentence id, e.g. `S1-P1`. |
| `source_name` | string | Source name. |
| `quote` | string | Verbatim quotation; it must be locatable in the source. |
| `quote_sha256` | string | SHA-256 of the quotation. |
| `char_start` / `char_end` | integer | Character offsets of the quotation in the source text. |
| `rationale` | string | Prosecution or defence rationale, at most 240 characters. |
| `status` | string | `accepted` or `struck`. |
| `strike_codes` | array | Rejection codes; empty when accepted. |
| `strike_reason` | string/null | Human-readable first rejection reason. |
| `checks` | object | Nine boolean checks: `quote_exact`, `relation`, `subject`, `population`, `object`, `endpoint`, `quantity`, `strength`, `polarity`. |
| `coverage` | number | IDF-weighted share of the claim's content words present in the quote, 0–1. |
| `bridge` | object/null | Semantic-bridge record; null when no bridge was used. |

## Consistency rules

- Same input, same source, same mode → same `run_id` and same `atoms` verdicts; `generated_at` is the only time field allowed to change.
- `not_in_source` means this source does not state the claim; it does not mean the claim is false.
- Every `quote` must resolve back through `char_start`/`char_end`; an argument that fails to locate its quote never enters `arguments`.
