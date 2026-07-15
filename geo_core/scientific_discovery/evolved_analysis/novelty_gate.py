"""novelty_gate.py — Gate 2 of the two-gate EVALUATE: is a candidate scientific
claim ALREADY in the literature?

This is the "do not simply repeat things we already know from textbooks or the
scientific literature (incl. arXiv)" gate that the prime directive requires for
open-ended Eureka search (design doc §5.3).

How it works
------------
1. Retrieve the most similar papers from arXiv (primary; no API key needed) and,
   if reachable, Semantic Scholar — for terms extracted from the claim.
2. Ask the LLM, GROUNDED ONLY in the retrieved abstracts, whether the SPECIFIC
   claim is stated or directly implied by any of them. The LLM must cite which
   abstract entails it, or say "none".

Honesty guarantees
------------------
- The entailment judgment is constrained to retrieved text — the LLM is given the
  abstracts and asked to point at the entailing one. It is NOT a free-form
  "is this novel?" judgement (that would re-introduce the circular LLM-as-judge
  fiction problem this whole effort removes).
- Retrieval/judge failures are CONSERVATIVE: if novelty cannot be checked, the
  claim is NOT promoted as a novel Eureka. It returns status ``retrieval-failed``
  / ``judge-failed`` with ``novel=False``.
- Retrieved papers are persisted to a provenance manifest; nothing is fabricated.

Caching: results are keyed by a normalized claim hash in
``~/.geodisc_persistent/evolved_programs/novelty_cache.json`` so repeated claims do
not re-hit the APIs.

Public API: ``check_novelty(claim, min_effect_description="") -> NoveltyResult``.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
_GATEWAY = None  # cached llm gateway (loaded decoupled from geo_core/__init__)


def _get_gateway():
    """Return the canonical LLM gateway via the shared decoupled loader
    (see ``_llm.py``). Returns None on failure."""
    global _GATEWAY
    if _GATEWAY is not None:
        return _GATEWAY
    try:
        from ._llm import get_gateway as _gg
        _GATEWAY = _gg()
        return _GATEWAY
    except Exception as e:
        logger.warning("[novelty] could not load LLM gateway: %s", e)
        return None

CACHE_PATH = Path.home() / ".geodisc_persistent" / "evolved_programs" / "novelty_cache.json"
ARXIV_ENDPOINT = "https://export.arxiv.org/api/query"
S2_ENDPOINT = "https://api.semanticscholar.org/graph/v1/paper/search"
_RATE_SLEEP = 4.0  # arXiv asks for >=3s between calls


@dataclass
class Paper:
    source: str        # "arxiv" | "s2"
    title: str
    abstract: str
    identifier: str    # arxiv id or s2 paperId
    year: Optional[str] = None


@dataclass
class NoveltyResult:
    novel: bool
    status: str        # novel | known | retrieval-failed | judge-failed
    claim: str
    entailed_by: Optional[Paper] = None
    n_retrieved: int = 0
    reasoning: str = ""
    retrieved: List[Paper] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.entailed_by:
            d["entailed_by"] = asdict(self.entailed_by)
        return d


# --------------------------------------------------------------------------- #
# geochemistry domain-relevance guard (§7.4: off-topic retrieval != novel)     #
# --------------------------------------------------------------------------- #
# Geochemistry journals are poorly indexed on arXiv/Semantic Scholar, so
# retrieval for a geochem claim often returns OFF-TOPIC papers (stats, finance,
# ML...). Running the entailment judge on those yields "none entails" -> a FALSE
# "novel" verdict for textbook relations. The guard requires retrieval to
# surface at least one on-domain paper before "novel" can be declared; otherwise
# it returns retrieval-failed (conservative — never promote on bad retrieval).
GEOCHEM_DOMAIN_TERMS = {
    # major oxides
    "sio2", "tio2", "al2o3", "fe2o3", "feo", "feot", "mgo", "cao", "mno",
    "na2o", "k2o", "p2o5",
    # rocks
    "basalt", "basaltic", "granite", "granitic", "andesite", "andesitic",
    "rhyolite", "dacite", "peridotite", "gabbro", "diorite", "dolerite",
    "shale", "sandstone", "siltstone", "chert", "limestone", "dolostone",
    "marble", "schist", "gneiss", "quartzite", "tuff", "breccia",
    "conglomerate", "evaporite",
    # rock classes / series
    "tholeiitic", "calc-alkaline", "calcalkaline", "alkaline", "subalkaline",
    "ultramafic", "mafic", "felsic", "igneous", "metamorphic", "sedimentary",
    "volcanic", "plutonic", "pyroclastic",
    # minerals
    "quartz", "feldspar", "olivine", "pyroxene", "plagioclase", "amphibole",
    "biotite", "muscovite", "calcite", "dolomite", "pyrite", "hematite",
    "magnetite", "ilmenite", "apatite", "zircon", "monazite", "garnet",
    "zeolite", "smectite", "illite", "kaolinite", "chlorite",
    # geochemistry / petrology vocabulary
    "geochem", "geochemistry", "whole-rock", "wholerock", "trace-element",
    "rare-earth", "major-element", "isotope", "isotopic", "fractionat",
    "crystalli", "partial melting", "serpentin", "hydrothermal", "metasomat",
    "diagenesis", "weathering", "petrolog", "petrograph", "mineralog",
    "magma", "lava", "tephra", "mantle", "crustal", "stratigraph",
    "depositional", "provenance", "sedimentolog",
    # classic diagrams / classifications (textbook markers)
    "harker", "fenner", "mg#", "mg-number", "bowen", "silica saturation",
}


def _domain_terms_in(text: str) -> set:
    """Which geochemistry domain terms appear in ``text`` (lowercased)."""
    if not text:
        return set()
    t = text.lower()
    return {term for term in GEOCHEM_DOMAIN_TERMS if term in t}


def _filter_relevant(papers: List[Paper]) -> List[Paper]:
    """Keep only papers that are themselves geochemistry / Earth-science
    (contain at least one domain term). Off-topic retrievals (finance / stats /
    ML papers) are dropped so the entailment judge is never fed irrelevant
    context that would yield a false 'novel'."""
    return [p for p in papers
            if _domain_terms_in((p.title or "") + " " + (p.abstract or ""))]


# --------------------------------------------------------------------------- #
# retrieval                                                                    #
# --------------------------------------------------------------------------- #
def _http_get(url: str, timeout: int = 25) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GEODISC-novelty-gate/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.debug("[novelty] GET failed %s: %s", url[:80], e)
        return None


def retrieve_arxiv(query: str, max_results: int = 5) -> List[Paper]:
    """Query arXiv Atom API. Returns papers (title+abstract). Rate-limited."""
    q = urllib.parse.quote(query)
    url = (f"{ARXIV_ENDPOINT}?search_query=all:{q}&start=0&max_results={max_results}"
           f"&sortBy=relevance")
    raw = _http_get(url)
    time.sleep(_RATE_SLEEP)  # respect arXiv's >=3s guideline
    if not raw:
        return []
    papers: List[Paper] = []
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(raw)
        for e in root.findall("a:entry", ns):
            title = (e.find("a:title", ns).text or "").strip().replace("\n", " ")
            summary = (e.find("a:summary", ns).text or "").strip().replace("\n", " ")
            arxiv_id = (e.find("a:id", ns).text or "").rsplit("/", 1)[-1]
            published = (e.find("a:published", ns).text or "")[:4]
            papers.append(Paper("arxiv", title, summary, arxiv_id, published))
    except Exception as e:
        logger.warning("[novelty] arXiv parse failed: %s", e)
    return papers


def retrieve_s2(query: str, max_results: int = 5) -> List[Paper]:
    """Query Semantic Scholar (optional; often rate-limited without a key)."""
    q = urllib.parse.quote(query)
    fields = "title,abstract,year,externalIds"
    url = (f"{S2_ENDPOINT}?query={q}&limit={max_results}&fields={fields}")
    raw = _http_get(url)
    time.sleep(_RATE_SLEEP)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("code") == 429:
            return []  # rate-limited; silently skip
        papers = []
        for item in data.get("data", []) or []:
            papers.append(Paper(
                "s2",
                (item.get("title") or "").strip(),
                (item.get("abstract") or "").strip(),
                item.get("paperId", ""),
                str(item.get("year") or "")[:4]))
        return papers
    except Exception as e:
        logger.debug("[novelty] s2 parse failed: %s", e)
        return []


def _extract_query(claim: str) -> str:
    """Reduce a claim to arXiv-searchable terms, keeping DOMAIN NOUNS and
    dropping generic connective/statistical words.

    Earlier this kept the first 6 non-stopwords, which for a claim like
    "...galaxy's g-r color is positively correlated with ... redshift" yielded
    "sdss sample galaxy color positively correlated" — dropping 'redshift', the
    crucial term, so retrieval never fetched the photo-z papers that would entail
    it. We now drop generic stats words (correlated, significant, relation, …)
    and keep up to 8 domain-relevant terms.
    """
    stop = {"the", "a", "an", "of", "in", "with", "and", "to", "is", "are",
            "that", "this", "for", "on", "at", "by", "be", "from", "as", "it",
            "we", "show", "have", "has", "than", "more", "less", "very",
            "between", "into", "its", "their", "was", "were", "our", "these",
            "those", "such", "also", "using", "used", "use",
            # generic statistical / framing words — not useful as search terms
            "correlated", "correlation", "correlates", "positively", "negatively",
            "significant", "significantly", "strongly", "weakly", "relation",
            "relationship", "associated", "associate", "sample", "samples",
            "result", "results", "found", "find", "report", "reported",
            "higher", "lower", "greater", "fewer", "increase", "decrease",
            "evidence", "indicates", "indicate", "suggests", "suggest"}
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]+", claim.lower())
    terms = [w for w in words if w not in stop and len(w) > 2]
    # de-dup preserving order, keep up to 8
    seen, kept = set(), []
    for w in terms:
        if w not in seen:
            seen.add(w)
            kept.append(w)
    return " ".join(kept[:8]) or claim[:60]


# --------------------------------------------------------------------------- #
# the grounded entailment judge                                                #
# --------------------------------------------------------------------------- #
def _judge_known(claim: str, papers: List[Paper]) -> tuple[bool, Optional[Paper], str, str]:
    """Ask the LLM whether ``claim`` is ALREADY-KNOWN (not a new discovery).

    A claim is already-known if EITHER:
      (a) one of the retrieved abstracts states or directly implies it (cite it), OR
      (b) it is a well-established foundational/textbook result the field treats as
          given (e.g. the MgO–SiO2 Harker fractionation trend, FeOt enrichment
          in tholeiitic basalts / the Fenner trend, total-alkali–silica (TAS)
          classification, Mg#, silica saturation, Bowen's reaction series).

    (a) is grounded in retrieved text; (b) is a domain-knowledge judgement. Both
    are auditable via the returned ``reason_label`` and ``reasoning``. Be
    conservative: borderline claims lean toward 'known' (we would rather drop a
    marginal result than emit a textbook restatement as a 'discovery').

    Returns (known, entailing_paper, reason_label, reasoning). reason_label is
    'entailed' | 'foundational' | 'novel'. On judge failure returns
    (False, None, '', '') — caller treats that conservatively (judge-failed)."""
    if not papers:
        return False, None, "", ""
    gw = _get_gateway()
    if gw is None:
        return False, None, "", ""
    abstracts = "\n\n".join(
        f"[{i}] {p.title} ({p.year})\n{p.abstract[:900]}"
        for i, p in enumerate(papers))
    system = (
        "You are a strict GEOCHEMISTRY novelty auditor. A candidate scientific "
        "CLAIM is ALREADY-KNOWN (not a new discovery) if EITHER (a) one of the "
        "RETRIEVED ABSTRACTS states or directly implies it — cite that abstract's "
        "index; OR (b) it is a well-established foundational / textbook result "
        "that the field treats as given: the MgO-SiO2 Harker fractionation trend, "
        "FeOt enrichment in tholeiitic basalts (the Fenner/AFM trend), total-"
        "alkali-silica (TAS) classification, Fe-Mg covariation, Mg#, silica "
        "saturation, Bowen's reaction series, standard element partitioning, "
        "Walther's law, index-fossil stratigraphy, etc. Use retrieved text for "
        "(a) and standard geochemistry knowledge for (b). When uncertain, lean "
        "toward already-known — a borderline claim should not be advertised as a "
        "new discovery.")
    user = (f"CANDIDATE CLAIM:\n{claim}\n\nRETRIEVED ABSTRACTS:\n{abstracts}\n\n"
            "Respond with ONLY JSON: "
            '{"known": true|false, "reason": "entailed"|"foundational"|"novel", '
            '"by_abstract": <int|null>, "reasoning": "<one sentence>"}')
    try:
        text, _ = gw.complete(
            system=system, messages=[{"role": "user", "content": user}],
            max_tokens=300)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return False, None, "", ""
        verdict = json.loads(m.group(0))
        known = bool(verdict.get("known"))
        label = str(verdict.get("reason", ""))[:24]
        idx = verdict.get("by_abstract")
        reasoning = str(verdict.get("reasoning", ""))[:300]
        entailing = None
        if known and isinstance(idx, int) and 0 <= idx < len(papers):
            entailing = papers[idx]
        return known, entailing, label, reasoning
    except Exception as e:
        logger.warning("[novelty] judge failed: %s", e)
        return False, None, "", ""


# --------------------------------------------------------------------------- #
# caching                                                                      #
# --------------------------------------------------------------------------- #
def _cache_key(claim: str) -> str:
    norm = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", " ", claim.lower())).strip()
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


def _load_cache() -> dict:
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=2, default=str))
    except Exception as e:
        logger.debug("[novelty] cache save failed: %s", e)


# --------------------------------------------------------------------------- #
# public entry point                                                           #
# --------------------------------------------------------------------------- #
def check_novelty(claim: str, use_s2: bool = True, force: bool = False) -> NoveltyResult:
    """Gate 2: return whether ``claim`` is novel (not in the literature).

    Conservative on failure: retrieval- or judge-failures are NOT promoted as
    novel (``novel=False`` with a ``status`` explaining why).
    """
    if not claim or not claim.strip():
        return NoveltyResult(False, "judge-failed", claim, reasoning="empty claim")

    key = _cache_key(claim)
    cache = _load_cache()
    if not force and key in cache:
        c = cache[key]
        return NoveltyResult(c.get("novel", False), c.get("status", "?"),
                             claim, None, c.get("n_retrieved", 0),
                             c.get("reasoning", ""))

    query = _extract_query(claim)
    logger.info("[novelty] retrieving for claim (query=%r)", query)
    papers = retrieve_arxiv(query, max_results=5)
    if use_s2:
        papers += retrieve_s2(query, max_results=5)
    # de-dup by title
    seen = set()
    deduped = []
    for p in papers:
        k = p.title.lower()[:80]
        if k and k not in seen:
            seen.add(k)
            deduped.append(p)
    papers = deduped[:8]

    if not papers:
        res = NoveltyResult(False, "retrieval-failed", claim, n_retrieved=0,
                            reasoning="no papers retrieved; novelty unverified")
        cache[key] = res.to_dict()
        _save_cache(cache)
        return res

    # §7.4 domain-relevance guard: geochemistry is poorly indexed on arXiv/S2,
    # so retrieval for a geochem claim often returns off-topic papers. If this
    # is a geochem claim but NO retrieved paper is on-domain, the retrieval is
    # off-topic — do NOT judge on irrelevant abstracts (that would falsely mark
    # textbook relations novel). Conservative: retrieval-failed.
    claim_terms = _domain_terms_in(claim)
    if claim_terms:
        relevant = _filter_relevant(papers)
        if not relevant:
            res = NoveltyResult(
                False, "retrieval-failed", claim, n_retrieved=len(papers),
                reasoning=(f"retrieved {len(papers)} paper(s) but none are "
                           "geochemistry-relevant (off-topic); novelty unverified"))
            cache[key] = res.to_dict()
            _save_cache(cache)
            logger.info("[novelty] retrieval-failed (off-topic) — %s", claim[:60])
            return res
        judge_papers = relevant
    else:
        judge_papers = papers  # claim is not clearly geochem; guard N/A

    known, entailing, label, reasoning = _judge_known(claim, judge_papers)
    if not label and not reasoning:
        # judge itself failed -> conservative
        res = NoveltyResult(False, "judge-failed", claim, n_retrieved=len(judge_papers),
                            reasoning="LLM novelty judge unavailable")
        cache[key] = res.to_dict()
        _save_cache(cache)
        return res

    if known:
        reason = (f"{label}: {reasoning}") if label else reasoning
        res = NoveltyResult(False, "known", claim, entailed_by=entailing,
                            n_retrieved=len(judge_papers), reasoning=reason,
                            retrieved=judge_papers)
    else:
        res = NoveltyResult(True, "novel", claim, n_retrieved=len(judge_papers),
                            reasoning=reasoning, retrieved=judge_papers)
    cache[key] = res.to_dict()
    _save_cache(cache)
    logger.info("[novelty] %s — %s (n=%d)", res.status, claim[:60], len(papers))
    return res


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    claim = " ".join(sys.argv[1:]) or "Whole-rock SiO2 is negatively correlated with MgO (the Harker fractionation trend)"
    r = check_novelty(claim)
    print(json.dumps(r.to_dict(), indent=2)[:1500])
