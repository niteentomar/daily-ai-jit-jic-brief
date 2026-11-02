ROLE: Strict reviewer deciding whether research papers belong in a lesson.

LESSON TOPIC: "{topic}"

PAPERS (title, year, abstract excerpt):
{papers}

Grade EVERY paper for how directly it is ABOUT the lesson topic or one of its listed sub-concepts:
- 3 = introduces, defines or surveys the topic itself (a seminal or canonical paper for it)
- 2 = directly studies one of the topic's sub-concepts
- 1 = only mentions or uses the topic; the paper is really about something else
- 0 = unrelated (a famous paper from another area is still 0)

Examples for the topic "Transformer Architecture - Attention Mechanism":
- "Attention Is All You Need" -> 3 (introduces the transformer)
- "Linformer: Self-Attention with Linear Complexity" -> 2 (studies the attention sub-concept)
- "Highly accurate protein structure prediction with AlphaFold" -> 1 (uses attention for biology)
- "Using thematic analysis in psychology" -> 0

Return one entry per paper: id (P1, P2, ...), grade (0-3), reason (at most 15 words).
