# BidWise — Decisions Log

## Project Identity
- **Name:** BidWise
- **Repo:** HenriqueAPSilva/bidwise (public, open source, MIT)
- **URL:** bidwise.streamlit.app
- **Stack:** Python, Streamlit, ReportLab, Matplotlib
- **Language:** English (MVP). PT-BR deferred to v1.1

## Architecture Decisions

### Format Recommendation Engine (motor.py)
- 4 formats: English Full (ranking + thermometer), English Reduced (ranking only), Dutch Reverse, Japanese Reverse
- Scoring system: each format has independent scoring function, highest score wins
- Motor is the SINGLE SOURCE OF TRUTH for all numbers (saving, prices, parameters)
- Simulator handles behavior only, never generates its own saving numbers
- Confidence score calculated internally but NEVER shown to user

### Opening Price Logic (DEFINITIVE)
- **English (both):** Best Response — suppliers enter with their equalized prices. No buyer-defined ceiling. Motor returns 0% adjustment.
- **Dutch:** Buyer-Defined. ≥4 suppliers → start 20% below best proposal. <4 suppliers → start 10% below.
- **Japanese:** Buyer-Defined. High commoditization → start at best proposal (0%). Medium/Low → start at worst proposal.
- Radio button options in UI: "Use BidWise suggestion" / "Use best equalization price as ceiling (0%)" / "Custom adjustment"

### Supplier Input Model
- Individual per supplier (not aggregated): name, proposal ($), strategic interest, behavior
- Price spread auto-calculated from individual proposals
- comportamento_predominante and interesse_predominante = mode of individual values (for scoring)
- Simulation uses individual profiles for behavioral modeling

### Removed Features
- **Urgency:** removed entirely — auction blocks a full day regardless, urgency doesn't affect format choice
- **Collusion risk:** removed from inputs, scoring, and all files
- **AI Analysis:** disabled in MVP — no Claude API calls, no Anthropic references anywhere
- **Confidence score:** kept internal, removed from UI and PDF
- **Cap of 18% on saving:** removed, only natural cap (optimistic ≤ spread)
- **"90+ auctions" mention:** removed from all files

### Saving Estimation
- Must be multiples of decrement (floor rounding)
- If rounded to 0 but raw > 0, use 1x decrement as minimum
- Applies to pessimistic, realistic, AND optimistic
- Natural cap: optimistic never exceeds price spread

### Duration
- Cap: 90 minutes for ALL formats
- Japanese: if exceeds 90min, reduce rounds proportionally keeping time/round

### Thermometer Visibility
- Derived directly from format choice, not separate logic
- INGLES_COMPLETO → Enabled
- INGLES_REDUZIDO → Disabled
- HOLANDES/JAPONES → None (don't show field)

## UI/UX Decisions

### Privacy
- Bar at top: "No cookies · No tracking · No data stored · Your scenarios exist only in your active session"
- No data transmitted externally
- "Take to AI" prompt uses anonymized names (Supplier 1, 2...) and aggregated data only

### Currency
- $ (not R$) throughout

### Layout
- Sidebar width: 420px
- Sections order: Recommendation → Parameters → Saving Estimate + graph + PDF button → Simulation → Compare Scenarios → Take to AI → Theoretical Foundation
- Dividers between sections
- No dedicated "Export Report" section — PDF button inline

### Dropdown Labels (shortened)
- Kraljic: "Leverage — High impact, low risk" etc.
- Commoditization: "High — Standard specs, many suppliers" etc.
- Behavior: "Competitive — Bids aggressively, responds to pressure" etc.
- Strategic interest: "High — Wants contract, will bid hard" etc.

### Emojis per Format
- English Full → 📊
- English Ranking Only → 📋
- Dutch → 🔒
- Japanese → ⏬
- No auction → ⚠️

### Compare Scenarios
- Visible section (not expander)
- User names each scenario
- Saving 1st scenario shows it immediately with "Save another to compare"
- Clear all button

### Footer
- "Built by Henrique Silva — Strategic Sourcing Analyst"

## Chart: Uncertainty Projection
- Per supplier, ordered as user input
- Circle (blue, open) = initial proposal
- Diamond (green, filled) = realistic target
- Blue box (semi-transparent) = uncertainty range
- X-axis labels: "Supplier A (F)" where letter = archetype initial
- Appears in app.py AND in PDF (last section)
- Logo "BidWise" bottom right

## Simulation Decisions

### Archetype Mapping (strict)
- Competitive + High interest → Aggressive Leader
- Competitive + Medium OR Moderate + High → Cautious Follower
- Moderate + Medium/Low → Floor-setter
- Conservative + any OR any + Low → Dropout Candidate
- If no supplier matches an archetype, that archetype DOES NOT appear in narrative

### Narrative Style
- Reference suppliers by name: "Supplier A (conservative, low interest) is likely to withdraw early"
- Group same-archetype suppliers: "Supplier A and C (Floor-setters) will..."
- Soft prediction: "Best positioned to win: X, followed by Y" (never "Likely winner")

### Individual Targets (for chart)
- Aggressive Leader: saving × 1.3
- Floor-setter: saving × 1.0
- Dropout: saving × 0.5
- Range: ±30% of target

## PDF Decisions
- Scenario Summary + supplier table at the beginning (before recommendation)
- Remove duplicate "Supplier profiles" section
- Include uncertainty projection chart at the end
- All text in English
- No AI narrative section

## Pending (not yet implemented)
- Spread > 50% warning in app.py
- Fix truncated Opening Price label ("vs. e...")
- Fix saving optimistic = 0.0% bug
- Enums leaking in Portuguese to "Take to AI" prompt
- Bilingual toggle (v1.1)
- Incumbent supplier checkbox (v1.1)
- Pre-auction health check / effort-to-saving ratio (v1.1)
- Post-auction analysis tab (v1.1)
- Communication timing recommendation (v1.1)
- Lot strategy (future)

## Analytics
- Plausible Analytics (free tier, cookie-free)
- Domain: bidwise.streamlit.app

## About Page
- No mention of specific number of auctions
- Emphasize: deterministic engine, no black box, open source
- How to verify: F12 → Network tab
- "AI as amplifier, not substitute"
