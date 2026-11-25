"""Executable invariants for the three core citation functions.

Each test pins a fixed input to a fixed output. If any of these drift, the
receipt that Claim Autopsy produces for a claim is no longer the same receipt.
"""

import unittest

from core import court, decompose, evidence, negation

SOURCE = "Alpha is true. Beta is false."


class TestCoreInvariants(unittest.TestCase):
    def test_build_evidence_offsets_and_hashes_are_stable(self):
        evidence = court.build_evidence(SOURCE, "doc")

        assert evidence["source"]["chars"] == 29
        assert evidence["source"]["sentences"] == 2
        assert evidence["source"]["sha256"] == (
            "16fb4f1a6afdd6686a56ae787091a31ab210861a854bf308a13e4cc01790a43c"
        )

        first, second = evidence["sentences"]
        assert (first["evidence_id"], first["char_start"], first["char_end"]) == (
            "S1-P1", 0, 14,
        )
        assert first["quote"] == "Alpha is true."
        assert (second["evidence_id"], second["char_start"], second["char_end"]) == (
            "S1-P2", 15, 29,
        )
        assert second["quote"] == "Beta is false."
        assert second["quote_sha256"] == (
            "8810da1dc43d3e0925e5e254def7195755ee1f277d38da40e8cbd1eba31255ca"
        )

    def test_quote_in_accepts_only_exact_or_whitespace_normalised_quote(self):
        source = "Alpha is true."

        assert court._quote_in("Alpha   is true", source) == (True, "Alpha is true")
        assert court._quote_in("Alpha is false", source) == (False, None)
        assert court._quote_in("Alpha is true", source) == (True, "Alpha is true")

    def test_judge_quote_self_quote_is_supporting_and_strike_free(self):
        evidence = court.build_evidence(SOURCE, "doc")

        result = court.judge_quote("Alpha is true", "Alpha is true.", evidence["idf"])

        assert result["ok"] is True
        assert result["coverage"] == 1.0
        assert result["strike_codes"] == []
        assert result["direction"] == "supports"
        assert result["checks"] == {
            "quote_exact": True,
            "relation": True,
            "subject": True,
            "population": True,
            "object": True,
            "endpoint": True,
            "quantity": True,
            "strength": True,
            "polarity": True,
        }

    def test_negation_detect_marks_polarity_flip(self):
        result = negation.detect("Alpha is not true")

        assert result["original"] == "Alpha is not true"
        assert result["normalized"] == "Alpha true"
        assert result["markers"] == ["is not"]
        assert result["count"] == 1
        assert result["flip"] is True
        assert result["uncertain"] is False

    def test_quantities_extracts_percent_value(self):
        assert evidence.quantities("GDP grew 3.4% in 2020") == {"%": {3.4}}

    def test_same_proposition_is_true_only_for_same_proposition(self):
        assert evidence.same_proposition("Alpha is true", "Alpha is true") is True
        assert evidence.same_proposition("Alpha is true", "Alpha is false") is False

    def test_rule_split_splits_conjunction_into_two_atoms(self):
        assert decompose.rule_split("Alpha is true and Beta is false") == [
            "Alpha is true",
            "Beta is false",
        ]

    def test_word_count_counts_alphanumerics_not_punctuation(self):
        assert court._word_count("COVID-19 reduced GDP by 3.4% in 2020.") == 9

    def test_term_in_matches_whole_token_only(self):
        assert court._term_in("cat", "The cat sat") is True
        assert court._term_in("cat", "The concatenate function") is False

    def test_norm_quote_collapses_whitespace(self):
        assert court._norm_quote("  Alpha\t is\n true  ") == "Alpha is true"


if __name__ == "__main__":
    unittest.main()
