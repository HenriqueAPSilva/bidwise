# BidWise 🔨

**Reverse Auction Strategy Advisor** — powered by auction theory & Coupa platform rules.

BidWise recommends the optimal reverse auction format and parameters for corporate buyers, maximizing saving through data-driven configuration.

[screenshot placeholder]

## What it does

Insert your procurement scenario → get a complete auction strategy:
- **Format recommendation** (English, Dutch, or Japanese Reverse) with theoretical justification
- **Optimized parameters** (minimum decrement, opening price, duration, auto-extension)
- **Saving estimate** (pessimistic / realistic / optimistic ranges)
- **Supplier behavior simulation** with risk alerts
- **Scenario comparator** to test different configurations side by side
- **PDF export** of the complete strategy report
- **Optional AI-enhanced analysis** powered by Claude API

## Supported Coupa auction formats

- English Reverse — Full visibility (ranking + thermometer)
- English Reverse — Reduced visibility (ranking only)
- Dutch Reverse (clock auction — closest to sealed bid)
- Japanese Reverse (clock auction — progressive elimination)

## Theoretical foundation

| Book | Author | Applied concept |
|------|--------|----------------|
| Auction Theory | Vijay Krishna | Format selection, revenue equivalence |
| Thinking Strategically | Dixit & Nalebuff | Nash equilibria, strategic behavior |
| Negotiation Genius | Malhotra & Bazerman | Anchoring, opening price effects |
| The Psychology of Price | Leigh Caldwell | Ranking/thermometer psychological effects |
| Competitive Procurement Strategy | David Muir | Mechanism selection (auction vs RFQ) |

## Built by

**Henrique Silva** — 7+ years in strategic sourcing with extensive experience in reverse auctions at Vale S.A. and ArcelorMittal Brasil. Electrical Engineering (CEFET-MG), MBA (USP).

- Managed R$1.2B+ refractory portfolio at ArcelorMittal
- Achieved 11% average saving across Sol do Cerrado, Salobo III, and S11D projects
- Winner of ArcelorMittal's Açolab hackathon with a no-code contract analysis chatbot

[LinkedIn](https://www.linkedin.com/in/henrique-alexandre-pinto-silva/) · [GitHub](https://github.com/HenriqueAPSilva)

## Tech stack

Python · Streamlit · Claude API (Anthropic) · ReportLab · Pandas

## Run locally

```bash
git clone https://github.com/HenriqueAPSilva/bidwise.git
cd bidwise
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
streamlit run app.py
```

## License

MIT
