window.COURT_REPLAY = {
  "meta": {
    "label": "recorded dossiers: real local-AI runs, rules-only controls, and one adversarial fixture",
    "note": "Every AI dossier here is a recording of an actual local Qwen run; the page says so. Only `python serve.py` calls the model live. The adversarial fixture is labelled and is not a model run.",
    "live_run": {
      "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
      "provider": "local-llama.cpp",
      "generated_at": "2026-11-20T20:15:21.843797+00:00",
      "cases": [
        "flu",
        "eiffel",
        "coffee",
        "quantity",
        "population",
        "relation"
      ]
    }
  },
  "cases": {
    "flu": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "Getting a flu vaccine gives you the flu.",
        "source_name": "live fixture",
        "source_sha256": "13b95aaa1ef7d038b3aa9a3624745c285d186c807323a0240bc3143866d2fb8f"
      },
      "source": {
        "source_id": "S1",
        "name": "live fixture",
        "sha256": "13b95aaa1ef7d038b3aa9a3624745c285d186c807323a0240bc3143866d2fb8f",
        "chars": 108,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "Getting a flu vaccine gives you the flu.",
          "verdict": "refuted",
          "reason": "A verified quotation states the same proposition with the opposite polarity.",
          "accepted_argument_ids": [
            "P-A1-S1-P1-13b95a"
          ],
          "struck_argument_ids": [],
          "evidence_ids": [
            "S1-P1"
          ],
          "nearest": {
            "quote": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
            "coverage": 1.0,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 108
          },
          "what_would_change_it": "A source sentence asserting the same proposition would change this verdict."
        }
      ],
      "arguments": [
        {
          "argument_id": "P-A1-S1-P1-13b95a",
          "side": "prosecution",
          "origin": "ai",
          "atom_id": "A1",
          "relation": "contradicts",
          "evidence_id": "S1-P1",
          "source_name": "live fixture",
          "quote": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
          "quote_sha256": "13b95aaa1ef7d038b3aa9a3624745c285d186c807323a0240bc3143866d2fb8f",
          "char_start": 0,
          "char_end": 108,
          "rationale": "The evidence directly contradicts the claim that getting a flu vaccine gives you the flu.",
          "status": "accepted",
          "strike_codes": [],
          "strike_reason": null,
          "checks": {
            "quote_exact": true,
            "relation": true,
            "subject": true,
            "population": true,
            "object": true,
            "endpoint": true,
            "quantity": true,
            "strength": true,
            "polarity": true
          },
          "coverage": 1.0
        }
      ],
      "summary": {
        "claims": 1,
        "supported": 0,
        "refuted": 1,
        "not_in_source": 0,
        "conflict": 0,
        "accepted_arguments": 1,
        "struck_arguments": 0,
        "ai_arguments": 1,
        "ai_accepted": 1,
        "ai_struck": 0,
        "rule_arguments": 0
      },
      "receipt": {
        "run_id": "bb5bce9edf51e779",
        "generated_at": "2026-11-20T20:15:05.798339+00:00",
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [
        {
          "step": "advocates",
          "meta": {
            "prosecution": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 4340,
              "usage": {
                "prompt_tokens": 421,
                "completion_tokens": 66,
                "total_tokens": 487
              },
              "role": "prosecution",
              "arguments": 1,
              "output_format": "array"
            },
            "defense": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 207,
              "usage": {
                "prompt_tokens": 420,
                "completion_tokens": 2,
                "total_tokens": 422
              },
              "role": "defense",
              "arguments": 0,
              "output_format": "array"
            },
            "available": true,
            "parallel": true
          }
        }
      ],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "__source": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
      "replay_mode": "live-run-recording",
      "demo_label": "RECORDED LIVE AI RUN · qwen2.5-1.5b-instruct-q4_k_m.gguf"
    },
    "eiffel": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "The Eiffel Tower is located in Paris.",
        "source_name": "live fixture",
        "source_sha256": "27dfce3b87229e59f268c64d50e954a6d7b640bd75557ed0185b622284d0ec1b"
      },
      "source": {
        "source_id": "S1",
        "name": "live fixture",
        "sha256": "27dfce3b87229e59f268c64d50e954a6d7b640bd75557ed0185b622284d0ec1b",
        "chars": 45,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "The Eiffel Tower is located in Paris.",
          "verdict": "supported",
          "reason": "A verified quotation states the same proposition with the same polarity.",
          "accepted_argument_ids": [
            "D-A1-S1-P1-27dfce"
          ],
          "struck_argument_ids": [
            "P-A1-S1-P1-27dfce"
          ],
          "evidence_ids": [
            "S1-P1"
          ],
          "nearest": {
            "quote": "The Eiffel Tower is located in Paris, France.",
            "coverage": 1.0,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 45
          },
          "what_would_change_it": "A source sentence asserting the same proposition with the opposite polarity would change this verdict."
        }
      ],
      "arguments": [
        {
          "argument_id": "P-A1-S1-P1-27dfce",
          "side": "prosecution",
          "origin": "ai",
          "atom_id": "A1",
          "relation": "supports",
          "evidence_id": "S1-P1",
          "source_name": "live fixture",
          "quote": "The Eiffel Tower is located in Paris, France.",
          "quote_sha256": "27dfce3b87229e59f268c64d50e954a6d7b640bd75557ed0185b622284d0ec1b",
          "char_start": 0,
          "char_end": 45,
          "rationale": "The evidence explicitly states that the Eiffel Tower is located in Paris, France, which directly supports the claim.",
          "status": "struck",
          "strike_codes": [
            "side_mismatch"
          ],
          "strike_reason": "quotation points the other way",
          "checks": {
            "quote_exact": true,
            "relation": true,
            "subject": true,
            "population": true,
            "object": true,
            "endpoint": true,
            "quantity": true,
            "strength": true,
            "polarity": true
          },
          "coverage": 1.0
        },
        {
          "argument_id": "D-A1-S1-P1-27dfce",
          "side": "defense",
          "origin": "ai",
          "atom_id": "A1",
          "relation": "supports",
          "evidence_id": "S1-P1",
          "source_name": "live fixture",
          "quote": "The Eiffel Tower is located in Paris, France.",
          "quote_sha256": "27dfce3b87229e59f268c64d50e954a6d7b640bd75557ed0185b622284d0ec1b",
          "char_start": 0,
          "char_end": 45,
          "rationale": "The evidence explicitly states that the Eiffel Tower is located in Paris, France, which directly supports the claim.",
          "status": "accepted",
          "strike_codes": [],
          "strike_reason": null,
          "checks": {
            "quote_exact": true,
            "relation": true,
            "subject": true,
            "population": true,
            "object": true,
            "endpoint": true,
            "quantity": true,
            "strength": true,
            "polarity": true
          },
          "coverage": 1.0
        }
      ],
      "summary": {
        "claims": 1,
        "supported": 1,
        "refuted": 0,
        "not_in_source": 0,
        "conflict": 0,
        "accepted_arguments": 1,
        "struck_arguments": 1,
        "ai_arguments": 2,
        "ai_accepted": 1,
        "ai_struck": 1,
        "rule_arguments": 0
      },
      "receipt": {
        "run_id": "3d46adb24ebeeb26",
        "generated_at": "2026-11-20T20:15:12.064979+00:00",
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [
        {
          "step": "advocates",
          "meta": {
            "prosecution": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 6254,
              "usage": {
                "prompt_tokens": 415,
                "completion_tokens": 63,
                "total_tokens": 478
              },
              "role": "prosecution",
              "arguments": 1,
              "output_format": "array"
            },
            "defense": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 6253,
              "usage": {
                "prompt_tokens": 414,
                "completion_tokens": 63,
                "total_tokens": 477
              },
              "role": "defense",
              "arguments": 1,
              "output_format": "array"
            },
            "available": true,
            "parallel": true
          }
        }
      ],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "__source": "The Eiffel Tower is located in Paris, France.",
      "replay_mode": "live-run-recording",
      "demo_label": "RECORDED LIVE AI RUN · qwen2.5-1.5b-instruct-q4_k_m.gguf"
    },
    "coffee": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "Coffee stunts growth in children.",
        "source_name": "live fixture",
        "source_sha256": "1efdf507c30c00f7b589f8676b088d9e1c92975ef8a15e4b14488cfa7e4ad3a0"
      },
      "source": {
        "source_id": "S1",
        "name": "live fixture",
        "sha256": "1efdf507c30c00f7b589f8676b088d9e1c92975ef8a15e4b14488cfa7e4ad3a0",
        "chars": 49,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "Coffee stunts growth in children.",
          "verdict": "not_in_source",
          "reason": "No verified quotation states this proposition in the supplied source.",
          "accepted_argument_ids": [],
          "struck_argument_ids": [],
          "evidence_ids": [],
          "nearest": {
            "quote": "Vitamin D is important for bone health in adults.",
            "coverage": 0.0,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 49
          },
          "what_would_change_it": "A sentence, in this source, that states the same subject, quantity and strength as the claim would change this result."
        }
      ],
      "arguments": [],
      "summary": {
        "claims": 1,
        "supported": 0,
        "refuted": 0,
        "not_in_source": 1,
        "conflict": 0,
        "accepted_arguments": 0,
        "struck_arguments": 0,
        "ai_arguments": 0,
        "ai_accepted": 0,
        "ai_struck": 0,
        "rule_arguments": 0
      },
      "receipt": {
        "run_id": "b92cbe6c0e15744b",
        "generated_at": "2026-11-20T20:15:12.642588+00:00",
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [
        {
          "step": "advocates",
          "meta": {
            "prosecution": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 568,
              "usage": {
                "prompt_tokens": 411,
                "completion_tokens": 2,
                "total_tokens": 413
              },
              "role": "prosecution",
              "arguments": 0,
              "output_format": "array"
            },
            "defense": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 567,
              "usage": {
                "prompt_tokens": 410,
                "completion_tokens": 2,
                "total_tokens": 412
              },
              "role": "defense",
              "arguments": 0,
              "output_format": "array"
            },
            "available": true,
            "parallel": true
          }
        }
      ],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "__source": "Vitamin D is important for bone health in adults.",
      "replay_mode": "live-run-recording",
      "demo_label": "RECORDED LIVE AI RUN · qwen2.5-1.5b-instruct-q4_k_m.gguf"
    },
    "struck": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "Getting a flu vaccine gives you the flu.",
        "source_name": "provided source",
        "source_sha256": "13b95aaa1ef7d038b3aa9a3624745c285d186c807323a0240bc3143866d2fb8f"
      },
      "source": {
        "source_id": "S1",
        "name": "provided source",
        "sha256": "13b95aaa1ef7d038b3aa9a3624745c285d186c807323a0240bc3143866d2fb8f",
        "chars": 108,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "Getting a flu vaccine gives you the flu.",
          "verdict": "refuted",
          "reason": "A verified quotation states the same proposition with the opposite polarity.",
          "accepted_argument_ids": [
            "P-A1-S1-P1-13b95a"
          ],
          "struck_argument_ids": [
            "P-A1-S1-P1"
          ],
          "evidence_ids": [
            "S1-P1"
          ],
          "nearest": {
            "quote": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
            "coverage": 1.0,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 108
          },
          "what_would_change_it": "A source sentence asserting the same proposition would change this verdict."
        }
      ],
      "arguments": [
        {
          "argument_id": "P-A1-S1-P1-13b95a",
          "side": "prosecution",
          "atom_id": "A1",
          "relation": "contradicts",
          "evidence_id": "S1-P1",
          "source_name": "provided source",
          "quote": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus.",
          "quote_sha256": "13b95aaa1ef7d038b3aa9a3624745c285d186c807323a0240bc3143866d2fb8f",
          "char_start": 0,
          "char_end": 108,
          "rationale": "The source states the vaccine cannot cause influenza.",
          "status": "accepted",
          "strike_codes": [],
          "strike_reason": null,
          "checks": {
            "quote_exact": true,
            "relation": true,
            "subject": true,
            "population": true,
            "object": true,
            "endpoint": true,
            "quantity": true,
            "strength": true,
            "polarity": true
          },
          "coverage": 1.0
        },
        {
          "argument_id": "P-A1-S1-P1",
          "side": "prosecution",
          "atom_id": "A1",
          "relation": "unknown",
          "evidence_id": "S1-P1",
          "quote": "The flu vaccine contains live virus and causes influenza.",
          "status": "struck",
          "strike_codes": [
            "quote_not_found"
          ],
          "strike_reason": "quotation does not appear in the cited evidence",
          "checks": {
            "quote_exact": false
          },
          "coverage": 0.0,
          "rationale": "An adversarial fixture: this sentence is not in the source."
        }
      ],
      "summary": {
        "claims": 1,
        "supported": 0,
        "refuted": 1,
        "not_in_source": 0,
        "conflict": 0,
        "accepted_arguments": 1,
        "struck_arguments": 1
      },
      "receipt": {
        "run_id": "1b2ce9a68cc53b83",
        "generated_at": "2026-11-20T19:28:52.463160+00:00",
        "model": "adversarial fixture",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "demo_label": "ADVERSARIAL FIXTURE — one fabricated quotation is struck",
      "__source": "It is impossible to get influenza from the injected vaccine because the vaccine does not contain live virus."
    },
    "quantity": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "Adults need 150 minutes of moderate exercise per week.",
        "source_name": "live fixture",
        "source_sha256": "0c3d82c02ed2df30406e7b226f4b5cf3904e9604483142218c764c3a6580f9a3"
      },
      "source": {
        "source_id": "S1",
        "name": "live fixture",
        "sha256": "0c3d82c02ed2df30406e7b226f4b5cf3904e9604483142218c764c3a6580f9a3",
        "chars": 68,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "Adults need 150 minutes of moderate exercise per week.",
          "verdict": "not_in_source",
          "reason": "No verified quotation states this proposition in the supplied source.",
          "accepted_argument_ids": [],
          "struck_argument_ids": [],
          "evidence_ids": [],
          "nearest": {
            "quote": "Adults should get at least 60 minutes of moderate exercise per week.",
            "coverage": 0.6,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 68
          },
          "what_would_change_it": "A sentence, in this source, that states the same subject, quantity and strength as the claim would change this result."
        }
      ],
      "arguments": [],
      "summary": {
        "claims": 1,
        "supported": 0,
        "refuted": 0,
        "not_in_source": 1,
        "conflict": 0,
        "accepted_arguments": 0,
        "struck_arguments": 0,
        "ai_arguments": 0,
        "ai_accepted": 0,
        "ai_struck": 0,
        "rule_arguments": 0
      },
      "receipt": {
        "run_id": "2a78553f01fe3dd1",
        "generated_at": "2026-11-20T20:15:13.304381+00:00",
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [
        {
          "step": "advocates",
          "meta": {
            "prosecution": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 650,
              "usage": {
                "prompt_tokens": 423,
                "completion_tokens": 2,
                "total_tokens": 425
              },
              "role": "prosecution",
              "arguments": 0,
              "output_format": "array"
            },
            "defense": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 650,
              "usage": {
                "prompt_tokens": 422,
                "completion_tokens": 2,
                "total_tokens": 424
              },
              "role": "defense",
              "arguments": 0,
              "output_format": "array"
            },
            "available": true,
            "parallel": true
          }
        }
      ],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "__source": "Adults should get at least 60 minutes of moderate exercise per week.",
      "replay_mode": "live-run-recording",
      "demo_label": "RECORDED LIVE AI RUN · qwen2.5-1.5b-instruct-q4_k_m.gguf"
    },
    "population": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "Children need 150 minutes of moderate exercise per week.",
        "source_name": "live fixture",
        "source_sha256": "dd86c214d5ea3c52e3ac865d3c0af38f0f1d649ddbde6d890f14fb52c1676237"
      },
      "source": {
        "source_id": "S1",
        "name": "live fixture",
        "sha256": "dd86c214d5ea3c52e3ac865d3c0af38f0f1d649ddbde6d890f14fb52c1676237",
        "chars": 54,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "Children need 150 minutes of moderate exercise per week.",
          "verdict": "not_in_source",
          "reason": "No verified quotation states this proposition in the supplied source.",
          "accepted_argument_ids": [],
          "struck_argument_ids": [
            "P-A1-S1-P1-dd86c2"
          ],
          "evidence_ids": [],
          "nearest": {
            "quote": "Adults need 150 minutes of moderate exercise per week.",
            "coverage": 0.7778,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 54
          },
          "what_would_change_it": "A sentence, in this source, that states the same subject, quantity and strength as the claim would change this result."
        }
      ],
      "arguments": [
        {
          "argument_id": "P-A1-S1-P1-dd86c2",
          "side": "prosecution",
          "origin": "ai",
          "atom_id": "A1",
          "relation": "supports",
          "evidence_id": "S1-P1",
          "source_name": "live fixture",
          "quote": "Adults need 150 minutes of moderate exercise per week.",
          "quote_sha256": "dd86c214d5ea3c52e3ac865d3c0af38f0f1d649ddbde6d890f14fb52c1676237",
          "char_start": 0,
          "char_end": 54,
          "rationale": "The evidence directly contradicts the claim that children need 150 minutes of moderate exercise per week.",
          "status": "struck",
          "strike_codes": [
            "population_mismatch"
          ],
          "strike_reason": "quotation is about a different population",
          "checks": {
            "quote_exact": true,
            "relation": true,
            "subject": true,
            "population": false,
            "object": true,
            "endpoint": true,
            "quantity": true,
            "strength": true,
            "polarity": true
          },
          "coverage": 0.7778
        }
      ],
      "summary": {
        "claims": 1,
        "supported": 0,
        "refuted": 0,
        "not_in_source": 1,
        "conflict": 0,
        "accepted_arguments": 0,
        "struck_arguments": 1,
        "ai_arguments": 1,
        "ai_accepted": 0,
        "ai_struck": 1,
        "rule_arguments": 0
      },
      "receipt": {
        "run_id": "7f2f5b42521e85da",
        "generated_at": "2026-11-20T20:15:17.821323+00:00",
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [
        {
          "step": "advocates",
          "meta": {
            "prosecution": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 4504,
              "usage": {
                "prompt_tokens": 420,
                "completion_tokens": 65,
                "total_tokens": 485
              },
              "role": "prosecution",
              "arguments": 1,
              "output_format": "array"
            },
            "defense": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 631,
              "usage": {
                "prompt_tokens": 419,
                "completion_tokens": 2,
                "total_tokens": 421
              },
              "role": "defense",
              "arguments": 0,
              "output_format": "array"
            },
            "available": true,
            "parallel": true
          }
        }
      ],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "__source": "Adults need 150 minutes of moderate exercise per week.",
      "replay_mode": "live-run-recording",
      "demo_label": "RECORDED LIVE AI RUN · qwen2.5-1.5b-instruct-q4_k_m.gguf"
    },
    "relation": {
      "mode": "court",
      "ai_mode": "ai",
      "input": {
        "claim": "Vitamin C cures the common cold.",
        "source_name": "live fixture",
        "source_sha256": "967b6f1e9688acbc55d1909320d2387f92815715d8caaa02997c3fc253583558"
      },
      "source": {
        "source_id": "S1",
        "name": "live fixture",
        "sha256": "967b6f1e9688acbc55d1909320d2387f92815715d8caaa02997c3fc253583558",
        "chars": 43,
        "sentences": 1
      },
      "atoms": [
        {
          "atom_id": "A1",
          "claim": "Vitamin C cures the common cold.",
          "verdict": "not_in_source",
          "reason": "No verified quotation states this proposition in the supplied source.",
          "accepted_argument_ids": [],
          "struck_argument_ids": [
            "P-A1-S1-P1-967b6f"
          ],
          "evidence_ids": [],
          "nearest": {
            "quote": "Vitamin C does not prevent the common cold.",
            "coverage": 0.6,
            "evidence_id": "S1-P1",
            "char_start": 0,
            "char_end": 43
          },
          "what_would_change_it": "A sentence, in this source, that states the same subject, quantity and strength as the claim would change this result."
        }
      ],
      "arguments": [
        {
          "argument_id": "P-A1-S1-P1-967b6f",
          "side": "prosecution",
          "origin": "ai",
          "atom_id": "A1",
          "relation": "contradicts",
          "evidence_id": "S1-P1",
          "source_name": "live fixture",
          "quote": "Vitamin C does not prevent the common cold.",
          "quote_sha256": "967b6f1e9688acbc55d1909320d2387f92815715d8caaa02997c3fc253583558",
          "char_start": 0,
          "char_end": 43,
          "rationale": "The evidence directly contradicts the claim that Vitamin C cures the common cold.",
          "status": "struck",
          "strike_codes": [
            "endpoint_mismatch",
            "low_coverage",
            "relation_mismatch"
          ],
          "strike_reason": "quotation answers a different endpoint",
          "checks": {
            "quote_exact": true,
            "relation": false,
            "subject": true,
            "population": true,
            "object": true,
            "endpoint": false,
            "quantity": true,
            "strength": true,
            "polarity": true
          },
          "coverage": 0.6
        }
      ],
      "summary": {
        "claims": 1,
        "supported": 0,
        "refuted": 0,
        "not_in_source": 1,
        "conflict": 0,
        "accepted_arguments": 0,
        "struck_arguments": 1,
        "ai_arguments": 1,
        "ai_accepted": 0,
        "ai_struck": 1,
        "rule_arguments": 0
      },
      "receipt": {
        "run_id": "1f3bee9b3025de1b",
        "generated_at": "2026-11-20T20:15:21.842939+00:00",
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "engine": "deterministic judge + AI advocates"
      },
      "trace": [
        {
          "step": "advocates",
          "meta": {
            "prosecution": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 4009,
              "usage": {
                "prompt_tokens": 412,
                "completion_tokens": 56,
                "total_tokens": 468
              },
              "role": "prosecution",
              "arguments": 1,
              "output_format": "array"
            },
            "defense": {
              "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
              "provider": "local-llama.cpp",
              "latency_ms": 629,
              "usage": {
                "prompt_tokens": 411,
                "completion_tokens": 2,
                "total_tokens": 413
              },
              "role": "defense",
              "arguments": 0,
              "output_format": "array"
            },
            "available": true,
            "parallel": true
          }
        }
      ],
      "disclaimer": "The court decides whether the supplied source states the claim. It is not an authoritative fact-check, and `not_in_source` is a finding about this source, not a claim that the statement is false.",
      "__source": "Vitamin C does not prevent the common cold.",
      "replay_mode": "live-run-recording",
      "demo_label": "RECORDED LIVE AI RUN · qwen2.5-1.5b-instruct-q4_k_m.gguf"
    }
  }
};
