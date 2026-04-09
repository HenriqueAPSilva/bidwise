## How to Model Your Suppliers

BidWise uses two inputs per supplier — **Behavior** and **Strategic Interest** — to predict auction dynamics. These two fields are flexible enough to model complex real-world situations. Here's how.

### Understanding the combinations

| Behavior | Interest | Archetype | What it means |
|----------|----------|-----------|---------------|
| Competitive | High | Aggressive Leader | Will bid early, often, and hard. Drives the price down. |
| Competitive | Medium | Cautious Follower | Watches the ranking, activates in the final sprint. |
| Moderate | High | Cautious Follower | Interested but calculated. Won't overextend. |
| Moderate | Medium | Floor-setter | Marks a position, waits. Doesn't reveal true floor. |
| Moderate | Low | Floor-setter | Participates but passively. |
| Conservative | High | Floor-setter | Wants the contract but already gave best price. |
| Conservative | Medium | Dropout Candidate | May withdraw if pushed. |
| Conservative | Low | Dropout Candidate | Likely won't bid actively. |

### Real-world scenarios

**🏢 The Incumbent**
The supplier who currently holds the contract. Switching costs work in their favor — the buyer prefers to keep them if the price is close enough. They rarely need to bid aggressively.

→ **Interest Medium + Behavior Moderate** (wants to keep but won't fight hard)
→ If complacent incumbent: **Interest Low + Behavior Conservative**

**📉 The "Already Cheap" Supplier**
Came in with an aggressive price in the RFQ/equalization round, but has no more room to go down. Their equalized price IS their floor.

→ **Interest High + Behavior Conservative** (wants the contract but can't move further)

**🌎 The Regional Aggressor**
Local company with logistics advantage, hungry for market share. Will undercut to win.

→ **Interest High + Behavior Competitive**

**🏛️ The Global Corporation**
Large multinational with global pricing policies. Local team has limited authority to deviate from headquarters-approved price lists.

→ **Interest Medium + Behavior Conservative**

**🆕 The New Entrant**
Supplier trying to break into your market. Willing to accept lower margins to establish a reference case or relationship.

→ **Interest High + Behavior Competitive**

**😐 The Reluctant Participant**
Was invited but doesn't really want the contract. Participating to maintain the relationship or because they were obligated.

→ **Interest Low + Behavior Conservative** (BidWise will classify as Dropout Candidate)

**🏭 The Supplier with Idle Capacity**
Has excess production capacity and needs volume to dilute fixed costs. Highly motivated to win at almost any price.

→ **Interest High + Behavior Competitive**

**💎 The Premium Supplier**
Sells quality and service, not price. Won't compete in a price-only auction. Their value proposition is post-sale support, reliability, or technical superiority.

→ **Interest Low + Behavior Conservative**

### Tips

- **When in doubt, use Moderate + Medium.** This is the neutral profile — BidWise will classify it as Floor-setter, which is the most common real-world behavior.

- **The most impactful input is the proposal value.** Even if you're unsure about behavior, entering accurate equalized proposals gives BidWise the spread data it needs for good recommendations.

- **Test different profiles.** Use the Compare Scenarios feature to see how changing one supplier's profile affects the recommendation. For example: what happens if the incumbent becomes more aggressive?
