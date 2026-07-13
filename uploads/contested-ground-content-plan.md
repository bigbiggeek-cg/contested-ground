# Contested Ground — Content & Design Reference

## Brand Overview
Contested Ground is a cybersecurity training site for IT pros leveling up in security. Content is written lessons plus podcast-style audio. Standalone brand — not tied to any personal brand.

**Positioning:** The cybersecurity knowledge every IT pro should have — but nobody explicitly taught them. Practical, vendor-neutral, no cert-dump fluff.

**Audience:** IT professionals (not security specialists) who need practical, applicable security knowledge for their day-to-day work and career growth.

---

## Design System

**Metaphor:** Football field — lessons grouped into "Drives" (topic tracks), each lesson tagged with a down-and-distance difficulty marker.

**Colors:**
- Navy (primary background): `#0B1F33`
- Navy mid (panels/cards): `#142C46`
- Navy line (borders/dividers): `#2A4361`
- Burnt orange (primary accent): `#D2571E`
- Bright orange (highlights/CTA): `#F2894E`
- Paper (primary text): `#F5EFE6`
- Slate (secondary text): `#8CA2BC`
- Slate dim (tertiary/muted): `#5E7591`

**Typography:**
- Display/headlines: **Oswald** (condensed, stadium-signage feel)
- Body/long-form reading: **Source Serif 4**
- Data, Event IDs, code references, difficulty markers: **JetBrains Mono**

**Structural devices:**
- **Drives** = the 6 topic tracks (see below)
- **Down-and-distance difficulty markers:**
  - 1ST & 10 = foundational
  - 2ND & 7 = intermediate
  - 3RD & LONG = advanced
- Yard-line dividers (dashed repeating pattern) used as section separators
- Each lesson page includes: track pill, down marker, read/listen time, audio player, key-takeaways callout, article body, related/up-next lessons

**Reference templates already built:** homepage mockup and lesson page template (HTML), available as design reference for the Next.js build.

---

## Content Structure: 6 Drives, 30 Lessons

### Drive 01 — Foundations
1. The IT Pro's Threat Model — what actually targets you vs. what makes headlines
2. Identity Is the New Perimeter — why credentials matter more than firewalls now
3. Patch Management Isn't Optional — the Windows Event IDs and CVEs that bite
4. Zero Trust: What It Actually Means (not the marketing version)
5. The CIA Triad in Practice — using it as a decision tool, not a textbook definition

### Drive 02 — Detection & Response
6. What Your SOC Actually Sees (and What It Doesn't)
7. Reading Logs Like an Analyst — Event IDs every IT pro should recognize
8. Lateral Movement 101 — how attackers move once they're in
9. Ransomware Playbook — the first hour matters more than the first day
10. Building a Detection Mindset Without a SOC Budget
11. EDR vs. Antivirus — what actually changed and why it matters
12. Tabletop Exercises: Practicing the Incident Before It's Real

### Drive 03 — Cloud & Modern Surface
13. Cloud Misconfigurations That Get Companies Breached
14. MFA Isn't Enough — MFA fatigue, token theft, and session hijacking
15. Shadow IT and Your Expanding Attack Surface
16. SaaS Sprawl and the Apps Nobody Approved
17. API Security Basics for Non-Developers
18. Container & Kubernetes Security 101

### Drive 04 — Practical Defense & Career
19. Backup Strategy That Survives Ransomware (3-2-1 isn't enough anymore)
20. Vendor Risk — why your supply chain is your problem
21. Incident Response Basics — building a plan before you need one
22. Talking to Leadership About Risk (without the jargon)
23. Certs That Actually Matter for IT Pros Moving Into Security

### Drive 05 — The Human Element
24. Social Engineering: Why Smart People Fall For It
25. Building a Security Culture People Don't Secretly Hate
26. Insider Threats: Not Always Malicious
27. Phishing Simulations Done Right (and Done Wrong)

### Drive 06 — Compliance & Governance
28. Compliance Isn't Security (But You Still Need Both)
29. Frameworks Without Drowning — NIST, CIS, ISO, decoded
30. Audit Season: Surviving It Without a Fire Drill

---

## Flagship Long-Form Pieces
Longer, higher-production pieces (20–30 min listen / 3000+ word read) that pull threads across multiple drives into a single narrative. Planned release cadence: roughly monthly, interspersed with the weekly regular-lesson cadence.

1. **Anatomy of a Breach: A Real Incident, Hour by Hour** — a composited, anonymized ransomware incident walked from initial access to containment. Ties Drives 1, 2, and 4 together into one narrative.

2. **The Modern Attack Surface: A Field Map** — a visual, reference-style deep dive mapping identity, endpoints, cloud, SaaS, APIs, and containers as one connected terrain. Designed to be bookmarked and revisited, not just read once.

3. **Why Good Security Programs Still Get Breached** — covers alert fatigue, compliance theater, security-culture failure, and the gap between having a policy and people actually following it. Pulls from Drives 5 and 6.

4. **Building an Incident Response Plan From Scratch, In a Weekend** — a step-by-step, genuinely usable guide. Candidate for a companion downloadable template/checklist — first real "gated content" opportunity (open question: free lead magnet vs. future paid-tier content).

---

## Open Decisions
- Domain: standalone domain recommended (not tied to bigbiggeek.net/.ai) — check `contestedground.io` / `contestedground.com` availability
- Monetization: undecided — build initial content free, gauge engagement, decide between one-time purchase vs. subscription later
- Gated content: whether flagship piece #4's companion template is a free lead magnet or reserved for a future paid tier
- Next build step: scaffold as a real Next.js site via Claude Code, using existing HTML templates as design reference
