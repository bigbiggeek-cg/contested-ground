# Future Work

Not scheduled — just capturing intent for later.

## ~~Rename Flagship → Deep Dives, then flesh out content~~ — Done
Renamed "Flagship" to "Deep Dives" everywhere (nav, footer, section id/heading, JS variable names). Built a new [Deep Dive Page.dc.html](Deep%20Dive%20Page.dc.html) template (modeled on the Blog's Post Page) and wrote full long-form content for all 4 pieces — each ~1900–2500 words with key takeaways, domain tags, and full article bodies. Homepage cards now link to them with real read times (10–13 min). Note: shorter than the "3000+ word" target in the original content plan — ask if longer versions are wanted.

## Downloadable PDF "book" version of the content
Compile the course content into a book-style PDF, with a download link somewhere on the site. Scope/format (full course vs. per-Domain, cover/TOC design, etc.) not yet decided.

## Cybersecurity self-assessment
A standalone assessment (distinct from the per-lesson quizzes) that rates the user's overall cybersecurity understanding — "where am I, what can I improve." Likely surfaces a score/level and personalized recommendations on which Domains/lessons to focus on. Scope/format (question count, scoring model, where it lives in the nav) not yet decided.

## Quiz answers are predictable — mostly the middle option
Checked the 60 quiz questions in Lesson Page.dc.html: 48 of 60 (80%) have the correct answer as the middle (2nd of 3) option, 11 have it first, only 1 has it last. Predictable enough that a user could learn to guess "always pick B" instead of engaging with the question. Fix: shuffle/rebalance correct-answer position across the question set so it's not detectably patterned.
