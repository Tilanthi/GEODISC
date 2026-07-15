"""Tests for the Gate-2 geochemistry domain-relevance guard (the §7.4 fix).

Root cause being fixed: for geochemistry claims, arXiv/Semantic-Scholar retrieval
often returns OFF-TOPIC papers (geochem journals are poorly indexed there). The
old Gate 2 then ran its entailment judge on those irrelevant abstracts, found
"none entails", and FALSELY marked textbook relations (e.g. tholeiitic
Fe-enrichment) as novel — emitting false discoveries.

The fix: only declare "novel" when retrieval surfaced papers that are actually
on-domain for the claim. If a geochem claim retrieves no geochem-relevant paper,
return ``retrieval-failed`` (conservative — never promote on bad retrieval).

Run: python3 geo_core/tests/test_novelty_gate.py   (also pytest-discoverable)
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from geo_core.scientific_discovery.evolved_analysis.novelty_gate import (  # noqa: E402
    Paper, _domain_terms_in, _filter_relevant, _openalex_abstract,
    retrieve_openalex, _matches_textbook_blocklist)


# --- domain-term extraction -------------------------------------------------- #
def test_domain_terms_in_geochem_claim():
    terms = _domain_terms_in(
        "Iron enrichment (FeOt) in tholeiitic basalts anti-correlates with SiO2")
    assert "tholeiitic" in terms
    assert any(t in terms for t in ("feot", "feo"))
    assert "sio2" in terms or "basalt" in terms


def test_domain_terms_in_non_geochem_is_empty():
    """A market-data / statistics text must have NO geochem domain terms,
    so the relevance guard correctly treats its papers as off-topic."""
    terms = _domain_terms_in(
        "Statistical enrichment of trading signals in market data analysis")
    assert terms == set(), f"unexpected geochem terms in market text: {terms}"


# --- relevance filtering ----------------------------------------------------- #
def test_filter_relevant_keeps_geochem_drops_offtopic():
    papers = [
        Paper("arxiv", "Statistical enrichment in market trading data",
              "We analyze market-data enrichment of trading signals.", "m1"),
        Paper("arxiv", "Tholeiitic basalt geochemistry and the Fenner trend",
              "FeOt enrichment in tholeiitic basalts follows the Fenner trend.",
              "g1"),
    ]
    rel = _filter_relevant(papers)
    assert len(rel) == 1, f"expected 1 relevant, got {len(rel)}"
    assert "basalt" in rel[0].title.lower() or "tholeiitic" in rel[0].title.lower()


def test_filter_relevant_all_offtopic_returns_empty():
    papers = [
        Paper("arxiv", "Market data enrichment", "trading signal enrichment.", "m1"),
        Paper("s2", "Statistical enrichment analysis", "enrichment of survey data.", "m2"),
    ]
    assert _filter_relevant(papers) == []


# --- the off-topic verdict (no network: retrieval monkeypatched) ------------- #
def test_offtopic_retrieval_is_not_marked_novel():
    """THE fix: a geochem claim whose retrieval returns only off-topic papers
    must come back retrieval-failed (novel=False), NOT novel — so no false
    discovery is emitted. (All three sources are mocked off-topic/empty.)"""
    from geo_core.scientific_discovery.evolved_analysis import novelty_gate as ng

    orig_oa, orig_arxiv, orig_s2 = ng.retrieve_openalex, ng.retrieve_arxiv, ng.retrieve_s2
    ng.retrieve_openalex = lambda q, max_results=5: []   # no geochem source hit
    ng.retrieve_arxiv = lambda q, max_results=5: [
        Paper("arxiv", "Market data enrichment of trading signals",
              "Statistical enrichment analysis of financial market data.", "m1")]
    ng.retrieve_s2 = lambda q, max_results=5: []
    try:
        r = ng.check_novelty(
            "FeOt enrichment in tholeiitic basalts shows a distinct trend",
            force=True)
        assert r.novel is False, "off-topic retrieval must NOT be marked novel"
        assert r.status == "retrieval-failed", f"expected retrieval-failed, got {r.status}"
    finally:
        ng.retrieve_openalex, ng.retrieve_arxiv, ng.retrieve_s2 = orig_oa, orig_arxiv, orig_s2


# --- OpenAlex geochemistry literature source -------------------------------- #
def test_openalex_abstract_reconstruction():
    """OpenAlex stores abstracts as an inverted index {word: [positions]}."""
    inv = {"whole": [0], "rock": [1], "SiO2": [2], "correlates": [3], "MgO": [4]}
    assert _openalex_abstract(inv) == "whole rock SiO2 correlates MgO"
    assert _openalex_abstract(None) == ""
    assert _openalex_abstract({}) == ""


def test_retrieve_openalex_parses_and_keeps_geochem():
    """retrieve_openalex must parse the OpenAlex JSON and return real Paper
    objects (title + reconstructed abstract). (Network is mocked.)"""
    from geo_core.scientific_discovery.evolved_analysis import novelty_gate as ng
    sample = {"results": [
        {"display_name": "Tholeiitic basalt FeOt enrichment (Fenner trend)",
         "abstract_inverted_index": {"FeOt": [0], "enrichment": [1], "tholeiitic": [2]},
         "concepts": [{"display_name": "Geochemistry", "score": 0.8}],
         "primary_location": {"source": {"display_name": "Journal of Petrology"}},
         "publication_year": 1995, "id": "W123"},
    ]}
    orig = ng._http_get
    ng._http_get = lambda url, timeout=25: json.dumps(sample)
    try:
        papers = ng.retrieve_openalex("tholeiitic basalt iron", max_results=5)
        assert len(papers) == 1
        assert "tholeiitic" in papers[0].title.lower()
        assert papers[0].abstract == "FeOt enrichment tholeiitic"
        assert papers[0].year == "1995"
    finally:
        ng._http_get = orig


# --- Phase 1: textbook blocklist (deterministic Gate-2 fast-path) ------------ #
def test_blocklist_matches_textbook_name():
    assert _matches_textbook_blocklist("Whole-rock SiO2 vs MgO follows the Harker trend") is not None
    assert _matches_textbook_blocklist("Rocks plot on the TAS diagram by silica vs alkali") is not None


def test_blocklist_matches_canonical_oxide_pair():
    # a SIMPLE pairwise oxide statement -> matched (textbook)
    m = _matches_textbook_blocklist("SiO2 is negatively correlated with MgO in basalts")
    assert m is not None


def test_blocklist_does_not_match_partial_correlation():
    # a PARTIAL/residual relation mentioning SiO2+MgO must NOT be blocklisted
    # (it may be genuinely novel) -- let the judge decide. Conservative.
    assert _matches_textbook_blocklist(
        "partial correlation of SiO2 and MgO after controlling for FeO") is None
    assert _matches_textbook_blocklist(
        "residual variation of MgO after removing the SiO2 fractionation trend") is None


def test_blocklist_does_not_match_trace_novelty():
    # trace-element relations are the widened niche -- NOT blocklisted (judge handles)
    assert _matches_textbook_blocklist(
        "Zr/Nb ratio correlates with La/Ce among arc basalts") is None


def test_blocklist_fast_path_short_circuits_retrieval():
    """A blocklisted claim returns 'known' with NO retrieval (deterministic)."""
    from geo_core.scientific_discovery.evolved_analysis import novelty_gate as ng
    called = {"yes": False}
    def _boom(q, max_results=5):
        called["yes"] = True
        return []
    o_oa, o_ax, o_s2 = ng.retrieve_openalex, ng.retrieve_arxiv, ng.retrieve_s2
    ng.retrieve_openalex, ng.retrieve_arxiv, ng.retrieve_s2 = _boom, _boom, _boom
    try:
        r = ng.check_novelty("SiO2 negatively correlates with MgO (Harker trend)", force=True)
        assert r.novel is False and r.status == "known"
        assert called["yes"] is False           # retrieval never ran
        assert "blocklist" in (r.reasoning or "").lower()
    finally:
        ng.retrieve_openalex, ng.retrieve_arxiv, ng.retrieve_s2 = o_oa, o_ax, o_s2


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
