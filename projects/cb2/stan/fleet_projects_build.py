#!/usr/bin/env python3
"""Build fleet project catalogs — Bunny truth (15) + Daddy archive (65)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

# Bunny truth — keaton INDEX + GEM sprint + FRUITION (Brian: 14–16)
BUNNY_ROWS: list[tuple[str, str, str, str, str, str, str]] = [
    ("sarah", "Sarah Voice", "LIVE", "Sarah · voice scheduling · minimal intrusion", "$$ appointment lane · human tester first", "fleet/SHIP_A_SARAH.txt", "ship"),
    ("hitme", "hitme Landing", "LIVE", "Visitors · strangers on LTE", "$ platform · leads to paid lanes later", "fleet/SHIP_B_HITME.txt", "ship"),
    ("cards", "CollX Card Scanner", "LIVE", "Collectors · estate executors · Brian inventory", "$$ Stripe after 6 scans · 497-card inventory", "fleet/SHIP_C_CARDS.txt", "ship"),
    ("heritage", "Heritage Card Demo", "DEMO", "Genealogy fans · phone rotate showcase", "$ demo → upsell catalog / print", "lester/heritage/card_demo.html", "ship"),
    ("jailbreak", "Free Lester / Jailbreak", "READY", "Card collectors · voice coach at table", "$$ micro per Live session · card grade upsell", "lester/free_lester_instructions.md", "ship"),
    ("rover", "Rover / Mesh Radio", "LIVE", "Brian road phone · camera+mic extension", "$0 internal · saves LTE hassle", "fleet/MESH_RADIO_URL.txt", "ship"),
    ("aws_lane", "AWS Talk Lane", "LIVE", "Brian riffing money ideas", "$0 ideation · batch to ship lanes", "fleet/AWS_LANE.txt", "ship"),
    ("alexa", "Alexa Brief Mode", "DONE", "Brian · Echo one-click", "$0 home filter · no port spam", "fleet/bus/GEM_PROJECT_SPRINT.txt", "platform"),
    ("story_games", "Story → Games Catalog", "NEXT", "Brian · game writers · story archive", "$ IP licensing later", "fleet/bus/GEM_PROJECT_SPRINT.txt", "backlog"),
    ("keaton", "Keaton Landing", "WIRING", "Public visitors · hitme.dev front door", "$ brand funnel · sound + counter", "fleet/KEATON.txt", "creative"),
    ("hitme_core", "hitme.dev Core", "LIVE", "Whole fleet · bus + URLs", "$0 infra · enables all lanes", "fleet/keaton/INDEX.txt", "platform"),
    ("gem_studio", "Gem Studio", "LIVE", "CB1 Chrome · local API", "$0 librarian tool", "fleet/keaton/INDEX.txt", "platform"),
    ("bunny_lab", "Bunny Lab", "LIVE", "Brian · builder indie loop", "$0 builder UX · Keaton host", "hitme.dev/bunny", "platform"),
    ("gl_live", "GL Live / Transcript Lab", "MESSY", "Brian · Gemini Live stack", "$0 until voice good enough", "gl/INDEX.md", "platform"),
    ("keaton_loader", "Keaton Project Loader", "LIVE", "All boxes · same project list", "$0 conflict avoidance", "fleet/KEATON.txt", "platform"),
]

# Daddy full scan — archive only (was wrongly shown as main list)
ARCHIVE_ROWS: list[tuple[str, str, str, str, str, str, str]] = BUNNY_ROWS + [
    ("sell_sheet", "497-Card Sell Sheet", "PRODUCE", "eBay buyers · local flippers", "$$ direct card sales · bundles", "/cards/sell", "money"),
    ("bundles", "Bundle Lots / CSV", "PRODUCE", "Bulk buyers · estate liquidators", "$$ lot pricing · eBay export", "/bundles", "money"),
    ("cockpit", "Garage Cockpit", "PRODUCE", "Brian · ship RPM dashboard", "$0 captain focus tool", "/cockpit", "platform"),
    ("dossier", "Deduction Dossier", "PRODUCE", "Tax / hobby deduction narrative", "$ saves accountant time", "/dossier", "money"),
    ("brochure", "Top Card Brochure", "PRODUCE", "Show-off one grail card", "$ marketing for single high sale", "/brochure", "money"),
    ("911", "9·1·1 Daily Ship List", "PRODUCE", "Brian · 20-min ship discipline", "$0 execution habit", "/911", "platform"),
    ("encore", "Encore Meter", "PRODUCE", "Brian · gamified follow-through", "$0 retention", "/encore", "platform"),
    ("studio_deck", "Studio Deck", "PRODUCE", "Internal · pitch all lanes", "$0 sales collateral", "/studio", "platform"),
    ("setlist", "Top 10 Setlist", "PRODUCE", "Collectors browsing highlights", "$ merch / list sales", "/setlist", "money"),
    ("story_card", "Story Card", "PRODUCE", "Story + card crossover fans", "$ narrative upsell on inventory", "/cards/story", "creative"),
    ("camel", "Camel Game", "SHIPPED v0.8", "Casual gamers · Silk Road theme", "$ mobile game · IAP later", "drop_pile/done/CAMEL_v0.8_shipped.md", "creative"),
    ("parcels", "Five Parcels Game", "LIVE", "Redneck homestead players", "$ ad / tip jar · Morgan brand", "/parcels", "creative"),
    ("dirt_strong", "Dirt Strong / Heartbeat", "LIVE", "Homestead · patriot audience", "$ merch · media · sponsors", "/dirt-strong", "creative"),
    ("sell_baby", "Sell Your Baby", "CONCEPT", "Satire readers · photo guilt parents", "$ $3/upload joke · Fall of Man Pageant", "drop_pile/proposals/SELL_YOUR_BABY_v0.md", "creative"),
    ("slicer", "Video Slicer", "CONCEPT", "Strangers on LTE · clip their video", "$$ micro · Play internal test", "concepts/CONCEPT_slicer_playstore.md", "money"),
    ("puppy_video", "Puppy Video", "CONCEPT", "Brian video pipeline", "$ TBD · demand test", "concepts/CONCEPT_puppy_video.md", "backlog"),
    ("anti_movie", "Anti-Movie One Page", "CONCEPT", "Film skeptics · one-pager pitch", "$ publishing / patron", "concepts/ideas/CONCEPT_anti_movie_one_page.md", "backlog"),
    ("estate_tiers", "CollX Estate Tiers", "IDEA-A", "Executors with 3000-card estates", "$$ grade · consign · dump routing fees", "concepts/ideas/IDEA_collx_estate_three_tiers.md", "money"),
    ("psa_alt", "PSA Alternative Grading", "IDEA-B", "Raw card collectors · transparency seekers", "$$ $2 micro-cert · beats PSA wait", "concepts/ideas/IDEA_psa_alternative.md", "money"),
    ("gedcom", "GEDCOM Synthesis", "IDEA", "Genealogy hobbyists", "$ subscription · report packs", "concepts/ideas/IDEA_gedcom_synthesis.md", "backlog"),
    ("estate_drawer", "Estate Drawer Catalog", "IDEA", "Families cataloging physical drawers", "$ estate SaaS · executor assist", "concepts/ideas/IDEA_estate_drawer_catalog.md", "backlog"),
    ("pedigree", "Fabulous Pedigree Antidote", "IDEA", "Genealogy accuracy nerds", "$ report sales", "concepts/ideas/IDEA_fabulous_pedigree_antidote.md", "backlog"),
    ("story_mine", "Story Mine", "PROPOSAL", "Brian · game writers · 4–6M word archive", "$ IP catalog → games · licensing", "drop_pile/proposals/inbox/PROPOSAL_cb2_story_mine.md", "backlog"),
    ("sarah_appt", "Sarah Appointment Lane", "PROPOSAL", "Sarah · seminary schedule", "$ low-intrusion SaaS", "drop_pile/proposals/inbox/PROPOSAL_sarah_appointment_lane.md", "money"),
    ("label_gun", "Handheld Label Gun", "PROPOSAL", "Brian · asset tagging", "$0 tool · saves time", "drop_pile/proposals/inbox/PROPOSAL_brian_gun_styled_printer.md", "backlog"),
    ("net_failover", "Dual-SIM Failover", "PROPOSAL", "Home server uptime", "$0 ops · avoids downtime", "drop_pile/proposals/PROPOSALS_MASTER_LIST.md", "platform"),
    ("fred", "Fred Team Desk", "LIVE", "Brian phone · one-word routing", "$0 command surface", "fred.hitme.dev/team_desk", "platform"),
    ("george", "George Echo Voice", "LIVE", "Brian room · AWS Bedrock voice", "$0 home assistant · upgrades memory", "fleet/GEORGE.txt", "platform"),
    ("clerk", "Clerk / Gem Catalog", "DYING→CLERK", "CB1 Drive librarian", "$0 ops · enables ship lanes", "fleet/bus/cpt_to_gem.txt", "platform"),
    ("checkin", "Fleet Checkin / TV", "LIVE", "Brian walking garage", "$0 visibility", "hitme.dev/checkin", "platform"),
    ("picture_inbox", "Picture Inbox", "LIVE", "Brian photo drops", "$0 routing to Gem", "fleet/bus/PICTURE_INBOX.txt", "platform"),
    ("lester6", "Lester6 Slave Fleet", "ONGOING", "3 boxes · Gemini + Cursor", "$0 automation backbone", "lester/GOAL_ALL_LOCAL_LESTER_SLAVES.md", "platform"),
    ("seminary", "Seminary Application", "LIVE", "Sarah seminary path", "$0 family · possible content", "/seminary", "creative"),
    ("readsy", "Readsy Signup", "PARK", "Human once · Playwright after", "$ automation SaaS", "fleet/bus/IDEAS.txt", "backlog"),
    ("mesh_qr", "Mesh Radio QR Fleet", "PARK", "Phone join mesh instantly", "$0 fleet extension", "fleet/bus/IDEAS.txt", "backlog"),
    ("reggae", "Reggae Master Design", "NEW", "Gem/Uncle · new project UI law", "$0 design system", "fleet/design/REGGAE_MASTER.txt", "platform"),
    ("insomniac", "Insomniac Power Fix", "OPEN", "CB1 stay awake plugged in", "$0 reliability", "insomniac.txt", "platform"),
    ("stripe_cards", "Card Reader Stripe", "LIVE", "Scanner upsell after 6 free", "$$ subscription · test 4242", "lester/baseball_cards/STRIPE_SETUP.md", "money"),
    ("fruition", "Fruition Roll Board", "LIVE", "Brian pick A/B/C ship lane", "$0 decision support", "fleet/bus/FRUITION_BOARD.txt", "platform"),
    ("dog_trust", "Dog Trust Test", "PARKED", "Internal trust experiment", "$0 · not a crew member", "fleet/DEAD_WORDS.txt", "backlog"),
    ("camel_spike_05", "Camel v0.5 Continue", "SPIKE", "Game design iteration", "$0 R&D", "drop_pile/done/CAMEL_v0.5_continue.md", "spike"),
    ("camel_spike_06", "Camel v0.6 Dynasty", "SPIKE", "Game design iteration", "$0 R&D", "drop_pile/done/CAMEL_v0.6_dynasty.md", "spike"),
    ("camel_spike_07", "Camel v0.7 Home vs Road", "SPIKE", "Game design iteration", "$0 R&D", "drop_pile/done/CAMEL_v0.7_design_home_vs_road.md", "spike"),
    ("spike_gen", "SPIKE 3000 Generations", "SPIKE", "Genealogy math research", "$0 research", "drop_pile/done/SPIKE_3000_generations_math.md", "spike"),
    ("spike_dai", "SPIKE Yellow Emperor Gap", "SPIKE", "Genealogy research", "$0 research", "drop_pile/done/SPIKE_yellow_emperor_dai_gap.md", "spike"),
    ("spike_fair", "SPIKE Intersections Fair", "SPIKE", "Genealogy connections", "$0 research", "drop_pile/done/SPIKE_intersections_connections_fair.md", "spike"),
    ("mick_index", "Mick Index", "PRODUCE", "Collector browse index", "$ list sales aid", "/mick", "money"),
    ("garage_radio", "Garage Radio", "PRODUCE", "Brian vibe · card lore radio", "$0 engagement", "brian_produce radio", "creative"),
    ("fortune", "Garage Fortune", "PRODUCE", "Brian daily nudge", "$0 morale", "brian_produce fortune", "creative"),
    ("scan_pager", "Scan One-Pager", "PRODUCE", "New scanner onboarding", "$ converts to Stripe", "brian_produce scan", "money"),
    ("audio_done", "Audio Done Receipts", "LIVE", "Brian · hear what finished", "$0 ops joy · mobile /done", "fleet/AUDIO_DONE.txt", "platform"),
    ("team_order", "Team Order Log", "LIVE", "Brian one-line who gets job", "$0 routing", "fleet/indie_loop/TEAM_ORDER.txt", "platform"),
]


def _pack(rows: list[tuple[str, str, str, str, str, str, str]], *, source: str) -> dict:
    ts = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    projects = [
        {
            "id": r[0],
            "name": r[1],
            "status": r[2],
            "end_user": r[3],
            "profit": r[4],
            "source": r[5],
            "tier": r[6],
        }
        for r in rows
    ]
    return {
        "updated": ts,
        "source": source,
        "count": len(projects),
        "by_tier": {
            t: sum(1 for p in projects if p["tier"] == t)
            for t in ("ship", "money", "platform", "creative", "backlog", "spike")
        },
        "projects": projects,
    }


def main() -> None:
    bus = bus_root()
    safe_mkdir(bus / "fleet")
    bunny = _pack(BUNNY_ROWS, source="bunny · keaton INDEX + GEM sprint + FRUITION")
    archive = _pack(ARCHIVE_ROWS, source="daddy archive scan")
    (bus / "fleet/PROJECTS_CATALOG.json").write_text(
        json.dumps(bunny, indent=2) + "\n", encoding="utf-8"
    )
    (bus / "fleet/PROJECTS_ARCHIVE.json").write_text(
        json.dumps(archive, indent=2) + "\n", encoding="utf-8"
    )
    (bus / "fleet/PROJECTS_CATALOG.txt").write_text(
        f"PROJECTS — Bunny truth · {bunny['count']} · {bunny['updated']}\n"
        f"UI: https://hitme.dev/projects\n"
        f"Law: fleet/PROJECTS_BUNNY.txt\n"
        f"Archive ({archive['count']}): fleet/PROJECTS_ARCHIVE.json\n",
        encoding="utf-8",
    )
    print(f"Bunny catalog: {bunny['count']} · archive: {archive['count']}")


if __name__ == "__main__":
    main()
