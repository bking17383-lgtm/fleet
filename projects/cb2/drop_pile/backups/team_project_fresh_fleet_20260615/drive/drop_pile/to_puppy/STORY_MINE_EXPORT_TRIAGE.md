# Puppy — Story Mine Phase 1 + triage

**Word:** `STORY MINE`  
**From:** CAPTN · Brian delegate 2026-06-15  
**Account:** tpgoround@gmail.com (Drive sync on puppy64)

---

## Job

1. Export gdoc bodies → `stories_export/raw/*.md` (batch 1 ~50, then scale)
2. Run triage:

```bash
python3 /mnt/home/google_drive/MyDrive/lester/story_mine/story_triage.py
```

3. Post to `fleet/bus/puppy_outbox.txt`:

```
story_mine: exported N · inventions found M · triage picks on Drive
hostname: puppy64
```

---

## Batch 1 priority (export first)

Read `stories_export/catalog/PRIORITY_EXPORT.txt`

Use Drive API or sync mount + export tool per `concepts/STORY_MINE_DESIGN.md`  
**Do not** export fleet/lester/drop_pile gdocs (manifest excludes)

---

## Done when

- `stories_export/raw/` has files (not empty)
- `TRIAGE_PICKS.md` lists inventions + novelty lanes
- Uncle can read picks without Brian relay

Brian stays creative. Puppy executes. No LLM burn on 4M words — regex triage first.
