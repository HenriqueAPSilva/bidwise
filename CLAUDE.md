# CLAUDE.md — BidWise

## Project Overview
BidWise is a Streamlit web app that recommends the optimal reverse auction format and parameters for corporate buyers, based on official Coupa platform rules and auction theory. Built by Henrique Silva (7+ years in strategic sourcing, 90+ reverse auctions at Vale S.A. and ArcelorMittal Brasil).

**Live URL:** `bidwise.streamlit.app`
**Repo:** `HenriqueAPSilva/bidwise`
**Stack:** Python 3.11+, Streamlit, Anthropic SDK (Claude Sonnet), ReportLab, Pandas, Matplotlib
**Deploy:** GitHub (public) → Streamlit Cloud. API key in Streamlit secrets. Users access for free.

---

## Architecture

```
bidwise/
├── app.py              # Streamlit UI (main entry point)
├── motor.py            # Recommendation engine (pure logic, no dependencies)
├── simulador.py        # Supplier behavior simulation (pure logic → Claude API narrative)
├── prompt_engine.py    # Structured prompts for Claude API
├── config.py           # Loads API key from env/secrets
├── exportador.py       # PDF report generation (ReportLab)
├── i18n.py             # Bilingual support (EN/PT-BR) — v1.1
├── analytics.py        # Plausible Analytics integration
├── requirements.txt
├── .gitignore
├── CLAUDE.md
└── README.md
```

**Design principles:**
- `motor.py` is the heart — deterministic, auditable, zero external dependencies
- Claude API is an amplifier, not a crutch — used only for narrative generation in `simulador.py` and `prompt_engine.py`
- Architecture must support future expansion beyond reverse auctions (modular, not monolithic)

---

## Coupa Reverse Auction Formats (Official Rules)

### English Reverse — Full visibility (ranking + thermometer)
- Suppliers compete freely by reducing prices
- Each supplier sees their ranking position AND a hot/cold thermometer indicating proximity to best bid
- Does NOT see exact competitor values — only relative position
- Mandatory minimum decrement configured by buyer
- Configurable auto-extension in final minutes
- Lowest bid at end of time wins
- Maximum psychological competitive pressure

### English Reverse — Reduced visibility (ranking only)
- Identical to above but supplier sees ONLY ranking position, no thermometer
- Reduces psychological urgency — supplier knows if winning/losing but not "by how much"
- Recommended when moderate risk of excessive reactive behavior

### Dutch Reverse (clock auction — closest to sealed bid)
- Buyer sets INITIAL LOW price (below expected purchase price)
- Price RISES continuously by fixed amount at each time interval
- FIRST supplier to accept the called price wins immediately
- Auction ends on first acceptance — no further competition
- Suppliers see NO competitor activity
- Maximum opacity format
- Buyer fully controls the pace

### Japanese Reverse (clock auction — progressive elimination)
- Buyer sets INITIAL HIGH price (above expected purchase price)
- Price decreases by fixed value/percentage each round
- Supplier must actively accept each round's price to remain — omission = elimination
- Non-acceptors are permanently eliminated
- LAST active participant wins
- Suppliers see round number and current price value
- More efficient than English for large fields — eliminates passivity

### When NOT to auction
- Single supplier or duopoly with no technical substitute
- Highly strategic item with critical supplier for operational continuity
- Long-term relationship that shouldn't be exposed to public price pressure
- Restrictive technical specification only one supplier fully meets

---

## Recommendation Business Rules

### Format scoring (motor.py)
Each format has a scoring function based on weighted input variables. The format with the highest score wins. Key drivers:

| Factor | English Full | English Reduced | Dutch | Japanese |
|--------|-------------|----------------|-------|----------|
| Sweet spot # suppliers | 4+ | 3-5 | 2-3 | 5+ |
| Best commoditization | High | Medium | Any | High |
| Best behavior | Competitive | Moderate | Conservative | Moderate (heterogeneous) |
| Collusion risk response | Penalized | Neutral | Rewarded (opacity) | Neutral |
| Urgency response | Low/Medium | Low/Medium | High (first accept) | Medium |

### Parameter calculation formulas

**Minimum decrement:**
- Spread > 20%: 1.5%–3.0%
- Spread 10%–20%: 0.8%–1.5%
- Spread < 10%: 0.3%–0.8%
- Behavior adjustment: Competitive → top of range, Conservative → bottom

**Opening price:**
- English: 5% below best proposal
- Japanese: near average of proposals (needs room to descend)
- Dutch: well below best; climb rate calibrated by strategic interest

**Duration:**
- English: 20–45 min (scaled by # suppliers)
- Dutch: 15–30 min
- Japanese: 5–10 min/round × estimated rounds

**Auto-extension (English only):** 3 min extension if bid in last 3 min

**Japanese rounds:** (spread% / decrement%) + 2 buffer rounds

**Dutch increment:** 0.5%–1.5% per tick based on strategic interest

### Saving estimation
Base ranges per format × 4 multiplicative factors (spread, # suppliers, behavior, strategic interest). Hard cap: optimistic saving never exceeds spread %.

**CRITICAL CALIBRATION NOTE:** Current base ranges produce optimistic values up to 25%. Real-world benchmark from 90+ auctions is ~11% average. Reduce base multipliers or add absolute cap at 18-20%. Experienced buyers will distrust inflated estimates.

### Confidence score
Current implementation divides winner score by sum of all positive scores → diluted results (0.37-0.40). Improve to: (winner - runner_up) / winner. This better captures "how clearly dominant" the recommendation is.

---

## Simulator (simulador.py)

**Architecture:** Deterministic data layer + Claude API narrative layer.

The simulator should:
1. Calculate structured behavior predictions per supplier archetype (who leads, who drops, at what price range)
2. Generate risk alerts (desert auction, early dropout, collusion signals)
3. Pass structured data to Claude API for natural language narrative

**Supplier archetypes to model:**
- Aggressive leader (low cost, high interest — bids early and often)
- Cautious follower (watches ranking, bids in final minutes)
- Floor-setter (bids once to establish position, waits)
- Dropout candidate (high cost or low interest — exits early)

**Per-format simulation logic:**
- English: model bidding waves and last-minute sniping
- Dutch: model acceptance threshold per archetype
- Japanese: model round-by-round elimination sequence

---

## Claude API Usage (prompt_engine.py)

**Model:** `claude-sonnet-4-20250514` for MVP. Opus as future option in config.
**API key:** loaded from `st.secrets["ANTHROPIC_API_KEY"]` (Streamlit Cloud) or `os.environ["ANTHROPIC_API_KEY"]` (local dev).

**Cost control:**
- Claude API is triggered ONLY by explicit user action ("Generate AI analysis" button)
- Motor.py and simulador.py deterministic outputs are the primary product
- Rate limit: consider capping at 5 API calls per session

**Prompt structure:**
- System prompt: auction theory expert persona with Coupa domain knowledge
- User prompt: structured JSON with motor.py outputs + input parameters
- Response format: structured sections (narrative, risks, opportunities)

---

## PDF Export (exportador.py)

Use ReportLab. The PDF should include:
1. Header with BidWise branding
2. Recommendation card (format + justification)
3. Optimized parameters table
4. Supplier behavior simulation narrative
5. Saving estimate (pessimistic/realistic/optimistic)
6. Theoretical references
7. Alerts (if auction is not recommended)
8. Footer with timestamp and disclaimer

---

## App Features (app.py)

### MVP (Week 1):
- Input form with all 8 variables + optional BRL values
- Recommendation card with visual highlight
- Parameters table
- Saving estimate with range visualization
- Supplier behavior simulation (deterministic + optional AI narrative)
- Scenario comparator (side-by-side, 2-3 configs)
- PDF export button
- Plausible Analytics (anonymous)
- English UI only

### v1.1 (Week 2):
- Bilingual toggle (EN/PT-BR)
- "Show reasoning" expandable — format scores side by side
- Improved saving calibration based on user feedback

### Future:
- RFQ strategy advisor module
- TCO calculator integration
- Kraljic matrix visualizer
- Multi-lot auction strategy

---

## Analytics

Plausible Analytics (free tier, privacy-first, no cookies).
Script tag in Streamlit via `st.markdown` with `unsafe_allow_html=True`.
Domain: `bidwise.streamlit.app`

---

## Code Conventions

- Type hints on all functions (use dataclasses for structured data, Enum for domains)
- Docstrings with theoretical references where applicable
- No abbreviations in variable names (except `inp` for InputLeilao, `pct` for percentage, `brl` for Brazilian Real)
- Comments in English (code), content in English (UI MVP), Portuguese reserved for v1.1
- Keep motor.py with zero external dependencies — stdlib only
- Test scenarios in `if __name__ == "__main__"` blocks during development

---

## Theoretical References (cite in justifications)

| Book | Author | Concepts |
|------|--------|----------|
| Auction Theory | Vijay Krishna | Format selection, private vs common value, revenue equivalence theorem |
| Thinking Strategically | Dixit & Nalebuff | Game theory, Nash equilibria, strategic behavior |
| Negotiation Genius | Malhotra & Bazerman | Anchoring, opening price effect, extension strategy |
| The Psychology of Price | Leigh Caldwell | Ranking/thermometer psychological effects on decisions |
| Competitive Procurement Strategy | David Muir | When auction is right mechanism vs RFQ vs direct negotiation |

---

## Known Issues & TODOs

- [ ] Saving estimation needs calibration (cap at 18-20%, reduce base ranges)
- [ ] Confidence score formula needs rework (winner-runner_up)/winner
- [ ] Urgency enum has gender inconsistency (Alto/Alta) — normalize in motor.py
- [ ] simulador.py not yet created
- [ ] prompt_engine.py not yet created
- [ ] Plausible integration not yet implemented
- [ ] Bilingual support deferred to v1.1
