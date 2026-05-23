// Seed data for the daily radar — personal quest: bug bounty + AI-era money flows + path to $1M
window.QUESTS = [
  { id: "q1", name: "Bug bounty signal", color: "#c97f3f", count: 14 },
  { id: "q2", name: "AI disruption money flows", color: "#8a6dc9", count: 22 },
  { id: "q3", name: "Solo founder ARR", color: "#4f8a5e", count: 9 },
  { id: "q4", name: "Path to $1M", color: "#b85a5a", count: 6 },
  { id: "q5", name: "Craft & taste", color: "#5a7fb8", count: 11 },
];

window.SOURCES = [
  { id: "hn", name: "Hacker News", glyph: "Y", count: 4 },
  { id: "x", name: "X / Twitter", glyph: "X", count: 5 },
  { id: "reddit", name: "Reddit", glyph: "r", count: 3 },
  { id: "gh", name: "GitHub", glyph: "G", count: 2 },
  { id: "rss", name: "RSS", glyph: "R", count: 4 },
];

window.TAGS = [
  "ssrf", "idoor", "race-condition", "supply-chain",
  "claude", "agents", "rag", "evals",
  "arr-report", "pricing", "distribution",
  "btc", "stables", "yield",
  "discipline", "deep-work",
];

// score: 1-10 (intent match). 7+ surface with amber dot. Includes a `reason` string the LLM "wrote".
window.ITEMS = [
  {
    id: "i01", source: "hn", quest: "q1",
    title: "Show HN: I made $180k in bug bounties last year — full workflow + tooling",
    summary: "Six-month log of recon → triage → report. Heavy on Caido + Nuclei + custom diffing. Author is solo, no team, EU-based.",
    url: "news.ycombinator.com/item?id=…", points: 412, comments: 187,
    time: "2h", new: true,
    score: 9.4, reason: "Direct match on bug bounty quest. Concrete workflow + earnings number — high signal vs. theory posts you usually skip.",
    tags: ["arr-report", "discipline"],
    body: "After three years at a fullstack job I gave myself 12 months runway and went full-time on web bounties. Year one: $180k, mostly from three programs. What worked: pick three programs and live in them for months. Don't program-hop. What didn't: chasing P1s before mapping. Below is the exact daily routine, the toolchain (Caido + custom nuclei templates), and the three reports that paid 60% of the year."
  },
  {
    id: "i02", source: "x", quest: "q2",
    title: "@swyx: 'AI agents will eat 80% of mid-tier SaaS by 2027 — but the floor of solo-built businesses just got 100x deeper'",
    summary: "Thread on what survives: distribution, taste, vertical specificity. Calls out 8 companies likely commoditized in 18mo.",
    url: "x.com/swyx/status/…", points: 2840, comments: 312,
    time: "4h", new: true,
    score: 9.1, reason: "Maps the disruption you're trying to navigate. Names specific incumbents — actionable for ARR positioning.",
    tags: ["agents", "distribution", "pricing"],
    body: "Hot take, tag yourself: which of these 8 SaaS categories survives the agent layer? My bet — the ones with proprietary data flywheels die last. Everyone else has 18 months to find a wedge that isn't a workflow LLMs can replicate."
  },
  {
    id: "i03", source: "gh", quest: "q1",
    title: "trailofbits/semgrep-rules — new SSRF detection ruleset for Node 22+",
    summary: "147 new patterns. PR mentions catching 3 zero-days in widely-used npm packages during development.",
    url: "github.com/trailofbits/semgrep-rules", points: 89, comments: 12,
    time: "6h", new: true,
    score: 8.7, reason: "New tooling that compounds your recon. SSRF is your bread-and-butter class — these patterns become baseline scans.",
    tags: ["ssrf", "supply-chain"],
    body: "Adds taint tracking for fetch(), undici, native http. The interesting ones are in `node-redirects-followed.yaml` — catches the redirect-allowlist-bypass pattern that's been showing up in HackerOne reports all year."
  },
  {
    id: "i04", source: "reddit", quest: "q3",
    title: "r/SaaS: $0 → $42k MRR in 11 months, solo, one product, no team",
    summary: "Boring tax compliance tool for Shopify sellers. No funding. Author breaks down channels: 70% SEO, 20% partner integrations, 10% paid.",
    url: "reddit.com/r/SaaS/comments/…", points: 1240, comments: 287,
    time: "8h", new: true,
    score: 8.9, reason: "Solo founder template that worked WITHOUT a moat — closest pattern to your '1hr/day → product' arc.",
    tags: ["arr-report", "distribution"],
    body: "I'm a developer who's never done sales. The unlock was realizing the smallest sellers (≤$10k/mo on Shopify) had no compliance tooling priced for them — TaxJar starts at $99/mo and felt insulting at that scale. I built the dumbest possible version, priced $19/mo, and let SEO do the rest."
  },
  {
    id: "i05", source: "hn", quest: "q2",
    title: "Anthropic ships Claude 4.5 Haiku — 80% cheaper than Sonnet, indistinguishable on most agent benchmarks",
    summary: "Pricing math: a workflow that costs $0.40 in Sonnet now costs $0.08. Margin shift for AI wrappers is brutal.",
    url: "news.ycombinator.com/item?id=…", points: 1820, comments: 614,
    time: "11h", new: true,
    score: 8.4, reason: "Pricing changes that re-shuffle which AI wrappers can survive. Direct input to your 'what to build' decisions.",
    tags: ["claude", "agents", "pricing"],
    body: "If you priced your SaaS assuming Sonnet costs, your gross margin just went from 40% to 88%. If you priced assuming Haiku costs, your competitor's margin just went from -10% to 40%. Everyone is repricing this weekend."
  },
  {
    id: "i06", source: "x", quest: "q4",
    title: "@naval: 'The path to $1M is now a question of taste, not labor'",
    summary: "Short thread arguing that AI compresses execution time to zero, so the bottleneck is knowing what to build.",
    url: "x.com/naval/status/…", points: 5200, comments: 401,
    time: "14h", new: false,
    score: 7.2, reason: "Re-affirms a worldview you already hold — useful as fuel but watch confirmation bias.",
    tags: ["distribution"],
    body: ""
  },
  {
    id: "i07", source: "rss", quest: "q1",
    title: "PortSwigger: Top 10 web hacking techniques of 2025 — nominations open",
    summary: "Annual research roundup. Last year's winner was the GraphQL alias-overloading DoS class. Submissions close end of month.",
    url: "portswigger.net/research/top-10-2025", points: 0, comments: 0,
    time: "1d", new: false,
    score: 8.1, reason: "The single best yearly index of new bug classes. Read the full list — last year three of these became your top earners.",
    tags: ["ssrf", "race-condition"],
    body: "Nominations are open until the 30th. The shortlist drops in two weeks. Historically the techniques that win here become the next year's bounty gold rush — reading this list early is one of the highest-leverage hours of the year."
  },
  {
    id: "i08", source: "hn", quest: "q5",
    title: "How to actually finish things — a working programmer's anti-distraction protocol",
    summary: "No new ideas. Aggressive single-tasking, written daily intent, a forced 'shipping clock'. Author shipped 4 products in 18 months.",
    url: "news.ycombinator.com/item?id=…", points: 940, comments: 220,
    time: "1d", new: false,
    score: 7.8, reason: "Discipline content — your stated weak point. Concrete protocol, not motivation.",
    tags: ["discipline", "deep-work"],
    body: ""
  },
  {
    id: "i09", source: "reddit", quest: "q1",
    title: "r/bugbounty: First $50k bounty after 8 months of zero. The bug class nobody is looking at.",
    summary: "OAuth state-parameter desync across consent screens. Hits 4 major IDPs. Author hints at the methodology without giving it away.",
    url: "reddit.com/r/bugbounty/…", points: 612, comments: 89,
    time: "1d", new: false,
    score: 8.8, reason: "Specific bug class + earnings proof. The methodology hint is enough to reverse-engineer the recon path.",
    tags: ["idoor", "ssrf"],
    body: ""
  },
  {
    id: "i10", source: "gh", quest: "q2",
    title: "anthropics/courses — new repo: 'Building production agents'",
    summary: "Four-module course. Heavy on evals and failure-mode analysis. PRs from real anthropic engineers, not just docs team.",
    url: "github.com/anthropics/courses", points: 312, comments: 18,
    time: "1d", new: false,
    score: 7.9, reason: "First-party material on the exact stack you'd build with. Evals chapter is the actual differentiator.",
    tags: ["claude", "agents", "evals"],
    body: ""
  },
  {
    id: "i11", source: "x", quest: "q1",
    title: "@samczsun: 'New EVM bug class — discovered via differential fuzzing across 4 clients'",
    summary: "Thread is sparse on detail (responsible disclosure window). Mentions the affected client trio. Bounty paid was 'low seven figures'.",
    url: "x.com/samczsun/status/…", points: 4100, comments: 280,
    time: "2d", new: false,
    score: 8.6, reason: "Adjacent quest — Web3 bug hunting tier you've been circling. Differential fuzzing technique generalizes to your current targets.",
    tags: ["race-condition"],
    body: ""
  },
  {
    id: "i12", source: "rss", quest: "q3",
    title: "Indie Hackers: 'I killed my SaaS at $8k MRR to start over. Here's the math.'",
    summary: "Founder ran a profitable bootstrapped tool for 2 years, then decided the ceiling was too low. Migration to a new wedge, same audience.",
    url: "indiehackers.com/post/…", points: 410, comments: 67,
    time: "2d", new: false,
    score: 6.4, reason: "Interesting case study but the math is wedge-specific. Read the audience-retention section, skip the rest.",
    tags: ["arr-report"],
    body: ""
  },
  {
    id: "i13", source: "hn", quest: "q2",
    title: "The new moat is the eval set — why your AI product dies without one",
    summary: "Argues that prompts are commodity, models are commodity, but a 2,000-row eval set tuned to your customer's exact failure modes is the only durable advantage.",
    url: "news.ycombinator.com/item?id=…", points: 780, comments: 144,
    time: "2d", new: false,
    score: 8.3, reason: "Sharpest framing of the 'AI wrapper' survival question. Operational, not philosophical.",
    tags: ["agents", "evals"],
    body: ""
  },
  {
    id: "i14", source: "reddit", quest: "q4",
    title: "r/financialindependence: Reached $1M net worth at 31 — the boring breakdown",
    summary: "Software engineer, no equity windfalls, no crypto. 9 years of consistent 60% savings rate + index funds. Lifestyle creep section is honest.",
    url: "reddit.com/r/fi/…", points: 2100, comments: 580,
    time: "2d", new: false,
    score: 5.8, reason: "Counter-narrative to your 'find the alpha money flow' frame — the dull path also works. Worth one read to calibrate.",
    tags: ["discipline"],
    body: ""
  },
  {
    id: "i16", source: "hn", quest: "q1",
    // Deduped: same story appeared on HN + Reddit + X — merged into one card
    sources: [
      { id: "hn", name: "Hacker News", glyph: "Y" },
      { id: "reddit", name: "Reddit", glyph: "r" },
      { id: "x", name: "X", glyph: "X" },
    ],
    title: "Critical IDOR in HackerOne's own platform — disclosed after 90-day window",
    summary: "Researcher found that HackerOne's internal report ID was sequential and enumerable. Full report, payload, and $20k bounty confirmed. Same story cross-posted across three sources — Quarry deduped it.",
    url: "news.ycombinator.com/item?id=dedup-demo", points: 1840, comments: 341,
    time: "3h", new: true,
    score: 9.6, srcReliability: 94,
    tags: ["idoor", "ssrf"],
    body: "The bug was straightforward: sequential report IDs + missing auth check on one internal API endpoint. The 90-day window is now closed. The researcher walked through the full recon path — it started with a JavaScript file that referenced an undocumented endpoint.",
  },

  {
    id: "i15", source: "x", quest: "q5",
    title: "@patrickc: 'Reading list for people who want to build durable companies, not careers'",
    summary: "Eight books, four of them not in the usual rotation. The Henderson one in particular is unusual.",
    url: "x.com/patrickc/status/…", points: 3200, comments: 190,
    time: "3d", new: false,
    score: 7.0, reason: "High-signal taste-maker, but reading lists are noise unless you commit to one. Save the Henderson recommendation.",
    tags: ["deep-work"],
    body: ""
  },
];

// Saved memos — the knowledge garden
window.MEMOS = [
  {
    id: "m01", date: "Today",
    title: "Daily Radar — Tue, May 12",
    body: "Two patterns today. (1) OAuth state desync is having a moment — see Reddit $50k post + adjacent semgrep ruleset drop. Likely a 2-week window before everyone is hunting it. (2) Haiku 4.5 pricing collapses the floor — anyone running Sonnet in a per-task loop just got a 5x cost cut. Re-price the side project this weekend.",
    tags: ["daily-radar", "ssrf", "claude"],
    linkedItems: ["i03", "i05", "i09"],
  },
  {
    id: "m02", date: "Yesterday",
    title: "On the 1hr/day question",
    body: "Khabib's critique landed. 1hr/day is aspirational right now, not real. The discipline gap is the project, not the tool. Commit: 7am-8am, no exceptions, for 21 days. If I miss 3 days in a row, kill the project. Track on the streak counter.",
    tags: ["discipline", "deep-work"],
    linkedItems: [],
  },
  {
    id: "m03", date: "2d ago",
    title: "Bug class watchlist — May",
    body: "Tracking these for the month: (a) OAuth state-parameter desync, (b) GraphQL alias-overload DoS, (c) SSRF via Node 22 fetch redirect chains, (d) race conditions in stripe-connect webhook handlers. Hypothesis: (a) and (c) are the highest-EV given my current toolchain.",
    tags: ["ssrf", "race-condition", "idoor"],
    linkedItems: ["i03", "i09"],
  },
  {
    id: "m04", date: "3d ago",
    title: "The eval set as moat — synthesis",
    body: "Three sources converging this week on the same thesis: prompts and models are commodity, evals are not. The implication for me: any AI side project I build needs the eval set scoped on day one. Without it, I'm building a demo, not a product.",
    tags: ["agents", "evals", "claude"],
    linkedItems: ["i13", "i10"],
  },
  {
    id: "m05", date: "5d ago",
    title: "Wedge candidates — solo, dev-tool flavored",
    body: "Three wedges where the AI cost collapse + my fullstack background + bounty instincts compound: (1) auto-triage for HackerOne reports, (2) eval-set-as-a-service for vertical AI tools, (3) compliance scanner for Shopify-class small sellers (the $42k MRR post is the proof). Ranking: 2 > 1 > 3, but 3 has the clearest distribution path.",
    tags: ["arr-report", "distribution", "agents"],
    linkedItems: ["i04", "i13"],
  },
];

window.STATS = {
  newToday: 7,
  totalToday: 15,
  streakDays: 18,
  memosTotal: 142,
  itemsReviewed: 1840,
  weeklyTrained: 47,
};
