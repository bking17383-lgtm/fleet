Blueprints — reusable session cards (short context, not long chat history)

Puppy Cursor: add your blueprints here so penguin + Lester reuse the same recipes.

FILES
  index.json     — catalog (one entry per card)
  <id>.md        — full recipe (load only when task matches)

ADD A CARD
  1. Copy blueprint-format.md as template
  2. Add entry to index.json (id, title, summary, tags, projects, machines, file)
  3. Penguin syncs: python3 ~/.stan/blueprints.py sync

OR from penguin/puppy shell:
  python3 ~/.stan/blueprints.py  (see blueprint-format.md)

SESSION START (agents read index only)
  ~/.stan/handoff/session_note.md — lists one-line cards
  Full body: python3 ~/.stan/blueprints.py show <id>

Good puppy blueprint topics: phone server setup, vision/frames, deploy scripts, QR URLs.
