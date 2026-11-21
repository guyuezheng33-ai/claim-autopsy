"""Untrusted text discipline for the optional LLM path.

A claim is attacker-controlled: anyone can paste text that contains
instructions addressed to the model ("ignore previous instructions", a fake
`System:` turn, a fabricated JSON reply). This module treats that text as
data, never as prompt syntax:

- control and zero-width characters are stripped, so hidden payloads do not
  survive normalisation;
- size is bounded, so a pasted article cannot turn into an unbounded prompt;
- `<` and `>` are escaped, so a payload cannot close the data block;
- every line is quoted, so role markers lose their line-start authority;
- the block is wrapped in an explicitly named tag the system prompt refers to
  as untrusted.

This is defence in depth, not a guarantee. The actual guarantee is structural:
the deterministic gate owns every verdict, so a model that fully obeys an
injected instruction still cannot produce a supported/refuted verdict without
a valid stored citation (gates A13 and A22).
"""

import re

MAX_INPUT = 6000

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HIDDEN = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
_SPACES = re.compile(r"[ \t]{2,}")

# Markers reported for transparency. Detection is advisory: quoted data is
# still handled the same way whether or not a marker is found.
_MARKERS = (
    "ignore previous", "ignore all previous", "disregard previous",
    "system:", "assistant:", "developer mode", "you are now",
    "return supported", "return refuted", "respond with supported",
    "set verdict", "override the", "jailbreak",
)


def normalize(text):
    """Strip invisible characters, collapse runs, trim ends, keep line breaks."""
    s = _HIDDEN.sub("", str(text or ""))
    s = _CTRL.sub("", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _SPACES.sub(" ", s)
    s = "\n".join(line.strip() for line in s.split("\n"))
    return s.strip()


def over_limit(text):
    return len(normalize(text)) > MAX_INPUT


def suspicious(text):
    """Names of instruction-like markers found in the text. For the trace only."""
    low = normalize(text).lower()
    return [m for m in _MARKERS if m in low]


def as_data(text, label="claim_text"):
    """Return a delimited, quoted data block safe to embed in a user message."""
    s = normalize(text)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    quoted = "\n".join("> " + line for line in s.split("\n") if line)
    return "<%s>\n%s\n</%s>" % (label, quoted, label)
