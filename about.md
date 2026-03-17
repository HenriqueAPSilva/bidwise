## About BidWise

### Why I built this

I'm Henrique Silva, a procurement professional with 7+ years in strategic sourcing. I've run extensive reverse auctions and genuinely believe in this tool's potential.

Every reverse auction starts with the same question: which format should I use and how should I configure it? There's no tool for that — it's pure experience and intuition. BidWise codifies that decision into a transparent, auditable engine based on auction theory.

### How the engine thinks

BidWise scores four auction formats against your scenario and recommends the one that maximizes expected saving. Here's exactly how:

**Step 1 — Should you even run an auction?**
Before recommending a format, BidWise checks for disqualifying conditions: single supplier, strategic/bottleneck items with fewer than 3 suppliers, or a supplier field where low interest + conservative behavior makes a desert auction likely. If any condition is met, BidWise recommends an alternative mechanism (RFQ, direct negotiation, or a new qualification round).

**Step 2 — Scoring each format**
Four scoring functions run independently — one per format. Each function evaluates your scenario across multiple factors: number of suppliers, commoditization level, individual supplier behavior profiles, strategic interest profiles, Kraljic classification, and calculated price spread. Each factor adds or subtracts points. The format with the highest total score wins.

The key drivers per format:

* **English Full (ranking + thermometer):** Favors large fields (4+), high commoditization, competitive suppliers, high strategic interest. The thermometer amplifies psychological pressure.
* **English Ranking Only:** Favors moderate fields (3-5), medium commoditization, moderate behavior. Removes thermometer to prevent suppliers from calibrating the exact minimum needed to win.
* **Dutch Reverse:** Favors small fields (2-3), conservative suppliers, low spread. Maximum opacity — each supplier decides independently. Closest to a sealed bid.
* **Japanese Reverse:** Favors large fields (5+), high commoditization, heterogeneous behavior. Progressive elimination forces active decisions every round.

**Step 3 — Calculating the minimum decrement**
The decrement determines how much a supplier must reduce per bid. Too small = suppliers creep up the ranking without meaningful competition. Too large = weaker suppliers give up immediately.

BidWise calculates the average gap between adjacent proposals in your supplier field, then takes 40% of that gap as the base decrement. This ensures each bid can potentially change the ranking without being impossible.

The decrement is then bounded by dynamic caps based on contract value:

* Contracts under $200k: 0.5% – 14% range (high autonomy, suppliers decide fast)
* $200k – $2M: 0.3% – 10% (partial autonomy)
* $2M – $10M: 0.2% – 6% (each bid needs internal approval)
* Over $10M: 0.1% – 3% (committee-level decisions per bid)

Finally, adjusted by supplier behavior: competitive fields get +10%, conservative fields get -20%.

**Step 4 — Setting the opening price**
The opening price strategy depends on the format:

* **English Reverse:** Best Response — each supplier enters with their equalized proposal from the prior RFQ/RFP round. The ranking and competitive pressure do the work.
* **Dutch Reverse:** Buyer-defined floor. With 4+ suppliers: 20% below best proposal. With fewer: 10% below. The price climbs until someone accepts.
* **Japanese Reverse:** Buyer-defined ceiling. For commodities (high commoditization): starts at the best proposal. For complex items: starts at the worst proposal, giving everyone room to enter.

**Step 5 — Duration and extension**
Duration adapts to three factors: number of suppliers, contract value (larger = more time for internal approvals), and format characteristics (thermometer generates more interaction, needs more time).

Auto-extension (English only) also scales with contract value: 2 minutes for contracts under $200k up to 5 minutes for contracts over $2M. This captures last-minute sniping without rushing high-value decisions.

**Step 6 — Saving estimation**
Saving estimates are calculated per format with four multipliers: price spread (more room = more potential), number of suppliers (more competition = more saving), predominant behavior (competitive = more aggressive bids), and predominant strategic interest (high interest = more willingness to reduce).

All saving estimates are rounded down to the nearest multiple of the minimum decrement — because saving can only occur in discrete bid steps.

**Step 7 — Supplier behavior simulation**
Each supplier is classified into an archetype based on their individual behavior and strategic interest profile:

* Competitive + High interest → **Aggressive Leader**
* Competitive + Medium / Moderate + High → **Cautious Follower**
* Moderate + Medium or Low → **Floor-setter**
* Conservative + any / any + Low → **Dropout Candidate**

The simulation predicts who bids when, who exits early, and who is best positioned to win — but never overrides the motor's saving estimate. The engine calculates the numbers; the simulation tells the story.

### Your data, your control

* No cookies. No tracking. No accounts.
* No data is stored — your scenarios exist only in your active browser session
* No data is transmitted to external servers
* The "Copy prompt" feature generates text locally — nothing is sent unless YOU paste it somewhere
* Analytics by Plausible (privacy-first, cookie-free, no personal data)

**How to verify:** Open your browser's Developer Tools (F12), go to the Network tab, and run an analysis. You'll see only static asset requests to Streamlit Cloud and Plausible — no API calls with your data.

### Open source

Every line of code is available at [github.com/HenriqueAPSilva/bidwise](https://github.com/HenriqueAPSilva/bidwise).

Want to build something similar? Start with a real problem in your domain, codify your expertise into explicit rules, and use AI as an amplifier — not a substitute. The most valuable part of this project isn't the code. It's the decision logic behind it.

### Theoretical foundation

|Book|Author|Applied concept|
|-|-|-|
|Auction Theory|Vijay Krishna|Format selection, revenue equivalence, private vs common values|
|Thinking Strategically|Dixit \& Nalebuff|Nash equilibria, strategic behavior, sequential games|
|Negotiation Genius|Malhotra \& Bazerman|Anchoring, opening price effects, extension strategy|
|The Psychology of Price|Leigh Caldwell|Ranking/thermometer psychological effects on decisions|
|Competitive Procurement Strategy|David Muir|When auction is right mechanism vs RFQ vs direct negotiation|

### Built by

**Henrique Silva** — Strategic Sourcing Analyst.

[LinkedIn](https://www.linkedin.com/in/henrique-alexandre-pinto-silva/) · [GitHub](https://github.com/HenriqueAPSilva)

