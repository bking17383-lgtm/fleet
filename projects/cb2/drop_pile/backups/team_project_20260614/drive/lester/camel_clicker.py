#!/usr/bin/env python3
"""
The Standard Camel: Dung & Trader Tycoon (Terminal Edition)
Click dung, sell camels, marry wisely (only one wife — divorce costs half).
"""

import os
import json
import time
import random
import subprocess
import threading
import struct
import math
import wave

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(_SCRIPT_DIR, "standard_camel_save.json")

CAMEL_PRICES = {"std": 50, "bac": 250, "rac": 1000, "gld": 5000}
UPGRADE_PRICES = {"sauce": 30, "beard": 150, "mask": 800}
DUNG_PER_CAMEL = 2  # all types poop equally; per game-day when a day ends
RACE_REGISTER_FEE = 350  # investment sink — registering a circuit camel
SELL_CAMEL_REFUND = 0.10  # 90% loss — frees a land slot to pivot build

CAMEL_LABELS = {
    "std": "Standard (1 hump)",
    "bac": "Bactrian (2 hump)",
    "rac": "Al Kharid Racer",
    "gld": "Golden",
}

DAY_SECONDS = 75  # legacy; days are turn-based now (see advance_day)

KID_MATURE_DAYS = 8
KID_INTERVAL_DAYS = 3
MAX_KIDS = 4
MARRIAGE_THRESHOLD = 50_000  # marry in marriage hall
ESTATE_THRESHOLD = 500_000  # estate broker fork (oil / tourism / decoys)
WIN_FORTUNE = 1_000_000  # dynasty victory fortune gate
BED_LOCK_THRESHOLD = 50  # below this: locked in bed until recovered
CAMELS_PER_LAND = 5  # first parcel = 5 acres / 5 camel slots
RACE_UNLOCK_COINS = 3_500
RACE_ENTRY = {"rac": 800, "gld": 2500}
RACE_BASE_SPEED = {"rac": 52, "gld": 78}
CHAMPION_UPGRADE_COSTS = [6_000, 18_000, 55_000, 160_000]
LAND_COST_FIRST = 2_000_000   # parcel 2
LAND_COST_AFTER = 5_000_000   # parcel 3+

FOREIGN_SHARE_ITEMS = [
    "English vitals",
    "Persian blue glass",
    "a chipped Roman oil lamp",
    "Indian spice samples",
    "Greek counting beads",
    "Phoenician purple dye (tiny jar)",
    "Chinese silk scrap",
    "Egyptian papyrus fragment",
    "Scythian belt buckle",
]

ODDBALL_ARTIFACTS = [
    "Bronze camel bell (Bactrian trade mark)",
    "Sand-polished meteorite shard",
    "Carved ivory chess piece — knight is a goat",
    "Lead curse tablet (against rival merchants)",
    "Glass eye from a statue (nobody asks which)",
    "Obsidian mirror, slightly haunted",
    "Stamped seal of an unknown king",
    "Iron horseshoe (wrong animal, right luck)",
    "Beeswax tablet with half a recipe",
    "Coin hoard in a hollow hoof",
    "Desert rose crystal cluster",
    "Faded map scrap — east arrow circled twice",
]

GAME_VERSION = "v1.0.1"
DAWN_REGEN_MULT = 1.25  # herbs / dawn — 25% faster health regen each new day
FAILURE_DAYS_AT_ZERO = 5  # consecutive game-days at 0 health = total failure
INTRO_MUSIC_NAMES = ("intro_music.mp3", "intro_music.wav", "intro_music.ogg")
INTRO_GENERATED_WAV = "_intro_theme.wav"

# Holy relics — found wandering (menu H). kind: consumable (use once) or passive (kept)
RELIC_DEFS = {
    "healing_clay": {
        "name": "Healing clay (Ein Gedi)",
        "kind": "consumable",
        "desc": "Anoint wounds — +18 health",
    },
    "mirage_water": {
        "name": "Mirage water in a stone cup",
        "kind": "consumable",
        "desc": "Drink — +12 health",
    },
    "saints_balm": {
        "name": "Saint's balm (Qumran jar)",
        "kind": "consumable",
        "desc": "Rare salve — +25 health",
    },
    "circuit_oil": {
        "name": "Circuit oil (myrrh + sand)",
        "kind": "consumable",
        "desc": "Rub on racer — best camel +8 speed forever",
    },
    "winners_luck": {
        "name": "Winner's luck (bedouin charm)",
        "kind": "consumable",
        "desc": "Next race +12 effective speed",
    },
    "race_amulet": {
        "name": "Racer's amulet (bronze hump)",
        "kind": "passive",
        "desc": "Passive: all racers +5 speed",
    },
    "dowry_pouch": {
        "name": "Buried dowry pouch",
        "kind": "consumable",
        "desc": "Coins toward a household — +$4,500",
    },
    "bride_scroll": {
        "name": "Bride-price scroll (Phoenician)",
        "kind": "passive",
        "desc": "Passive: marriage costs $20k less",
    },
    "wedding_incense": {
        "name": "Wedding incense bundle",
        "kind": "consumable",
        "desc": "Families notice you — +$2,500 and +6 health",
    },
    "desert_coin": {
        "name": "Lost merchant's purse",
        "kind": "consumable",
        "desc": "Open — +$900",
    },
}

WANDER_FINDS = [
    ("healing_clay", 14),
    ("mirage_water", 12),
    ("saints_balm", 5),
    ("circuit_oil", 8),
    ("winners_luck", 9),
    ("race_amulet", 4),
    ("dowry_pouch", 10),
    ("bride_scroll", 5),
    ("wedding_incense", 8),
    ("desert_coin", 11),
]

DESERT_BOOKS = [
    "Book of Sandstorms (Qumran fragment)",
    "Luke generation scroll — longer count",
    "Phoenician trade routes, water-stained",
    "Ten Kings battle — Rig Veda excerpt",
    "Basque cognates appendix (disputed)",
    "Herodotus vs Judges: lion chapter",
]

# Only oil & tourism truly change mechanics; ~48 decoys are traps / vanity
REAL_CAREERS = {
    "oil": {
        "pitch": "Sell your estate — Bedouin syndicate offers CRUDE under the grazing lease.",
        "title": "Oil Baron of the Empty Quarter",
        "coin_per_well_day": 420,
        "health_fume_day": 2,
    },
    "tourism": {
        "pitch": "Sell your estate — Sultan's nephew builds LUXURY DESERT TOURS from your stable.",
        "title": "Minister of Sand & Hospitality",
        "tour_sale_bonus": 0.55,
        "tour_chance_day": 0.35,
        "visitor_coin_day": 180,
    },
}

DECOY_PITCHES = [
    ("Missile technology (warehouse of cardboard rockets)", "General of Paper Fire"),
    ("Blockchain CamelCoin — 'to the dunes!'", "Chief HODL Officer"),
    ("NFT series: Limited Edition Dung Pixels", "Baron of JPEGs"),
    ("Perpetual kebab franchise rights (no kitchens included)", "Sultan of Sauce IP"),
    ("Metaverse oasis — VR mirage subscription", "Sheikh of Lag"),
    ("AI oracle that predicts sandstorms (always says 'maybe')", "Prophet of Perhaps"),
    ("Pyramid scheme — literally a small pyramid", "Pharaoh of Upline"),
    ("Exclusive sand-import monopoly (it's everywhere)", "Duke of Granularity"),
    ("Camelcoin staking yield (paid in more camelcoin)", "DeFi Bedouin"),
    ("Wellness retreat: crystal dung harmonics", "Guru of Resonant Filth"),
    ("Export license for premium air ( jars not included )", "Baron of Breathing"),
    ("Strategic reserve of expired kebab sauce", "Commissar of Condiments"),
    ("Timeshare on a mirage (week 53 available)", "Mirage Timeshare Lord"),
    ("Patent on walking in straight lines", "IP Sheikh"),
    ("Subscription box: Mystery Dung Monthly", "Curator of Surprises"),
    ("Influencer contract — your camels on RuneTok", "Content Caliph"),
    ("Offshore dung banking (taxes unknown, sand certain)", "Swiss Sand Banker"),
    ("Rocket camels — legs sold separately", "Aerospace Nomad"),
    ("Desert NFT camel racing (horses not included)", "Race Commissioner"),
    ("Essential oils distilled from essential dung", "MLM Empress"),
    ("Diplomatic immunity in Pollnivneach (not valid anywhere)", "Honorary Consul"),
    ("Laser pointer technology for herding (cat optional)", "Tech Vizier"),
    ("Quantum sand — may or may not exist until observed", "Quantum Bedouin"),
    ("Celebrity endorsement from a famous goat", "Goat Whisperer"),
    ("Mineral rights to invisible limestone", "Limestone Pretender"),
    ("Export monopoly on left-handed tea cups", "Ceramic Warlord"),
    ("Space tourism — low orbit dung dump", "Orbital Merchant"),
    ("Premium camel insurance (claims denied artform)", "Underwriter of Denial"),
    ("Rare earth elements (actually just earth)", "Geology Influencer"),
    ("Memetic warfare division — mean tweets", "Lord of Ratio"),
    ("Carbon credits for methane camels (honest?)", "Climate Sheikh"),
    ("Archaeology rights to future ruins", "Anticipatory Indiana"),
    ("Franchise: Gorgeous Ali's (you keep the debt)", "Franchisee of Regret"),
    ("Solar farm where sun already was", "Sunlight Middleman"),
    ("Import/export of sand to adjacent sand", "Sand Arbitrageur"),
    ("VIP access to queue for nothing", "Queue Sultan"),
    ("Weaponized nostalgia — 'remember yesterday?'", "Minister of Yesterday"),
    ("Biotech: glow-in-dark dung (glow not included)", "Bio Baron"),
    ("Exclusive rights to echo sound effects", "Echo Mogul"),
    ("Desalination via positive thinking", "Hydration Optimist"),
    ("Camel Uber pivot (no drivers, no app)", "Ride-share Pretender"),
    ("Sovereign citizen passport (laminated sand)", "Micronation CEO"),
    ("Rare spice route — delivers only cinnamon air", "Spice Theoretician"),
    ("Defensive moat filled with more sand", "Moat Enthusiast"),
    ("Celebrity marriage to a wealthy rock", "Rock Consort"),
    ("IPO of your shadow (prospectus: shady)", "Shadow Broker"),
    ("Televangelism network — send coins", "Reverend of Receipts"),
    ("Alien technology (garage opener from 1998)", "X-Files Investor"),
    ("Premium graveyard plots for expired ideas", "Cemetery of Startups"),
]

WIVES = {
    "title": {
        "name": "Fatima the Fierce",
        "blurb": "Mean. Demands dung tribute daily. Grants royal title.",
        "daily_dung": 40,
        "title": "Sheikh of the Sands",
        "sell_bonus": 0.12,
        "market_floor": 3,
    },
    "kind": {
        "name": "Layla the Gentle",
        "blurb": "Kind. Slows filth sickness and restores health.",
        "health_regen_day": 5,
        "decay_mult": 0.55,
    },
    "kids": {
        "name": "Zahra the Fruitful",
        "blurb": "Kids multiply labor; young ones take a cut of sales.",
        "effort_per_kid": 0.18,
        "mature_effort": 0.10,
        "profit_cut_per_young": 0.14,
    },
}

SANITATION = {
    1: {"name": "Lime Bucket", "cost": 120, "decay_mult": 0.82, "regen_day": 1},
    2: {"name": "Desert Well", "cost": 480, "decay_mult": 0.68, "regen_day": 3},
    3: {"name": "Turkish Bath", "cost": 1600, "decay_mult": 0.52, "regen_day": 6},
}

KID_NAMES = ["Yusuf", "Amira", "Hassan", "Nadia", "Omar", "Leila", "Karim", "Safa"]

# loving / standard / hateful — rolled at birth
KID_TRAITS = {
    "loving": {
        "label": "loving",
        "effort_young": 0.22,
        "effort_mature": 0.14,
        "cut_young": 0.08,
        "health_day": 4,
        "death_chance_day": 0.012,
    },
    "standard": {
        "label": "standard",
        "effort_young": 0.14,
        "effort_mature": 0.09,
        "cut_young": 0.14,
        "health_day": 0,
        "death_chance_day": 0.028,
    },
    "hateful": {
        "label": "hates trade",
        "effort_young": -0.12,
        "effort_mature": -0.06,
        "cut_young": 0.10,
        "health_day": -3,
        "death_chance_day": 0.022,
        "sabotage_day": 0.18,
        "sabotage_sale": 0.11,
    },
}

ASCII_CAMEL = r"""
        ,,__
       / o  `\      ~ GORGEOUS ALI'S DISCOUNT CAMEL STORE ~
      |  __   \
      | /  \   |    "Dung is the currency of the desert, friend!
      |/    \  |     Marriage is the tax on the soul."
             \ \
             / /__
            / /_ /
           /____/
"""


def _write_intro_wav(path):
    """Somber generated theme — zero deps fallback when no intro_music.* bundled."""
    framerate = 22050
    notes = [
        (392.00, 0.55),
        (349.23, 0.55),
        (329.63, 0.70),
        (293.66, 0.90),
        (261.63, 1.10),
        (293.66, 0.70),
        (329.63, 0.90),
        (349.23, 1.20),
    ]
    frames = []
    for freq, sec in notes:
        n = int(framerate * sec)
        for i in range(n):
            t = i / framerate
            env = min(1.0, i / (framerate * 0.08), (n - i) / (framerate * 0.12))
            sample = int(5200 * env * math.sin(2 * math.pi * freq * t))
            frames.append(struct.pack("<h", sample))
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(b"".join(frames))


def _play_audio_file(path):
    players = [
        ["paplay", path],
        ["aplay", "-q", path],
        ["mpg123", "-q", path],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
    ]
    for cmd in players:
        try:
            subprocess.run(
                cmd,
                timeout=90,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    return False


def play_intro_music():
    def _run():
        for name in INTRO_MUSIC_NAMES:
            path = os.path.join(_SCRIPT_DIR, name)
            if os.path.isfile(path) and _play_audio_file(path):
                return
        gen = os.path.join(_SCRIPT_DIR, INTRO_GENERATED_WAV)
        try:
            if not os.path.isfile(gen):
                _write_intro_wav(gen)
            _play_audio_file(gen)
        except OSError:
            pass

    threading.Thread(target=_run, daemon=True).start()


def show_intro(failure=False):
    clear_screen()
    play_intro_music()
    if failure:
        print("\n  ☠  TOTAL FAILURE — the line ends in the wilderness\n")
    print("  ♪  ♪  ♪\n")
    print("  ============================================================")
    print("              T H E   S T A N D A R D   C A M E L")
    print("  ============================================================\n")
    lines = [
        "  Your father has just died.",
        "  Your mother chose to join him.",
        "",
        "  You, alone, can return the family",
        "  to glorious prominence.",
        "",
        "  How will you use your 5 acres",
        "  of wilderness?",
    ]
    for line in lines:
        print(line)
        time.sleep(0.65 if line else 0.35)
    print("\n  ============================================================")
    input("\n  [ Enter to begin ] ")
    clear_screen()


class CamelClicker:
    def __init__(self):
        self.coins = 100.0
        self.dung = 0.0
        self.camels = {"std": 0, "bac": 0, "rac": 0, "gld": 0}
        self.upgrades = {"sauce": 0, "beard": 0, "mask": 0}
        self.total_clicks = 0
        self.last_tick = time.time()
        self.market_price = 3
        self.inflation_camels = dict(CAMEL_PRICES)
        self.health = 100.0
        self.sanitation = 0
        self.wife = None
        self.kids = []
        self.game_day = 0.0
        self.days_since_kid = 0.0
        self.pending_events = []
        self.career = "merchant"
        self.estate_resolved = False
        self.vanity_title = ""
        self.oil_wells = 0
        self.tour_fame = 0
        self.tour_group_today = False
        self.camel_inflation_rate = 1.22
        self.land_parcels = 1  # parcel 1 = starter grazing (holds 5)
        self.race_camels = []
        self.pending_dead_racer = None
        self.last_pot_value = 0
        self.security_stock = 0
        self.desert_books = 0
        self.book_library = []
        self.books_studied = 0
        self.game_won = False
        self.artifacts = []
        self.holy_relics = []
        self.next_race_luck = 0
        self.home_snapshot = None
        self.days_since_race = 999
        self.on_silk_road = False
        self.silk_road_days_left = 0
        self.days_at_zero_health = 0
        self.herbs_used_today = False
        self._next_racer_id = 1
        self.capture_home_snapshot()

    def to_dict(self):
        return {
            "coins": self.coins,
            "dung": self.dung,
            "camels": self.camels,
            "upgrades": self.upgrades,
            "total_clicks": self.total_clicks,
            "inflation_camels": self.inflation_camels,
            "health": self.health,
            "sanitation": self.sanitation,
            "wife": self.wife,
            "kids": self.kids,
            "game_day": self.game_day,
            "days_since_kid": self.days_since_kid,
            "career": self.career,
            "estate_resolved": self.estate_resolved,
            "vanity_title": self.vanity_title,
            "oil_wells": self.oil_wells,
            "tour_fame": self.tour_fame,
            "land_parcels": self.land_parcels,
            "race_camels": self.race_camels,
            "pending_dead_racer": self.pending_dead_racer,
            "last_pot_value": self.last_pot_value,
            "security_stock": self.security_stock,
            "desert_books": self.desert_books,
            "book_library": self.book_library,
            "books_studied": self.books_studied,
            "game_won": self.game_won,
            "artifacts": self.artifacts,
            "holy_relics": self.holy_relics,
            "next_race_luck": self.next_race_luck,
            "home_snapshot": self.home_snapshot,
            "days_since_race": self.days_since_race,
            "on_silk_road": self.on_silk_road,
            "silk_road_days_left": self.silk_road_days_left,
            "days_at_zero_health": self.days_at_zero_health,
            "herbs_used_today": self.herbs_used_today,
            "next_racer_id": self._next_racer_id,
        }

    def load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                self.coins = data.get("coins", 100.0)
                self.dung = data.get("dung", 0.0)
                self.camels = data.get("camels", self.camels)
                self.upgrades = data.get("upgrades", self.upgrades)
                self.total_clicks = data.get("total_clicks", 0)
                self.inflation_camels = data.get("inflation_camels", self.inflation_camels)
                self.health = data.get("health", 100.0)
                self.sanitation = data.get("sanitation", 0)
                raw_wife = data.get("wife")
                self.wife = raw_wife if raw_wife in WIVES else None
                self.kids = data.get("kids", []) if self.wife == "kids" else []
                self.game_day = data.get("game_day", 0.0)
                self.days_since_kid = data.get("days_since_kid", 0.0)
                self.career = data.get("career", "merchant")
                self.estate_resolved = data.get("estate_resolved", False)
                self.vanity_title = data.get("vanity_title", "")
                self.oil_wells = data.get("oil_wells", 0)
                self.tour_fame = data.get("tour_fame", 0)
                self.land_parcels = max(1, data.get("land_parcels", 1))
                self.race_camels = data.get("race_camels", [])
                self.pending_dead_racer = data.get("pending_dead_racer")
                self.last_pot_value = data.get("last_pot_value", 0)
                self.security_stock = data.get("security_stock", 0)
                self.desert_books = data.get("desert_books", 0)
                self.book_library = data.get("book_library", [])
                self.books_studied = data.get("books_studied", 0)
                self.game_won = data.get("game_won", False)
                self.artifacts = data.get("artifacts", [])
                self.holy_relics = data.get("holy_relics", [])
                self.next_race_luck = data.get("next_race_luck", 0)
                self.home_snapshot = data.get("home_snapshot")
                self.days_since_race = data.get("days_since_race", 999)
                self.on_silk_road = data.get("on_silk_road", False)
                self.silk_road_days_left = data.get("silk_road_days_left", 0)
                self.days_at_zero_health = data.get("days_at_zero_health", 0)
                self.herbs_used_today = data.get("herbs_used_today", False)
                self._next_racer_id = data.get("next_racer_id", 1)
                self._migrate_kids()
                self._migrate_racer_ownership()
                if not self.home_snapshot:
                    self.capture_home_snapshot()
            except Exception:
                pass
        self.last_tick = time.time()

    def _check_fortune_milestone(self):
        if self.coins >= ESTATE_THRESHOLD and not self.estate_resolved:
            if not any("Estate brokers" in e for e in self.pending_events):
                self.pending_events.append(
                    f"⚠ Estate brokers circle you at ${ESTATE_THRESHOLD:,}. "
                    "Menu 8 — sell the stable?"
                )

    def career_label(self):
        if self.career == "oil":
            return REAL_CAREERS["oil"]["title"]
        if self.career == "tourism":
            return REAL_CAREERS["tourism"]["title"]
        if self.vanity_title:
            return f"{self.vanity_title} (still a dung merchant)"
        return "Camel Merchant"

    def can_marry(self):
        need = self.effective_marriage_threshold()
        if self.coins < need:
            return False, f"Fortune must reach ${need:,} before marriage."
        return True, ""

    def effective_marriage_threshold(self):
        need = MARRIAGE_THRESHOLD
        if "bride_scroll" in self.holy_relics:
            need -= 20_000
        return max(5_000, need)

    def relic_race_bonus(self):
        bonus = 0
        if "race_amulet" in self.holy_relics:
            bonus += 5
        bonus += self.next_race_luck
        return bonus

    def _pick_wander_relic(self):
        pool = list(WANDER_FINDS)
        if self.health < 50:
            pool.extend([("healing_clay", 10), ("mirage_water", 8), ("saints_balm", 6)])
        if not self.wife and self.coins < self.effective_marriage_threshold():
            pool.extend([("dowry_pouch", 8), ("bride_scroll", 4), ("wedding_incense", 6)])
        if self.race_camels or self.camels.get("rac", 0) or self.camels.get("gld", 0):
            pool.extend([("circuit_oil", 6), ("winners_luck", 6), ("race_amulet", 3)])
        ids = [r[0] for r in pool]
        weights = [r[1] for r in pool]
        choice = random.choices(ids, weights=weights, k=1)[0]
        if RELIC_DEFS[choice]["kind"] == "passive" and choice in self.holy_relics:
            return random.choice(["healing_clay", "mirage_water", "desert_coin"])
        return choice

    def wander_desert(self):
        if self.on_silk_road:
            return "The Silk Road calls — finish that journey first."
        self.health -= random.randint(3, 8)
        self.health = max(0, self.health)
        roll = random.random()
        if roll < 0.28:
            self.advance_day(1)
            return (
                f"Empty dunes. Wind only. The wander exhausts you. "
                f"Day {int(self.game_day)}."
            )
        if roll < 0.36:
            self.health -= random.randint(5, 12)
            self.health = max(0, self.health)
            self.advance_day(1)
            return f"Scorpion! Stung in the wadi. Day {int(self.game_day)}."
        relic_id = self._pick_wander_relic()
        self.holy_relics.append(relic_id)
        name = RELIC_DEFS[relic_id]["name"]
        self.advance_day(1)
        return (
            f"Holy find: {name}! ({RELIC_DEFS[relic_id]['desc']}) "
            f"Use in menu H. Day {int(self.game_day)}."
        )

    def use_holy_relic(self, slot):
        if slot < 1 or slot > len(self.holy_relics):
            return "Invalid relic number."
        relic_id = self.holy_relics[slot - 1]
        if RELIC_DEFS.get(relic_id, {}).get("kind") != "consumable":
            return f"{RELIC_DEFS[relic_id]['name']} is passive — it stays with you."
        self.holy_relics.pop(slot - 1)
        if relic_id == "healing_clay":
            self.health = min(100, self.health + 18)
            return "Healing clay — wounds close. +18 health."
        if relic_id == "mirage_water":
            self.health = min(100, self.health + 12)
            return "Mirage water — throat and spirit ease. +12 health."
        if relic_id == "saints_balm":
            self.health = min(100, self.health + 25)
            return "Saint's balm — the body remembers hope. +25 health."
        if relic_id == "circuit_oil":
            champ = self.best_racer()
            if not champ:
                self.holy_relics.append(relic_id)
                return "No racer to anoint. Keep the oil."
            champ["speed"] += 8
            return f"Circuit oil on {champ['name']} — speed {champ['speed']} (+8)."
        if relic_id == "winners_luck":
            self.next_race_luck = 12
            return "Winner's luck tucked in your sash. Next race +12 speed."
        if relic_id == "dowry_pouch":
            self.coins += 4500
            return "Dowry pouch — +$4,500 toward marriage."
        if relic_id == "wedding_incense":
            self.coins += 2500
            self.health = min(100, self.health + 6)
            return "Wedding incense — whispers at the oasis. +$2,500, +6 health."
        if relic_id == "desert_coin":
            self.coins += 900
            return "Lost purse — +$900."
        return "The relic crumbles to dust."

    def brew_desert_herbs(self):
        """Once per day — health option without waiting out bed lock."""
        if self.herbs_used_today:
            return "Herbs already brewed today — dawn brings more."
        self.herbs_used_today = True
        _, regen = self.sanitation_stats()
        gain = max(6, int((4 + regen) * DAWN_REGEN_MULT))
        self.health = min(100, self.health + gain)
        return f"Desert herbs steep by the fire. +{gain} health (once today)."

    def is_bedridden(self):
        return self.health <= BED_LOCK_THRESHOLD

    def is_total_failure(self):
        return self.days_at_zero_health >= FAILURE_DAYS_AT_ZERO

    def rest_in_bed(self):
        gain = 8
        if self.wife == "kind":
            gain += 7
        _, regen_day = self.sanitation_stats()
        gain += regen_day // 2
        gain = int(gain * DAWN_REGEN_MULT)
        self.health = min(100.0, self.health + gain)
        self.advance_day(1)
        if self.health > BED_LOCK_THRESHOLD:
            return f"Day {int(self.game_day)}: you rise at {int(self.health)}% health."
        return f"Day {int(self.game_day)}: still weak at {int(self.health)}% (need >{BED_LOCK_THRESHOLD}%)."

    def full_reset(self):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        fresh = CamelClicker()
        for attr in fresh.__dict__:
            setattr(self, attr, getattr(fresh, attr))
        self.last_tick = time.time()

    def total_camels(self):
        """All owned camels count toward land — including racers at home on the circuit."""
        return sum(self.camels.values())

    def _registered_racers(self, ctype=None):
        n = 0
        for r in self.race_camels:
            if ctype is None or r["ctype"] == ctype:
                n += 1
        if self.pending_dead_racer:
            if ctype is None or self.pending_dead_racer.get("ctype") == ctype:
                n += 1
        return n

    def camel_capacity(self):
        return self.land_parcels * CAMELS_PER_LAND

    def land_cost(self):
        if self.land_parcels < 2:
            return LAND_COST_FIRST
        return LAND_COST_AFTER

    def capture_home_snapshot(self):
        """Picture of home + herd (+ kids) — merchant carries this memory on the road."""
        lines = [
            "  .---------------------------.",
            "  |      YOUR HOME & HERD     |",
            "  '---------------------------'",
            f"   land: {'[■] ' * self.land_parcels}",
        ]
        labels = {"std": "1h", "bac": "2h", "rac": "R", "gld": "G"}
        herd = []
        for ctype, count in self.camels.items():
            herd.extend([labels[ctype]] * count)
        if herd:
            shown = " ".join(herd[:14])
            if len(herd) > 14:
                shown += f" +{len(herd)-14}"
            lines.append(f"   camels: {shown}")
        else:
            lines.append("   camels: (empty stable)")
        kids = self._living_kids()
        if kids:
            names = ", ".join(k["name"] for k in kids)
            lines.append(f"   kids: {names}")
        elif self.wife:
            lines.append(f"   home: {WIVES[self.wife]['name']}")
        else:
            lines.append("   home: bachelor stable")
        lines.append(f"   captured day {int(self.game_day)}")
        self.home_snapshot = {"day": int(self.game_day), "lines": lines}
        return self.home_snapshot

    def grow_land(self):
        cost = self.land_cost()
        if self.coins < cost:
            return False, f"Need ${cost:,} to irrigate another parcel (+{CAMELS_PER_LAND} camel slots)."
        self.coins -= cost
        self.land_parcels += 1
        self.capture_home_snapshot()
        return True, f"Land grown! Capacity: {self.camel_capacity()} camels ({self.land_parcels} parcels)."

    def try_buy_stable_camel(self, ctype):
        if self.total_camels() >= self.camel_capacity():
            cost = self.land_cost()
            return False, (
                f"No grazing room! {self.total_camels()}/{self.camel_capacity()} camels. "
                f"Win race pots for land — or pay ${cost:,} (brutal)."
            )
        cost = self.inflation_camels[ctype]
        if self.coins < cost:
            return False, "Not enough Dinars!"
        self.coins -= cost
        self.camels[ctype] += 1
        self.inflation_camels[ctype] = int(cost * self.camel_inflation_rate)
        self.capture_home_snapshot()
        return True, f"Bought 1 {ctype} camel ({self.total_camels()}/{self.camel_capacity()})."

    def _sellable_camels(self, ctype):
        return max(0, self.camels.get(ctype, 0) - self._registered_racers(ctype))

    def sell_stable_camel(self, ctype):
        if ctype not in CAMEL_LABELS:
            return False, "Unknown camel type."
        sellable = self._sellable_camels(ctype)
        if sellable <= 0:
            if self._registered_racers(ctype) > 0:
                return False, (
                    f"All {CAMEL_LABELS[ctype]} on circuit — "
                    "redeem/abandon racers before selling this type."
                )
            return False, f"No {CAMEL_LABELS[ctype]} to sell."
        refund = max(1, int(self.inflation_camels[ctype] * SELL_CAMEL_REFUND))
        self.camels[ctype] -= 1
        self.coins += refund
        self.capture_home_snapshot()
        return (
            True,
            f"Sold {CAMEL_LABELS[ctype]} for ${refund:,} (90% loss). "
            f"{self.total_camels()}/{self.camel_capacity()} slots used.",
        )

    def _migrate_racer_ownership(self):
        """Old saves decremented stable when registering — restore owned count."""
        for ctype in ("rac", "gld"):
            need = self._registered_racers(ctype)
            if self.camels.get(ctype, 0) < need:
                self.camels[ctype] = need

    def register_racer_from_stable(self, ctype):
        if ctype not in ("rac", "gld"):
            return "Only Al Kharid Racers or Golden camels can race."
        unregistered = self.camels.get(ctype, 0) - self._registered_racers(ctype)
        if unregistered <= 0:
            return f"No {ctype} camel free to register (all on circuit or lost)."
        if self.coins < RACE_REGISTER_FEE:
            return f"Registration costs ${RACE_REGISTER_FEE} (training + circuit papers)."
        self.coins -= RACE_REGISTER_FEE
        name = random.choice(["Thunder Hump", "Sand Comet", "Gorgeous Speed", "Ali's Fury", "Pot Winner"])
        racer = {
            "id": self._next_racer_id,
            "name": name,
            "ctype": ctype,
            "speed": RACE_BASE_SPEED[ctype] + random.randint(-4, 6),
            "upgrades": 0,
        }
        self._next_racer_id += 1
        self.race_camels.append(racer)
        self.capture_home_snapshot()
        return (
            f"{name} enters the circuit! Speed {racer['speed']}. "
            f"Still counts on your land ({DUNG_PER_CAMEL}/day)."
        )

    def best_racer(self):
        if not self.race_camels:
            return None
        return max(self.race_camels, key=lambda r: r["speed"] + r["upgrades"] * 12)

    def upgrade_champion(self):
        champ = self.best_racer()
        if not champ:
            return "No race camel. Register a Racer or Golden from stable."
        lvl = champ["upgrades"]
        if lvl >= len(CHAMPION_UPGRADE_COSTS):
            return f"{champ['name']} is max upgraded."
        cost = CHAMPION_UPGRADE_COSTS[lvl]
        if self.coins < cost:
            return f"Need ${cost:,} for upgrade tier {lvl + 1}."
        self.coins -= cost
        champ["upgrades"] += 1
        champ["speed"] += random.randint(6, 14)
        return f"{champ['name']} upgraded! Speed {champ['speed']} (tier {champ['upgrades']})."

    def _roll_pot_reward(self, pot):
        roll = random.random()
        if roll < 0.35:
            return "coins", pot, f"Pot: ${pot:,} Dinars!"
        if roll < 0.55:
            parcels = random.randint(1, 2)
            self.land_parcels += parcels
            self.capture_home_snapshot()
            return "land", parcels, f"Pot: {parcels} LAND parcel(s)! Capacity {self.camel_capacity()}."
        if roll < 0.70:
            art = random.choice(ODDBALL_ARTIFACTS)
            self.artifacts.append(art)
            return "artifact", art, f"Pot: oddball artifact — {art}!"
        if roll < 0.82:
            qty = random.randint(1, 3)
            self.security_stock += qty
            return "military", qty, f"Pot: military supplies x{qty} (security stock {self.security_stock})."
        book = random.choice(DESERT_BOOKS)
        self.desert_books += 1
        self.book_library.append(book)
        return "book", book, f"Pot: whole book found — {book}! (study in library)"

    def _maybe_village_pleasantry(self):
        if self.on_silk_road or random.random() > 0.07:
            return
        roll = random.random()
        if roll < 0.28:
            item = random.choice(FOREIGN_SHARE_ITEMS)
            gift = random.randint(80, 320)
            self.coins += gift
            self.pending_events.append(
                f"Village share: someone bought {item} — neighbors pass it around. (+${gift})"
            )
        elif roll < 0.48:
            self.health = min(100, self.health + random.randint(3, 8))
            self.pending_events.append(
                "Neighbor shares kebab sauce recipe. The air smells hopeful."
            )
        elif roll < 0.62 and self._living_kids():
            kid = random.choice(self._living_kids())
            self.health = min(100, self.health + 4)
            self.pending_events.append(
                f"{kid['name']} draws your camels in the dust. You smile despite yourself."
            )
        elif roll < 0.78:
            place = random.choice(["Petra", "Antioch", "Damascus", "Samarkand", "Kashgar"])
            self.pending_events.append(
                f"A traveler mentions {place} — roads east glitter in the telling."
            )
        elif roll < 0.88 and self.wife == "title" and self.days_since_race >= 6:
            self.health = min(100, self.health + 5)
            self.pending_events.append(
                "Fatima nods: you stayed with the herd. Respect restored a little."
            )
        elif roll < 0.95 and self.wife == "kind":
            self.health = min(100, self.health + 6)
            self.pending_events.append("Layla brews desert tea. Steady hands, steady heart.")
        else:
            bump = random.randint(1, 2)
            self.market_price = min(6, self.market_price + bump)
            self.pending_events.append(
                f"Market hums — dung fetches a little more today (+{bump}/unit)."
            )

    def study_next_book(self):
        if not self.book_library:
            return "No unread books. Win races — pots sometimes yield desert texts."
        title = self.book_library.pop(0)
        self.books_studied += 1
        self.health = min(100, self.health + 5)
        return (
            f"Studied: {title}. "
            f"Lore tier {self.books_studied} (+race speed, +sell insight)."
        )

    def book_sell_bonus(self):
        return 1.0 + self.books_studied * 0.025

    def book_race_bonus(self):
        return self.books_studied * 1.5

    def _legacy_achievement(self):
        if self.books_studied >= 5:
            return True, f"{self.books_studied} desert books mastered"
        for racer in self.race_camels:
            if racer["upgrades"] >= len(CHAMPION_UPGRADE_COSTS):
                return True, f"Champion {racer['name']} fully upgraded"
        if self.land_parcels >= 10:
            return True, f"{self.land_parcels} grazing parcels"
        mature = sum(1 for k in self._living_kids() if k.get("mature"))
        if mature >= 3:
            return True, f"{mature} adult heirs"
        return False, ""

    def can_claim_victory(self):
        if self.game_won:
            return False, "Dynasty already recorded on the scroll."
        if not self.wife:
            return False, "Marry first — a dynasty needs a household."
        if not self.estate_resolved:
            return False, "Resolve the estate fork first (menu 8)."
        if self.coins < WIN_FORTUNE:
            return False, f"Need ${WIN_FORTUNE:,} fortune (you have ${int(self.coins):,})."
        ok, detail = self._legacy_achievement()
        if not ok:
            return (
                False,
                "Leave a legacy: 5 studied books, max champion, 10 land parcels, or 3 adult kids.",
            )
        return True, detail

    def claim_victory(self):
        ok, detail = self.can_claim_victory()
        if not ok:
            return detail
        self.game_won = True
        return f"DYNASTY SECURED — {detail}. The bazaar sings your name."

    def _kid_race_reaction(self, won, racer_name):
        if self.wife != "kids":
            return
        for kid in self._living_kids():
            trait = kid.get("trait", "standard")
            name = kid.get("name", "A child")
            if won:
                if trait == "loving":
                    self.health = min(100, self.health + 5)
                    self.pending_events.append(f"{name} cheers — {racer_name} won!")
                elif trait == "hateful":
                    self.pending_events.append(
                        f"{name} sulks — hates that {racer_name} stole glory."
                    )
            elif trait == "loving":
                self.health -= 8
                self.pending_events.append(
                    f"{name} wails — {racer_name} died on the track."
                )
            elif trait == "hateful":
                self.pending_events.append(
                    f"{name} cackles at {racer_name}'s death. Shameful."
                )
            else:
                self.pending_events.append(
                    f"{name} asks if dead camels go to dung heaven."
                )

    def run_race(self, racer_id):
        if self.pending_dead_racer:
            return "Redeem or abandon your fallen racer first (race menu)."
        racer = next((r for r in self.race_camels if r["id"] == racer_id), None)
        if not racer:
            return "No such racer."
        if self.coins < RACE_UNLOCK_COINS:
            return f"Need ${RACE_UNLOCK_COINS:,} fortune to race at this level."
        entry = RACE_ENTRY[racer["ctype"]]
        if self.coins < entry:
            return f"Entry fee ${entry:,} — too poor to race."
        self.coins -= entry
        pot = int(entry * random.uniform(2.2, 4.8))
        self.last_pot_value = pot
        self.days_since_race = 0
        if self.wife == "title" and random.random() < 0.35:
            self.pending_events.append(
                "Fatima: 'You gamble camels while I am Sheikh?' Respect shaky."
            )
            self.health -= 4

        your_speed = (
            racer["speed"] + racer["upgrades"] * 12
            + self.security_stock * 0.5 + self.book_race_bonus()
            + self.relic_race_bonus()
        )
        if self.next_race_luck:
            self.next_race_luck = 0
        opp_speed = random.randint(45, 95) + int(self.game_day * 0.3)
        win = your_speed + random.randint(-8, 12) >= opp_speed

        if win:
            kind, val, text = self._roll_pot_reward(pot)
            if kind == "coins":
                self.coins += val
            bonus = self.desert_books * 50
            if bonus:
                self.coins += bonus
                text += f" (+${bonus} book lore bonus)"
            self._kid_race_reaction(True, racer["name"])
            self.advance_day(1)
            return f"WIN! {racer['name']} triumphs. {text} — Day {int(self.game_day)}."
        self._kid_race_reaction(False, racer["name"])
        racer["alive_pending"] = True
        self.pending_dead_racer = dict(racer)
        self.race_camels = [r for r in self.race_camels if r["id"] != racer_id]
        redeem = int(pot * 0.75)
        self.advance_day(1)
        return (
            f"LOSS. {racer['name']} falls — the desert claims racers. "
            f"Redeem for ${redeem:,} (3/4 of ${pot:,} pot)? Day {int(self.game_day)}."
        )

    def redeem_fallen_racer(self):
        if not self.pending_dead_racer:
            return "No fallen racer."
        cost = int(self.last_pot_value * 0.75)
        if self.coins < cost:
            return f"Redemption costs ${cost:,} (3/4 of last pot)."
        self.coins -= cost
        r = self.pending_dead_racer
        r.pop("alive_pending", None)
        r["speed"] = max(40, r["speed"] - 5)
        if self.wife == "kind":
            self.health = min(100, self.health + 10)
        self.race_camels.append(r)
        self.pending_dead_racer = None
        extra = " Layla's hands steady you." if self.wife == "kind" else ""
        return f"{r['name']} redeemed for ${cost:,}. Speed {r['speed']}.{extra}"

    def abandon_fallen_racer(self):
        if not self.pending_dead_racer:
            return "No fallen racer."
        name = self.pending_dead_racer["name"]
        ctype = self.pending_dead_racer.get("ctype", "rac")
        self.pending_dead_racer = None
        self.camels[ctype] = max(0, self.camels.get(ctype, 0) - 1)
        self.capture_home_snapshot()
        if self.wife == "kids":
            for kid in self._living_kids():
                if kid.get("trait") == "loving":
                    self.health -= 4
        return f"{name} is lost forever. The book of the desert adds a page."

    def _migrate_kids(self):
        for kid in self.kids:
            if "trait" not in kid:
                kid["trait"] = "standard"
            if "name" not in kid:
                kid["name"] = random.choice(KID_NAMES)
            if "alive" not in kid:
                kid["alive"] = True
        self.kids = [k for k in self.kids if k.get("alive", True)]

    def _roll_kid_trait(self):
        r = random.random()
        if r < 0.22:
            return "loving"
        if r < 0.38:
            return "hateful"
        return "standard"

    def _spawn_kid(self):
        trait = self._roll_kid_trait()
        name = random.choice(KID_NAMES)
        self.kids.append(
            {
                "born_day": self.game_day,
                "mature": False,
                "trait": trait,
                "name": name,
                "alive": True,
            }
        )
        t = KID_TRAITS[trait]
        self.pending_events.append(
            f"Born: {name} ({t['label']}). The desert giveth unpredictably."
        )
        self.capture_home_snapshot()

    def _living_kids(self):
        return [k for k in self.kids if k.get("alive", True)]

    def _kid_cfg(self, kid):
        return KID_TRAITS.get(kid.get("trait", "standard"), KID_TRAITS["standard"])

    def save(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.to_dict(), f, indent=4)
        except Exception:
            pass

    def effort_multiplier(self):
        mult = 1.0
        if self.health <= 0:
            mult *= 0.22
        elif self.health < 20:
            mult *= 0.38
        elif self.health < 45:
            mult *= 0.58
        elif self.health < 65:
            mult *= 0.82
        for kid in self._living_kids():
            cfg = self._kid_cfg(kid)
            if kid.get("mature"):
                mult += cfg["effort_mature"]
            else:
                mult += cfg["effort_young"]
        return max(0.15, mult)

    def get_idle_rate(self):
        """Dung from the herd when one game-day ends (turn-based)."""
        rate = self.total_camels() * DUNG_PER_CAMEL
        if self.upgrades["mask"] == 1:
            rate = int(rate * 1.25)
        if self.career == "oil":
            rate = int(rate * 0.5)
        if self.coins < 100_000:
            rate = int(rate * 0.88)
        return max(0, int(rate * self.effort_multiplier()))

    def _roll_market_price(self):
        floor = 2
        if self.wife == "title":
            floor = WIVES["title"]["market_floor"]
        choices = [2, 3, 4, 5] if self.coins >= 80_000 else [1, 2, 3, 4, 5]
        self.market_price = random.choice([x for x in choices if x >= floor])

    def _run_one_day_events(self):
        decay_mult, regen_day = self.sanitation_stats()
        if self.wife == "kind":
            decay_mult *= WIVES["kind"]["decay_mult"]
            regen_day += WIVES["kind"]["health_regen_day"]
        regen_day = max(0, int(regen_day * DAWN_REGEN_MULT))

        herd = self.total_camels()
        if herd >= 3:
            decay_mult *= 0.90
        filth = min(48, self.dung / max(40, 30 + herd * 6))
        base_rot = 4.5 + filth * 1.0
        if self.dung > 500:
            base_rot += 3
        if self.security_stock > 0:
            base_rot *= max(0.55, 1 - self.security_stock * 0.035)
        self.health -= base_rot * decay_mult
        self.health += regen_day
        if regen_day > 0:
            self.pending_events.append(
                f"Dawn herbs: +{regen_day} health as the day turns."
            )

        for kid in self._living_kids():
            cfg = self._kid_cfg(kid)
            self.health += cfg["health_day"]
            if random.random() < cfg["death_chance_day"]:
                self._kid_dies(kid, "fever")
                continue
            if kid.get("trait") == "hateful" and random.random() < cfg.get("sabotage_day", 0):
                loss = random.randint(8, 28)
                self.dung = max(0, self.dung - loss)
                self.health -= 5
                self.pending_events.append(
                    f"{kid['name']} despises commerce — spoiled {loss} dung out of spite."
                )

        self.health = max(0, min(100, self.health))

        if self.health <= 0:
            self.days_at_zero_health += 1
        else:
            self.days_at_zero_health = 0

        if self.career == "oil" and self.oil_wells > 0:
            self.coins += self.oil_wells * REAL_CAREERS["oil"]["coin_per_well_day"]
            self.health -= REAL_CAREERS["oil"]["health_fume_day"]
        elif self.career == "tourism":
            cfg = REAL_CAREERS["tourism"]
            self.tour_group_today = random.random() < cfg["tour_chance_day"]
            fame_bonus = 1 + self.tour_fame * 0.04
            self.coins += int(cfg["visitor_coin_day"] * fame_bonus)
            if self.tour_group_today:
                self.tour_fame = min(60, self.tour_fame + 1)
                self.pending_events.append(
                    "Luxury tour bus arrived — today's dung sales sparkle."
                )

        if self.wife == "title":
            cost = WIVES["title"]["daily_dung"]
            if self.dung >= cost:
                self.dung -= cost
                self.pending_events.append(
                    f"Fatima took {cost} dung tribute. Bow, {WIVES['title']['title']}."
                )
            else:
                self.health -= 18
                self.pending_events.append(
                    "Fatima is FURIOUS — no tribute! Health and respect suffer."
                )

        if self.wife == "kids":
            self.days_since_kid += 1
            if self.days_since_kid >= KID_INTERVAL_DAYS and len(self._living_kids()) < MAX_KIDS:
                self._spawn_kid()
                self.days_since_kid = 0

        for kid in self._living_kids():
            if not kid.get("mature") and (self.game_day - kid["born_day"]) >= KID_MATURE_DAYS:
                kid["mature"] = True
                self.pending_events.append(
                    f"{kid['name']} came of age ({KID_TRAITS[kid['trait']]['label']})."
                )

        if random.random() < 0.07:
            if self.security_stock > 0:
                self.security_stock -= 1
                self.pending_events.append(
                    "Sandstorm! Military supplies from a race pot saved the herd."
                )
            else:
                dloss = random.randint(12, 35)
                self.dung = max(0, self.dung - dloss)
                self.health -= random.randint(6, 12)
                self.pending_events.append(
                    f"Sandstorm! No security stock — lost {dloss} dung. Win military pots."
                )

        self.days_since_race += 1
        self._maybe_village_pleasantry()
        self._roll_market_price()

    def advance_day(self, count=1):
        """Turn-based calendar — days pass on sell, rest, race, travel (Silk Road)."""
        if count <= 0 or self.on_silk_road:
            return
        for _ in range(count):
            self.herbs_used_today = False
            self.game_day += 1
            herd = self.get_idle_rate()
            if herd:
                self.dung += herd
            self._run_one_day_events()
        self.capture_home_snapshot()
        self._check_fortune_milestone()

    def click_mult_base(self):
        if self.upgrades["sauce"] == 0:
            return 1
        if self.upgrades["sauce"] == 1:
            return 3
        if self.upgrades["sauce"] == 2:
            return 8
        return 20

    def click(self):
        mult = max(1, int(self.click_mult_base() * self.effort_multiplier()))
        self.dung += mult
        self.total_clicks += 1
        self.health -= 0.28 + (self.dung / 1000)
        self.health = max(0, self.health)
        return mult

    def sanitation_stats(self):
        decay_mult = 1.0
        regen_day = 0
        for lvl in range(1, self.sanitation + 1):
            s = SANITATION[lvl]
            decay_mult *= s["decay_mult"]
            regen_day += s["regen_day"]
        return decay_mult, regen_day

    def _kid_dies(self, kid, cause):
        kid["alive"] = False
        trait = kid.get("trait", "standard")
        name = kid.get("name", "A child")
        if trait == "loving":
            self.health -= 22
            self.pending_events.append(
                f"{name} died ({cause}). Your loving child — the stable feels empty."
            )
        elif trait == "hateful":
            self.health -= 6
            self.pending_events.append(
                f"{name} died ({cause}). Even grief arrives mixed with relief."
            )
        else:
            self.health -= 14
            self.pending_events.append(f"{name} died ({cause}). Desert claims its due.")
        self.kids = [k for k in self.kids if k.get("alive", True)]

    def process_idle(self, in_bed=False):
        if not in_bed:
            self._check_fortune_milestone()
        return self.get_idle_rate(), 0

    def sell_dung(self):
        if self.dung <= 0:
            return 0, "Stable dung is empty! Keep clicking!"
        bonus = 1.15 if self.upgrades["beard"] == 1 else 1.0
        bonus *= self.book_sell_bonus()
        if self.wife == "title":
            bonus *= 1.0 + WIVES["title"]["sell_bonus"]
        if self.career == "tourism" and self.tour_group_today:
            cfg = REAL_CAREERS["tourism"]
            bonus *= 1.0 + cfg["tour_sale_bonus"] + self.tour_fame * 0.008
        if self.career == "oil":
            bonus *= 0.72

        payout = int(self.dung * self.market_price * bonus)
        if self.coins < ESTATE_THRESHOLD and payout > 40_000:
            windfall_tax = int(payout * 0.1)
            payout -= windfall_tax
            self.pending_events.append(
                f"Bazaar windfall tax: ${windfall_tax:,} (fortune not yet secured)."
            )

        if self.health < 12 and random.random() < 0.35:
            self.dung = int(self.dung * 0.85)
            return 0, "Too sick to haggle — buyers walk off with a discount."

        cut = 0
        sabotage = 0
        for kid in self._living_kids():
            cfg = self._kid_cfg(kid)
            if not kid.get("mature"):
                cut_pct = cfg["cut_young"]
                cut += int(payout * cut_pct)
            if kid.get("trait") == "hateful" and random.random() < cfg.get("sabotage_sale", 0):
                sabotage += int(payout * 0.08)
                self.pending_events.append(
                    f"{kid['name']} scares a buyer — merchant life rejected."
                )
        payout -= cut + sabotage
        payout = max(0, payout)
        self.coins += payout
        self.dung = 0
        self.health += 2
        self.advance_day(1)
        msg = f"Sold for ${payout:,}. Dawn — Day {int(self.game_day)}."
        if cut:
            msg += f" (${cut:,} nursery tithe.)"
        if sabotage:
            msg += f" (${sabotage:,} lost to family sabotage.)"
        return payout, msg

    def accept_estate_offer(self, offer_key, decoy_title=None):
        self.estate_resolved = True
        if offer_key == "oil":
            self.career = "oil"
            total = sum(self.camels.values())
            self.oil_wells = max(2, total // 2 + 1)
            for k in self.camels:
                self.camels[k] = max(0, self.camels[k] // 2)
            self.coins = int(self.coins * 0.72)
            return (
                f"YOU ARE NOW: {REAL_CAREERS['oil']['title']}. "
                f"{self.oil_wells} wells pump. Dung fades; fumes hurt. Marriage unlocked."
            )
        if offer_key == "tourism":
            self.career = "tourism"
            self.tour_fame = 8
            self.coins = int(self.coins * 0.65)
            return (
                f"YOU ARE NOW: {REAL_CAREERS['tourism']['title']}. "
                f"Tours & visitors. Marriage unlocked."
            )
        self.career = "merchant"
        self.vanity_title = decoy_title or "Lord of Empty Promises"
        loss_pct = random.randint(22, 45)
        self.coins = int(self.coins * (1 - loss_pct / 100))
        self.health -= 15
        return (
            f"TRAP: '{self.vanity_title}' — no real change. "
            f"Lost {loss_pct}% fortune. Still a dung merchant. Marriage unlocked anyway."
        )

    def divorce(self):
        if not self.wife:
            return "You have no wife to divorce."
        name = WIVES[self.wife]["name"]
        self.coins = int(self.coins / 2)
        self.dung = int(self.dung / 2)
        for k in self.camels:
            self.camels[k] = self.camels[k] // 2
        self.kids = []
        self.days_since_kid = 0
        self.wife = None
        return f"{name} takes half of everything. The bazaar whispers."

    def marry(self, key):
        if self.wife:
            return "Divorce first — desert law allows one wife at a time."
        ok, reason = self.can_marry()
        if not ok:
            return reason
        if key not in WIVES:
            return "No such bride at the oasis."
        self.wife = key
        if key == "kids":
            self.kids = []
            self.days_since_kid = KID_INTERVAL_DAYS - 1
        else:
            self.kids = []
            self.days_since_kid = 0
        return f"Wedded to {WIVES[key]['name']}. May you survive it."

    def wife_status_line(self):
        if not self.wife:
            return "Single (wise?)"
        w = WIVES[self.wife]
        line = w["name"]
        if self.wife == "title":
            line += f" · {w['title']}"
        if self.wife == "kids":
            living = self._living_kids()
            young = sum(1 for k in living if not k.get("mature"))
            line += f" · {len(living)} kids ({young} young)"
        return line

    def status_alerts(self):
        alerts = []
        if self.pending_dead_racer:
            redeem = int(self.last_pot_value * 0.75)
            alerts.append(f"☠ {self.pending_dead_racer['name']} awaits redeem ${redeem:,} (menu 9)")
        if self.total_camels() >= self.camel_capacity():
            alerts.append(f"⚠ Land full ({self.total_camels()}/{self.camel_capacity()}) — grow land")
        if self.book_library:
            alerts.append(f"📖 {len(self.book_library)} unread book(s) — menu B")
        if self.health < 55 and not self.wife:
            alerts.append("❤ Low health / lonely — menu H: wander for holy relics")
        elif self.health < 55:
            alerts.append("❤ Low health — menu H: wander for healing relics")
        if self.holy_relics:
            use = sum(
                1 for r in self.holy_relics if RELIC_DEFS.get(r, {}).get("kind") == "consumable"
            )
            if use:
                alerts.append(f"✝ {use} relic(s) ready to use — menu H")
        if self.artifacts:
            alerts.append(f"🏺 {len(self.artifacts)} oddball artifact(s) — menu 4")
        if self.game_won:
            alerts.append("🏆 Dynasty secured — W to view scroll")
        elif self.coins >= WIN_FORTUNE and self.wife and self.estate_resolved:
            ok, _ = self._legacy_achievement()
            if ok:
                alerts.append("🏆 Dynasty win ready — press W")
            else:
                alerts.append("Legacy needed for dynasty: 5 books / max champ / 10 land / 3 adult kids")
        return alerts


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def health_bar(h):
    filled = int(max(0, min(100, h)) / 10)
    return "[" + "#" * filled + "-" * (10 - filled) + f"] {int(h)}%"


def library_menu(game):
    clear_screen()
    print("=============================================================")
    print(" 📖  DESERT LIBRARY — whole books from race pots")
    print("=============================================================")
    print(f" Studied: {game.books_studied}  |  Unread: {len(game.book_library)}")
    print(f" Sell bonus: +{int((game.book_sell_bonus()-1)*100)}%  |  Race bonus: +{game.book_race_bonus():.0f} spd")
    if game.book_library:
        print("\n Unread shelf:")
        for i, t in enumerate(game.book_library[:6], 1):
            print(f"  {i}. {t}")
        if len(game.book_library) > 6:
            print(f"  ... +{len(game.book_library)-6} more")
    print("\n 1. Study next book (+lore tier, +5 health)")
    print(" Enter. Return")
    sub = input("\n Choice: ").strip()
    if sub == "1":
        return game.study_next_book()
    return ""


def holy_wander_menu(game, from_bed=False):
    while True:
        clear_screen()
        print("=============================================================")
        title = " ✝  SICKBED RELICS" if from_bed else " ✝  HOLY WANDER — relics in the wilderness"
        print(title)
        print("=============================================================")
        print(f" Health: {health_bar(game.health)}  |  Day {int(game.game_day)}")
        marry_need = game.effective_marriage_threshold()
        print(f" Marriage gate: ${marry_need:,}  |  Race luck: +{game.relic_race_bonus()}")
        if game.holy_relics:
            print("\n --- Relics ---")
            for i, rid in enumerate(game.holy_relics, 1):
                d = RELIC_DEFS.get(rid, {"name": rid, "desc": "?"})
                tag = "PASSIVE" if d.get("kind") == "passive" else "use"
                print(f"  {i}. [{tag}] {d['name']}")
                print(f"      {d['desc']}")
        else:
            print("\n No relics yet.")
        if not from_bed:
            print("\n 1. Wander the desert (1 day — tiring; may find relics)")
        print(f" {'2' if not from_bed else '1'}. Brew desert herbs (+health, once per day)")
        print(f" {'3' if not from_bed else '2'}. Use consumable relic (number from list)")
        print(" Enter. Return")
        sub = input("\n Choice: ").strip().lower()
        if sub == "":
            return ""
        if not from_bed and sub == "1":
            return game.wander_desert()
        if sub == ("2" if not from_bed else "1"):
            return game.brew_desert_herbs()
        if sub == ("3" if not from_bed else "2"):
            if not game.holy_relics:
                return "No relics to use."
            num = input("Relic # from list above: ").strip()
            if not num.isdigit():
                return "Invalid."
            return game.use_holy_relic(int(num))
        return "Invalid."


def victory_menu(game):
    clear_screen()
    ok, detail = game.can_claim_victory()
    print("=============================================================")
    print(" 🏆  DYNASTY SCROLL — leave more than dung")
    print("=============================================================")
    print(f" Fortune: ${int(game.coins):,} / ${WIN_FORTUNE:,}")
    print(f" Marriage: {'yes' if game.wife else 'no'}  |  Estate: {'resolved' if game.estate_resolved else 'pending'}")
    leg_ok, leg_detail = game._legacy_achievement()
    print(f" Legacy: {leg_detail if leg_ok else 'incomplete'}")
    print(f" Books studied: {game.books_studied}  |  Land: {game.land_parcels} parcels")
    print(f" Racers: {len(game.race_camels)}  |  Day {int(game.game_day)}")
    print("=============================================================")
    if game.game_won:
        print("\n Your name is already on the scroll. The camels remember.")
        print("\n Enter. Return to stable")
        input()
        return ""
    if ok:
        print("\n Requirements met. Claim your dynasty?")
        print(" 1. Inscribe victory (keep playing)")
        print(" Enter. Not yet")
        sub = input("\n Choice: ").strip()
        if sub == "1":
            return game.claim_victory()
        return "The desert can wait one more day."
    print(f"\n {detail if not ok else 'Almost there.'}")
    print("\n Enter. Return")
    input()
    return detail if not ok else ""


def portrait_menu(game):
    clear_screen()
    print("=============================================================")
    print(" 🖼️  HOME PORTRAIT — memory you carry on the road")
    print("=============================================================")
    snap = game.home_snapshot or game.capture_home_snapshot()
    for line in snap.get("lines", []):
        print(line)
    if game.on_silk_road:
        print("\n (You are away — home waits in this picture.)")
    else:
        print("\n Snapshot refreshes each game-day. Silk Road will freeze this memory.")
    print("\n Enter. Return")
    input()
    return ""


def stable_menu(game):
    while True:
        clear_screen()
        print("=============================================================")
        print(" 🐫  STABLE — 5 slots; pivot your herd")
        print("=============================================================")
        print(f" Capacity: {game.total_camels()}/{game.camel_capacity()}  |  Parcels: {game.land_parcels}")
        print(f" L. Grow land — ${game.land_cost():,} (race pots easier)")
        print("-------------------------------------------------------------")
        for i, (k, label) in enumerate(
            [
                ("std", "Standard 1h"),
                ("bac", "Bactrian 2h"),
                ("rac", "Racer"),
                ("gld", "Golden"),
            ],
            1,
        ):
            sellable = game._sellable_camels(k)
            on_circuit = game._registered_racers(k)
            refund = max(1, int(game.inflation_camels[k] * SELL_CAMEL_REFUND))
            own = game.camels[k]
            print(
                f" {i}. Buy {label} — ${game.inflation_camels[k]:,} "
                f" (own {own}, sellable {sellable}, {DUNG_PER_CAMEL}/day each)"
            )
            if on_circuit:
                print(f"    ({on_circuit} on race circuit — not sellable)")
            print(f" S{i}. Sell one {label} — ${refund:,} refund (90% loss)")
        print("-------------------------------------------------------------")
        print(" Enter. Return to yard")
        sub = input("\n Choice: ").strip().lower()
        if sub == "":
            return ""
        if sub == "l":
            return land_menu(game)
        if sub in ("1", "2", "3", "4"):
            mapping = {"1": "std", "2": "bac", "3": "rac", "4": "gld"}
            ok, msg = game.try_buy_stable_camel(mapping[sub])
            if ok or msg:
                return msg
            continue
        if sub in ("s1", "s2", "s3", "s4"):
            mapping = {"s1": "std", "s2": "bac", "s3": "rac", "s4": "gld"}
            ok, msg = game.sell_stable_camel(mapping[sub])
            return msg
        return "Invalid."


def land_menu(game):
    clear_screen()
    print("=============================================================")
    print(" 🌾  GROW LAND — grazing parcels (5 camels each)")
    print("=============================================================")
    print(f" Camels: {game.total_camels()}/{game.camel_capacity()}  |  Parcels: {game.land_parcels}")
    print(f" Cash price: ${game.land_cost():,}  (race pots = practical land path)")
    print("\n 1. Buy parcel (+5 camel capacity)")
    print(" Enter. Return")
    sub = input("\n Choice: ").strip()
    if sub == "1":
        _, msg = game.grow_land()
        return msg
    return ""


def race_menu(game):
    while True:
        clear_screen()
        print("=============================================================")
        print(" 🏁  AL KHARID CIRCUIT — losers die; pot is life")
        print(f" {GAME_VERSION}  |  Book lore: +{game.book_race_bonus():.0f} race spd")
        print("=============================================================")
        print(f" Coins: ${int(game.coins):,}  |  Unlock: ${RACE_UNLOCK_COINS:,}+")
        print(f" Security stock: {game.security_stock}  |  Desert books: {game.desert_books}")
        print(f" Oddball artifacts: {len(game.artifacts)}  |  Pot: land · loot · coins")
        if game.pending_dead_racer:
            r = game.pending_dead_racer
            redeem = int(game.last_pot_value * 0.75)
            print(f"\n ☠ FALLEN: {r['name']} — redeem ${redeem:,} or abandon forever")
            print(" R. Redeem (3/4 pot)   A. Abandon")
        if not game.race_camels:
            print("\n No race camels. Register Racer/Golden from stable.")
        else:
            print("\n --- Your race camels ---")
            for r in game.race_camels:
                ch = " ★" if r == game.best_racer() else ""
                print(
                    f" {r['id']}. {r['name']} ({r['ctype']}) spd {r['speed']} "
                    f"upg {r['upgrades']}{ch}"
                )
        print("\n 1. Register Racer (rac) from stable — ${:,} fee".format(RACE_REGISTER_FEE))
        print(" 2. Register Golden (gld) from stable — ${:,} fee".format(RACE_REGISTER_FEE))
        print(" 3. RUN RACE (pick id — entry fee, death risk)")
        print(" 4. Upgrade champion (big money)")
        print(" Enter. Return")
        sub = input("\n Choice: ").strip().lower()
        if sub == "":
            return ""
        if sub == "r" and game.pending_dead_racer:
            return game.redeem_fallen_racer()
        if sub == "a" and game.pending_dead_racer:
            return game.abandon_fallen_racer()
        if sub == "1":
            return game.register_racer_from_stable("rac")
        if sub == "2":
            return game.register_racer_from_stable("gld")
        if sub == "3":
            if not game.race_camels:
                return "Register a racer first."
            rid = input("Race camel id: ").strip()
            if not rid.isdigit():
                return "Invalid id."
            return game.run_race(int(rid))
        if sub == "4":
            return game.upgrade_champion()
        return "Invalid."


def bed_menu(game):
    msg = ""
    while game.is_bedridden():
        clear_screen()
        game.process_idle(in_bed=True)
        print("=============================================================")
        print(" 🛏️  TOO ILL — STAY IN BED (stable locked)")
        print("=============================================================")
        print(f" ❤️  {health_bar(game.health)}  — need >{BED_LOCK_THRESHOLD}% to work")
        if game.health <= 0:
            left = FAILURE_DAYS_AT_ZERO - game.days_at_zero_health
            print(f" ⚠  At death's door ({max(0, left)} day(s) before total failure)")
        print(f" 💍  {game.wife_status_line()}")
        if game.wife == "kind":
            print(" Layla tends you (+bonus rest).")
        print("=============================================================")
        while game.pending_events:
            print(f" 📜 {game.pending_events.pop(0)}")
        if msg:
            print(f" 💬 {msg}")
            print("-------------------------------------------------------------")
            msg = ""
        print(" [Enter] Rest (ends day, +25% herb recovery)")
        print(" H. Herbs & holy relics (brew / use — no need to wait blind)")
        print(" 6. Sanitation upgrades (if you can afford)")
        print(" Q. Save & quit")
        print("=============================================================")
        choice = input(" Bed action: ").strip().lower()
        if choice in ("", "r", "rest"):
            msg = game.rest_in_bed()
            game.save()
        elif choice == "6":
            msg = sanitation_menu(game)
            game.save()
        elif choice == "h":
            msg = holy_wander_menu(game, from_bed=True)
            game.save()
        elif choice == "q":
            game.save()
            print("\nSaved from sickbed. Get well.\n")
            raise SystemExit(0)
        else:
            msg = "Rest, menu H (herbs/relics), or buy sanitation (6)."
    return msg


def estate_broker_menu(game):
    clear_screen()
    print("=============================================================")
    print(" 🏜️  ESTATE BROKERS — sell the stable, become something else")
    print("=============================================================")
    print(f" Fortune: ${int(game.coins):,}  |  Career: {game.career_label()}")
    if game.estate_resolved:
        print("\n Brokers have already taken their cut. You chose your path.")
        input("\nEnter...")
        return ""
    if game.coins < ESTATE_THRESHOLD:
        print(f"\n They ignore you until ${ESTATE_THRESHOLD:,}.")
        input("\nEnter...")
        return f"Brokers sniff: 'Come back at ${ESTATE_THRESHOLD:,}, merchant.'"

    real_key = random.choice(["oil", "tourism"])
    decoys = random.sample(DECOY_PITCHES, 4)
    offers = [(real_key, REAL_CAREERS[real_key]["pitch"], None)]
    for pitch, title in decoys:
        offers.append(("decoy", pitch, title))
    random.shuffle(offers)

    print("\n Five offers. FIFTY exist in the desert — ONE changes your life.\n")
    for i, (key, pitch, title) in enumerate(offers, 1):
        print(f" {i}. {pitch}")
    print("\n Enter. Flee (brokers return tomorrow)")
    sub = input("\n Sign which deal (1-5): ").strip()
    if sub == "":
        return "You sleep on it. Brokers will return."
    if sub not in ("1", "2", "3", "4", "5"):
        return "Invalid."
    key, pitch, title = offers[int(sub) - 1]
    return game.accept_estate_offer(key, title)


def marriage_menu(game):
    while True:
        clear_screen()
        print("=============================================================")
        print(" 💍  MARRIAGE HALL — one wife, desert law")
        print("=============================================================")
        ok, reason = game.can_marry()
        if not ok:
            print(f"\n 🔒 {reason}")
        else:
            print(f"\n ✓ Fortune meets marriage gate (${game.effective_marriage_threshold():,})")
        print(f" Status: {game.wife_status_line()}")
        print(f" Health: {health_bar(game.health)}")
        if game.wife:
            print(f"\n Divorce = she takes HALF (coins, dung, camels). Kids reset.")
        print("\n --- Choose ONE bride (requires single status) ---")
        print(" 1. Fatima the Fierce — daily dung tribute, royal title, +sell bonus")
        print(" 2. Layla the Gentle — health regen, fights filth sickness")
        print(" 3. Zahra the Fruitful — random kids: loving / standard / hateful; some die")
        print(" 4. 💔 Divorce current wife (half your stuff)")
        print(" Enter. Return to stable")
        sub = input("\n Choice: ").strip().lower()
        if sub == "":
            return ""
        if sub == "4":
            return game.divorce()
        mapping = {"1": "title", "2": "kind", "3": "kids"}
        if sub in mapping:
            ok, reason = game.can_marry()
            if not ok and not game.wife:
                return reason
            return game.marry(mapping[sub])
        return "Invalid choice."


def sanitation_menu(game):
    while True:
        clear_screen()
        print("=============================================================")
        print(" 🧼  DUNG SANITATION — stay healthy around the stable")
        print("=============================================================")
        print(f" Health: {health_bar(game.health)}")
        print(f" Level: {game.sanitation}/3")
        print(" (Low health cripples click + idle output. Piled dung breeds sickness.)")
        for lvl, s in SANITATION.items():
            owned = "OWNED" if game.sanitation >= lvl else f"${s['cost']} Coins"
            print(f" {lvl}. {s['name']} — less decay, +{s['regen_day']}/day regen [{owned}]")
        print("\n Enter. Return")
        sub = input("\n Upgrade (1-3): ").strip()
        if sub == "":
            return ""
        if sub not in ("1", "2", "3"):
            return "Invalid."
        target = int(sub)
        if game.sanitation >= target:
            return "Already at or above that level."
        if target != game.sanitation + 1:
            return "Buy sanitation upgrades in order."
        cost = SANITATION[target]["cost"]
        if game.coins < cost:
            return f"Need ${cost} for {SANITATION[target]['name']}."
        game.coins -= cost
        game.sanitation = target
        game.health = min(100, game.health + 8)
        return f"{SANITATION[target]['name']} installed. Slightly less doomed."


def main():
    had_save = os.path.exists(SAVE_FILE)
    game = CamelClicker()
    game.load()
    if not had_save:
        show_intro(failure=False)
    msg = "Five acres. One stable. The wilderness waits."

    while True:
        if game.is_total_failure():
            show_intro(failure=True)
            game.full_reset()
            game.save()
            msg = "Five acres. One stable. The wilderness waits."
            continue

        if game.is_bedridden():
            msg = bed_menu(game)
            continue

        clear_screen()
        rate, _ = game.process_idle()

        print("=============================================================")
        print(ASCII_CAMEL)
        print("=============================================================")
        print(f" 🪙  Coins: ${int(game.coins):,}  |  💩  Dung: {int(game.dung):,}")
        print(
            f" 🐫  {game.total_camels()}/{game.camel_capacity()} camels "
            f"({game.land_parcels} land)  |  🏁  {len(game.race_camels)} racers"
        )
        print(f" ⚙️  Herd: {rate} dung/day  |  📈  Market: {game.market_price}/dung  |  📅 Day {int(game.game_day)}")
        print(f" ❤️  {health_bar(game.health)}  |  🎖  {game.career_label()}")
        print(f" 💍  {game.wife_status_line()}")
        print(f" {GAME_VERSION}  |  Marry: ${game.effective_marriage_threshold():,}  |  Estate: ${ESTATE_THRESHOLD:,}")
        for alert in game.status_alerts():
            print(f" ⚠  {alert}")
        print("=============================================================")
        while game.pending_events:
            print(f" 📜 {game.pending_events.pop(0)}")
        if msg:
            print(f" 💬 {msg}")
            print("-------------------------------------------------------------")
            msg = ""

        print(" [Enter] Click camel")
        print(" 1. Sell all dung (ends day — herd poops at dawn)")
        print(" 2. Buy / sell camels (S1–S4 sell @ 10% refund)")
        print(" 3. Merchant upgrades")
        print(" 4. Stable status")
        print(" P. 🖼️ Home portrait (herd + kids snapshot)")
        if game.book_library or game.books_studied:
            print(" B. 📖 Desert library (study race-pot books)")
        if game.coins >= RACE_UNLOCK_COINS or game.race_camels or game.pending_dead_racer:
            print(" 9. 🏁 Camel races (losers die — redeem 3/4 pot)")
        print(" 5. 💍 Marriage hall")
        print(" 6. 🧼 Sanitation (health)")
        print(" H. ✝ Holy wander (desert relics — health / race / marriage)")
        if game.coins >= int(ESTATE_THRESHOLD * 0.85) or not game.estate_resolved:
            print(" 8. 🏜️ Estate brokers (500k fork — optional career)")
        if game.coins >= int(WIN_FORTUNE * 0.65) or game.game_won:
            print(" W. 🏆 Dynasty scroll (1M + legacy)")
        print(" 7. Reset")
        print(" Q. Save & quit")
        print("=============================================================")

        choice = input(" Action: ").strip().lower()

        if choice == "":
            mult = game.click()
            msg = f"Splop! (+{mult} dung) — sell to end the day"
            game.save()
        elif choice == "1":
            _, msg = game.sell_dung()
            game.save()
        elif choice == "2":
            msg = stable_menu(game)
            game.save()
        elif choice == "3":
            sauce_level = game.upgrades["sauce"]
            print("\n--- Merchant Upgrades ---")
            if sauce_level < 3:
                costs = [30, 120, 500]
                print(f"1. Kebab sauce tier {sauce_level + 1} — ${costs[sauce_level]}")
            else:
                print("1. Kebab sauce [MAX]")
            print(f"2. Fake beard (+15% sell) — ${UPGRADE_PRICES['beard']} [{'done' if game.upgrades['beard'] else 'buy'}]")
            print(f"3. Camel mask (+25% idle) — ${UPGRADE_PRICES['mask']} [{'done' if game.upgrades['mask'] else 'buy'}]")
            sub = input("Buy (1-3): ").strip()
            if sub == "1" and sauce_level < 3:
                cost = [30, 120, 500][sauce_level]
                if game.coins >= cost:
                    game.coins -= cost
                    game.upgrades["sauce"] += 1
                    msg = "Sauce upgraded!"
                    game.save()
                else:
                    msg = "Insufficient Dinars!"
            elif sub == "2" and game.upgrades["beard"] == 0 and game.coins >= UPGRADE_PRICES["beard"]:
                game.coins -= UPGRADE_PRICES["beard"]
                game.upgrades["beard"] = 1
                msg = "Gorgeous Ali disguise active!"
                game.save()
            elif sub == "3" and game.upgrades["mask"] == 0 and game.coins >= UPGRADE_PRICES["mask"]:
                game.coins -= UPGRADE_PRICES["mask"]
                game.upgrades["mask"] = 1
                msg = "Camel mask equipped!"
                game.save()
        elif choice == "4":
            print("\n--- Stable ---")
            for k in game.camels:
                on_circuit = game._registered_racers(k)
                extra = f" ({on_circuit} on circuit)" if on_circuit else ""
                print(f" {k}: {game.camels[k]}{extra}  [{DUNG_PER_CAMEL}/day each]")
            print(f" Effort mult: x{game.effort_multiplier():.2f}")
            print(f" Career: {game.career_label()}")
            if game.career == "oil":
                print(f" Oil wells: {game.oil_wells} (${REAL_CAREERS['oil']['coin_per_well_day']}/well/day)")
            if game.career == "tourism":
                print(f" Tour fame: {game.tour_fame} | Tour bus today: {game.tour_group_today}")
            print(f" Land: {game.land_parcels} parcels · {game.total_camels()}/{game.camel_capacity()} camels")
            if game.holy_relics:
                print(f" Holy relics ({len(game.holy_relics)}):")
                for rid in game.holy_relics:
                    d = RELIC_DEFS.get(rid, {"name": rid})
                    print(f"  · {d['name']}")
            print(f" Security: {game.security_stock}  |  Books: {game.desert_books}")
            if game.artifacts:
                print(f" Artifacts ({len(game.artifacts)}):")
                for art in game.artifacts[-8:]:
                    print(f"  · {art}")
                if len(game.artifacts) > 8:
                    print(f"  ... +{len(game.artifacts)-8} more")
            if game.race_camels:
                print(" (Racers stay on your land and poop with the herd.)")
                for r in game.race_camels:
                    print(f" Racer {r['name']}: spd {r['speed']} tier {r['upgrades']}")
            print(f" Sanitation: {game.sanitation}/3")
            if game._living_kids():
                for kid in game._living_kids():
                    age = int(game.game_day - kid["born_day"])
                    st = "adult" if kid.get("mature") else f"young {age}/{KID_MATURE_DAYS}d"
                    print(
                        f" {kid['name']}: {st} · {KID_TRAITS[kid['trait']]['label']}"
                    )
            input("\nEnter...")
        elif choice == "5":
            msg = marriage_menu(game)
            game.save()
        elif choice == "6":
            msg = sanitation_menu(game)
            game.save()
        elif choice == "h":
            msg = holy_wander_menu(game)
            game.save()
        elif choice == "b":
            msg = library_menu(game)
            game.save()
        elif choice == "p":
            msg = portrait_menu(game)
            game.save()
        elif choice == "8":
            msg = estate_broker_menu(game)
            game.save()
        elif choice == "9":
            msg = race_menu(game)
            game.save()
        elif choice == "w":
            msg = victory_menu(game)
            game.save()
        elif choice == "7":
            if input("Reset? (y/n): ").strip().lower() == "y":
                game.full_reset()
                game.save()
                show_intro(failure=False)
                msg = "Five acres. One stable. The wilderness waits."
        elif choice == "q":
            game.save()
            print("\nSaved. The camels remember.\n")
            break


if __name__ == "__main__":
    main()
