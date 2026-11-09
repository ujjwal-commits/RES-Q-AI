"""Priority engine.

The machine-learning model decides WHAT kind of emergency a report describes.
This engine decides HOW URGENT it is, and every point of the score is traceable
to a phrase in the report. That is what powers the "Why?" panel.

    priority score = base risk of the incident type
                     + points for each danger signal found in the text
                     - points for reassuring signals (minor, under control, drill ...)

Signals understand English and Hinglish (Hindi written in English letters).
"""
from __future__ import annotations

import re

from .locations import LOCATIONS


def _rx(*parts):
    return re.compile("|".join("(?:%s)" % p for p in parts), re.I)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TYPES = ["Accident", "Fire", "Medical", "Traffic", "Infrastructure", "Other"]
TIERS = ["Critical", "High", "Medium", "Low"]

# Starting risk of each incident type (0-100 scale)
BASE_RISK = {
    "Fire": 68, "Accident": 32, "Medical": 32,
    "Traffic": 12, "Infrastructure": 10, "Other": 5,
}
BASE_LABEL = {
    "Fire": "Fire or smoke reported",
    "Accident": "Accident reported",
    "Medical": "Medical emergency reported",
    "Traffic": "Road or traffic problem",
    "Infrastructure": "Infrastructure problem",
    "Other": "General report",
}

TIER_CUTOFFS = [(70, "Critical"), (40, "High"), (20, "Medium"), (0, "Low")]
SENSITIVE_LOCATION_POINTS = 5
# V1.2: fewer staff are on duty late at night, so a report gets a small urgency
# boost in that window. This only applies when the caller explicitly says the
# report is happening at night (see score_report's `night` argument) - it never
# fires on its own, so it can never make the automated tests flaky.
NIGHT_START_HOUR, NIGHT_END_HOUR = 22, 6
NIGHT_POINTS = 8
NIGHT_LABEL = "Night hours: fewer staff on duty, response may be slower"


def is_night_hour(hour: int) -> bool:
    return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR

RESOURCE_ICONS = {
    "Ambulance": "🚑", "Medical Team": "👨‍⚕️", "Fire Response": "🚒",
    "Rescue Team": "⛑️", "Maintenance": "🚧", "Traffic/Security": "🚔",
    "Security": "🛡️", "Electrician": "⚡", "Plumber": "🚰",
}


# Specific infrastructure alert, shown instead of the generic "Infrastructure" label.
# Order matters: checked top to bottom, first match wins.
INFRA_SUBTYPES = [
    ({"major_hazard"}, "Structural collapse / explosion risk"),
    ({"trapped"}, "Lift or people trapped"),
    ({"hazard"}, "Electrical hazard"),
    ({"outage"}, "Power outage"),
    ({"water"}, "Water leakage or flooding"),
]


def infra_subtype(keys: set):
    for need, label in INFRA_SUBTYPES:
        if keys & need:
            return label
    return "General maintenance issue"


def tier_for(score: float) -> str:
    for cutoff, name in TIER_CUTOFFS:
        if score >= cutoff:
            return name
    return "Low"


# ---------------------------------------------------------------------------
# Text clean-up
# ---------------------------------------------------------------------------
# "no one is injured" contains the word "injured" - remove such phrases first,
# otherwise the system would treat a reassurance as a danger signal.
NEGATED_INJURY = _rx(
    r"\b(?:no|nobody|no one|none|not any|without any|without)\b[^.,;!?]{0,20}?\b(?:injur\w*|hurt|wounded|casualt\w*|harm\w*)",
    r"\bnot\s+(?:injured|hurt|wounded)\b",
    r"\bkoi\s+(?:bhi\s+)?(?:ghayal|chot|zakhmi)\s+nahi(?:n)?\b",
    r"\bkisi\s+ko\s+(?:bhi\s+)?(?:chot|ghayal)\s+nahi\w*",
    r"\b(?:ghayal|chot)\s+nahi(?:n)?\b",
)


def normalise(text: str):
    """Lower-case, tidy spaces, strip negated-injury phrases. Returns (text, had_negated_injury)."""
    t = text.lower().replace("\u2019", "'")
    t = re.sub(r"\s+", " ", t).strip()
    had_negation = bool(NEGATED_INJURY.search(t))
    t = NEGATED_INJURY.sub(" ", t)
    return t, had_negation


# ---------------------------------------------------------------------------
# Signals (each one becomes a line in the "Why?" explanation)
# ---------------------------------------------------------------------------
FACTORS = [
    dict(key="injury", label="Injuries mentioned, medical help needed", points=28, rx=_rx(
        r"\binjur\w*", r"\bhurt\b", r"\bwound\w*", r"\bbleed\w*", r"\bblood\b", r"\bburns?\b",
        r"\bghayal\b", r"\bzakhmi\b", r"\bchot\b", r"\bkhoon\b", r"\bfractur\w*",
        r"\bbroken\s+(?:leg|arm|bone|hand|rib)", r"\bdeep\s+cut\b", r"\bhead\s+wound\b",
        r"\bswollen\b", r"\bunable\s+to\s+get\s+up\b",
        r"\b(?:riders?|persons?|people|students?|man|woman|boy|girl)\b[^.,;]{0,25}\b(?:on|lying\s+on)\s+the\s+(?:ground|road|floor)\b", r"\b(?:cannot|can't|unable\s+to)\s+(?:stand|walk)\b", r"\bpair\s+toot\b", r"\btoot\s+gaya\b",
    )),
    dict(key="serious", label="Life-threatening condition described", points=40, rx=_rx(
        r"\bunconscious\b", r"\bunresponsive\b", r"\bnot\s+(?:breathing|responding)\b",
        r"\b(?:he|she|him|her|student|person|man|woman|girl|boy|someone|rider|driver)\s+(?:is\s+|was\s+)?not\s+moving\b",
        r"\bno\s+(?:pulse|heartbeat)\b", r"\bheart\s+attack\b", r"\bcardiac\b",
        r"\b(?:student|person|man|woman|girl|boy|someone|he|she|guy|staff|professor|teacher)\s+(?:has\s+|just\s+)?collapsed\b",
        r"\bseizure\b", r"\bbehosh\b", r"\bsaans?\s+(?:nahi|nahin|band)\b",
        r"\banaphyla\w*", r"\bsevere\s+allergic\b", r"\ballergic\s+reaction\b", r"\basthma\s+attack\b",
        r"\b(?:difficulty|trouble|problem)\s+(?:in\s+)?breath\w*",
        r"\bbleeding\s+(?:heavily|profusely|badly)\b", r"\bbleeding\s+badly\b", r"\bsevere\s+bleeding\b",
        r"\bkhoon\s+beh\w*", r"\bdrown\w*", r"\bchoking\b", r"\bdora\s+pad\w*",
        r"\bstopped\s+breathing\b", r"\b(?:cannot|can't|not\s+able\s+to)\s+breathe\b", r"\bgasping\b",
    )),
    dict(key="concerning", label="Concerning symptoms reported", points=15, rx=_rx(
        r"\bchest\s+pain\b", r"\bpain\s+in\s+(?:the\s+)?chest\b", r"\bdizz\w*", r"\bfaint\w*", r"\bvomit\w*", r"\bulti\b", r"\bchakkar\b",
        r"\bsaans\s+lene\b", r"\bfood\s+poisoning\b",
    )),
    dict(key="trapped", label="People trapped", points=35, rx=_rx(
        r"\btrapped\b",
        r"\bstuck\s+(?:inside|in(?:side)?\s+(?:the\s+)?(?:lift|elevator|room|building|vehicle|car|bus|cabin))",
        r"\b(?:people|persons|students|log|kids|children|girls|boys|driver)\b[^.,;]{0,20}\bstuck\b",
        r"\b(?:phase|fase|phans\w*|phas)\s+(?:hue|hui|hai|hain|gaye|gaya|gayi|rahe|gae)\b",
        r"\bandar\s+(?:log\s+)?(?:phase|fase|phans\w*)\b",
        r"\bunder\s+(?:the\s+)?(?:debris|rubble)\b",
        r"\b(?:cannot|can't|can not)\s+(?:get|come)\s+out\b",
        r"\b(?:lift|elevator)\s+(?:is\s+)?(?:stuck|jammed)\b", r"\b(?:stuck|jammed)\b[^.,;]{0,20}\b(?:lift|elevator)\b",
        r"\b(?:lift|elevator)\b[^.]{0,40}\b(?:stopped|halted|between\s+floors)\b",
        r"\blift\s+mein\b[^.]{0,20}\b(?:fase|phase|phans\w*)\b",
    )),
    dict(key="major_hazard", label="Major hazard (collapse, explosion or gas leak)", points=45, rx=_rx(
        r"\b(?:wall|building|roof|ceiling|structure|bridge|slab|balcony|floor|tower|pillar|canopy|shed)\b[^.,;]{0,30}\bcollaps\w*",
        r"\bcollaps\w*\b[^.,;]{0,12}\b(?:wall|building|roof|ceiling|structure|slab|balcony|floor)\b",
        r"\b(?:gas|cylinder|lpg)\s+leak\w*", r"\bleak\w*\s+(?:of\s+)?gas\b", r"\bgas\s+smell\b", r"\bsmell\s+of\s+gas\b",
        r"\bexplo\w+", r"\bblast\b", r"\b(?:might|about\s+to|may)\s+(?:collapse|fall)\b",
        r"\bbuilding\s+(?:is\s+)?falling\b", r"\bcaved?\s+in\b", r"\bcave-in\b",
    )),
    dict(key="hazard", label="Electrical or structural hazard", points=35, skip_types={"Fire"}, rx=_rx(
        r"\blive\s+(?:electric\w*\s+)?(?:wire|cable)\w*",
        r"\b(?:exposed|hanging|fallen|broken|open|loose)\s+(?:electric\w*\s+)?(?:wire|cable)\w*",
        r"\b(?:electric\w*\s+)?(?:wire|cable)s?\s+(?:is\s+|are\s+)?(?:hanging|fallen|exposed|loose|broken|sparking)\b",
        r"\belectric\s+shock\b", r"\bshock\b", r"\bshort\s*circuit\b", r"\bspark\w*",
        r"\bcrack\w*", r"\bnangi\s+taar\b", r"\btaar\s+(?:gir|latak)\w*",
    )),
    dict(key="weapon", label="Weapon mentioned", points=35, rx=_rx(
        r"\bweapons?\b", r"\bknife\b", r"\bknives\b", r"\bgun\b", r"\bpistol\b", r"\bblade\b",
    )),
    dict(key="threat", label="Threat to personal safety", points=30, rx=_rx(
        r"\bfight\w*", r"\bassault\w*", r"(?<!heart )(?<!panic )(?<!asthma )\battack\w*", r"\bharass\w*",
        r"\bthreat\w*", r"\bbeat(?:ing)?\s+up\b", r"\bbeating\b", r"\bragging\b", r"\bladai\b", r"\bjhagda\b", r"\bmaar\s*pit\b", r"\bstalk\w*", r"\briot\b",
    )),
    dict(key="suspicious", label="Suspicious activity or theft", points=20, rx=_rx(
        r"\bsuspicious\b", r"\btheft\b", r"\bstolen\b", r"\bstole\b", r"\bsteal\w*", r"\bthie(?:f|ves)\b",
        r"\bchori\b", r"\bintruder\b", r"\bunknown\s+(?:person|man|people)\b",
    )),
    dict(key="wildlife", label="Wild animal on campus", points=20, rx=_rx(
        r"\bsnake\w*", r"\bscorpion\b", r"\bbee\s*hive\b", r"\bbees\b", r"\bmonkeys?\b", r"\bsaanp\b", r"\bbichhu\b",
    )),
    dict(key="worsening", label="Situation getting worse", points=15, rx=_rx(
        r"\bspread\w*", r"\bgetting\s+worse\b", r"\bworsen\w*", r"\bincreasing\b", r"\bgrowing\b",
        r"\bout\s+of\s+control\b", r"\bphail\w*", r"\bbadh\s+(?:raha|rahi|rahe)\b", r"\bbadhti\b",
        r"\brapidly\b", r"\bescalat\w*",
    )),
    dict(key="access", label="Emergency vehicle access affected", points=20, only_types={"Traffic", "Accident"}, rx=_rx(
        r"\bambulance\b[^.,;]{0,30}\b(?:stuck|cannot|can't|can not|unable|not able|delayed|waiting|blocked)\b",
        r"\bfire\s*(?:brigade|truck)\b[^.,;]{0,30}\b(?:stuck|cannot|can't|unable|delayed|waiting|blocked)\b",
        r"\bambulance\b[^.,;]{0,20}\bpass\b",
    )),
    dict(key="blocked", label="Road or path blocked", points=28, only_types={"Traffic"}, rx=_rx(
        r"\bblocked\b", r"\bblocking\b", r"\bblockage\b", r"\broad\s*block\b", r"\bband\s+hai\b", r"\bnot\s+passable\b",
        r"\b(?:road|lane|lanes|gate)\s+(?:is\s+|are\s+)?closed\b",
    )),
    dict(key="jam", label="Traffic congestion", points=10, only_types={"Traffic"}, rx=_rx(
        r"\bjam(?:med)?\b", r"\bcongestion\b", r"\bgridlock\b", r"\bline\s+lagi\b",
        r"\b(?:vehicles?|cars?|traffic|gaadiyan)\b[^.,;]{0,15}\bnot\s+moving\b",
    )),
    dict(key="outage", label="Power outage", points=15, only_types={"Infrastructure"}, rx=_rx(
        r"\bpower\s*(?:cut|outage|failure|down)\b", r"\bno\s+(?:electricity|power|current)\b", r"\bblackout\b",
        r"\bbijli\s+(?:nahi|nahin|chali|gul|cut|gayi)\b",
    )),
    dict(key="water", label="Water damage or flooding", points=15, only_types={"Infrastructure"}, rx=_rx(
        r"\bflood\w*", r"\bburst\b", r"\boverflow\w*", r"\bleakage\b", r"\b(?:pani|paani)\s+bhar\w*", r"\bwaterlog\w*",
    )),
    dict(key="severe_crash", label="Severe crash described", points=20, only_types={"Accident"}, rx=_rx(
        r"\boverturn\w*", r"\brolled\s+over\b", r"\brammed\b", r"\bspeeding\b", r"\bhigh\s+speed\b",
        r"\brun\s+over\b", r"\bpile-?up\b", r"\bwrecked\b",
    )),
    dict(key="severe", label="Described as serious or large-scale", points=15,
         only_types={"Fire", "Accident", "Medical", "Infrastructure"}, rx=_rx(
        r"\bhuge\b", r"\bmassive\b", r"\bmajor\b", r"\bserious\w*", r"\bsevere\w*", r"\bthick\b",
        r"\bbahut\s+(?:bada|badi|zyada)\b", r"\bvery\s+heavy\b",
    )),
    dict(key="urgent", label="Reporter asks for immediate help", points=8, rx=_rx(
        r"\burgent\w*", r"\bemergency\b", r"\bimmediate\w*", r"\basap\b", r"\bhurry\b", r"\bjaldi\b",
        r"\bturant\b", r"\bbachao\b", r"\bsend\s+help\b", r"\bneed\s+help\b",
    )),
    dict(key="vulnerable", label="Vulnerable people involved", points=5, rx=_rx(
        r"\bgirls?\b", r"\bchild\b", r"\bchildren\b", r"\bkids?\b", r"\belderly\b", r"\bpregnant\b",
        r"\bdisabled\b", r"\bbacch\w*", r"\bladki\w*", r"\bmahila\w*",
    )),
    # --- reassuring signals (negative points) ---
    dict(key="minor", label="Described as minor", points=-35, rx=_rx(
        r"\bminor\b", r"\bsmall\b(?!\s+(?:child|kid|girl|boy))", r"\bslight\w*", r"\bmild\b", r"\bhalk[ia]\b",
        r"\bchhot[aei]\b", r"\bnegligible\b", r"\bscratch\w*", r"\blittle\b", r"\bpaper\s+cut\b", r"\bdent\w*",
    )),
    dict(key="controlled", label="Reported as under control", points=-35, rx=_rx(
        r"\bunder\s+control\b", r"\bcontrol\s+mein\b", r"\bcontrolled\b", r"\bextinguished\b",
        r"\bput\s+out\b", r"\bnow\s+(?:safe|fine|ok|okay)\b", r"\bresolved\b", r"\bbujh\s+(?:gayi|gaya|chuki)\b",
    )),
    dict(key="partial", label="Only partly blocked", points=-10, only_types={"Traffic"}, rx=_rx(
        r"\b(?:one|single|1)\s+lane\b", r"\bpartial\w*", r"\bpartly\b", r"\bhalf\b",
    )),
    dict(key="conscious", label="Person reported conscious or stable", points=-5, rx=_rx(
        r"\bconscious\b", r"\bstable\b", r"\bawake\b", r"\bbreathing\s+normally\b", r"\bout\s+of\s+danger\b",
    )),
    dict(key="drill", label="Looks like a drill or test", points=-60, rx=_rx(
        r"\b(?:fire|mock|evacuation|safety)\s+drill\b", r"\bmock\b", r"\btest\s+alarm\b", r"\brehearsal\b",
    )),
]
NO_INJURY_LABEL = "No injuries reported"
NO_INJURY_POINTS = -5

# ---------------------------------------------------------------------------
# Extra text checks
# ---------------------------------------------------------------------------
_PEOPLE = (r"(?:people|persons?|students?|victims?|injured|log|logon|kids|children|labou?rers|workers|"
           r"staff|members|passengers|boys|girls|individuals|bacche|vyakti|ladke|ladkiyan|riders?)")
_NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5, "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
}
_COUNT_DIGIT = re.compile(r"\b(\d{1,3})\s*\+?\s*" + _PEOPLE + r"\b", re.I)
_COUNT_WORD = re.compile(r"\b(" + "|".join(_NUM_WORDS) + r")\s+" + _PEOPLE + r"\b", re.I)
_MANY = _rx(
    r"\b(?:several|many|multiple|numerous)\s+(?:\w+\s+)?(?:people|persons|students|injured|victims|kids|children|workers|staff|boys|girls|passengers|riders)\b",
    r"\bcrowd\b", r"\bgroup\s+of\b", r"\bcouple\s+of\b", r"\bkai\s+(?:log|students?)\b",
    r"\bkaafi\s+(?:log|students?|logon)\b", r"\bbahut\s+(?:se|saare|sare)\s+(?:log|students?)\b",
    r"\b(?:several|many)\s+(?:are\s+)?(?:hurt|injured)\b", r"\bkai\s+log\b",
    r"\b(?:students|people|persons|victims|workers)\s+(?:are\s+|were\s+)?(?:trapped|injured|hurt)\b",
)

_FIRE_WORDS = _rx(r"\bfire\b", r"\bsmok\w*", r"\bflames?\b", r"\bburning\b", r"\baag\b", r"\bdhuan\w*", r"\bblaze\b")
_ELECTRIC = _rx(r"\bwire\w*", r"\belectric\w*", r"\bspark\w*", r"\bshort\s*circuit\b", r"\btransformer\b", r"\bbijli\b",
                r"\bpower\b", r"\bcurrent\b")

# Rough keyword hints per type. Only used as a safety net when the ML model is unsure.
TYPE_HINTS = {
    "Fire": _rx(r"\bfire\b", r"\bsmok\w*", r"\bflames?\b", r"\bburn\w*", r"\baag\b", r"\bdhuan\w*", r"\bblaze\b"),
    "Accident": _rx(r"\baccident\w*", r"\bcollision\b", r"\bcollid\w*", r"\bcrash\w*", r"\brun\s+over\b",
                    r"\bhit\s+by\b", r"\btakkar\b", r"\btakra\w*", r"\boverturn\w*"),
    "Medical": _rx(r"\bfaint\w*", r"\bunconscious\b", r"\bheart\s+attack\b", r"\bchest\s+pain\b", r"\bfever\b",
                   r"\bbukhar\b", r"\bvomit\w*", r"\bseizure\b", r"\bbehosh\b", r"\bmedical\b", r"\bdoctor\b",
                   r"\bfirst\s+aid\b", r"\bbreath\w*", r"\bsick\b", r"\bbimar\b", r"\bulti\b", r"\basthma\b",
                   r"\bfell\b", r"\bslipped\b", r"\bpain\b", r"\bunwell\b", r"\bnot\s+feeling\s+well\b", r"\bheadache\b"),
    "Traffic": _rx(r"\btraffic\b", r"\bjam\b", r"\broad\s*block\w*", r"\bdiversion\b", r"\bwrongly\s+parked\b",
                   r"\bgalat\s+parking\b", r"\bvehicles?\b", r"\bcow\b", r"\bcattle\b", r"\bstray\s+animals?\b",
                   r"\bmiddle\s+of\s+the\s+road\b"),
    "Infrastructure": _rx(r"\blights?\b", r"\bleak\w*", r"\bpipe\b", r"\bwater\b", r"\bpower\b", r"\belectric\w*",
                          r"\bbijli\b", r"\bpaani\b", r"\blift\b", r"\bwall\b", r"\bceiling\b", r"\bcrack\w*",
                          r"\bwifi\b", r"\bbench\b", r"\bprojector\b", r"\btap\b", r"\bgas\b", r"\bwire\b"),
    "Other": _rx(r"\blost\b", r"\bfound\b", r"\bsuspicious\b", r"\bfight\w*", r"\btheft\b", r"\bstolen\b",
                 r"\bnoise\b", r"\bmusic\b", r"\bdogs?\b", r"\bharass\w*", r"\bkho\b", r"\bsnake\w*",
                 r"\bdrunk\b", r"\bshout\w*", r"\bargu\w*", r"\bquarrel\w*"),
}


def keyword_type_prior(text: str):
    """Share of keyword evidence per type (adds up to 1), or None if no keyword matched."""
    t = text.lower()
    hits = {ty: len(set(m.group(0) for m in rx.finditer(t))) for ty, rx in TYPE_HINTS.items()}
    total = sum(hits.values())
    if total == 0:
        return None
    return {ty: n / total for ty, n in hits.items()}


def extract_people(text: str):
    """Return (count or None, many_flag)."""
    t = text.lower()
    counts = [int(m.group(1)) for m in _COUNT_DIGIT.finditer(t)]
    counts += [_NUM_WORDS[m.group(1)] for m in _COUNT_WORD.finditer(t)]
    counts = [c for c in counts if 0 < c < 1000]
    n = max(counts) if counts else None
    return n, bool(_MANY.search(t))


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_report(text: str, incident_type: str, location, night: bool = False):
    """Return dict(score, tier, reasons, keys, people, flags). `night` defaults to False
    so existing callers and tests are unaffected unless they opt in."""
    t, had_negated_injury = normalise(text)
    reasons = [{"label": BASE_LABEL[incident_type], "points": BASE_RISK[incident_type], "kind": "base"}]
    fired = set()
    matched_terms = set()

    for f in FACTORS:
        if f.get("only_types") and incident_type not in f["only_types"]:
            continue
        if f.get("skip_types") and incident_type in f["skip_types"]:
            continue
        m = f["rx"].search(t)
        if m:
            fired.add(f["key"])
            span = m.group(0).strip()
            if span and len(span) <= 40:
                matched_terms.add(span)

    # a bigger hazard replaces the smaller one instead of stacking
    if "major_hazard" in fired:
        fired.discard("hazard")

    for f in FACTORS:
        if f["key"] in fired:
            kind = "mitigating" if f["points"] < 0 else "factor"
            reasons.append({"label": f["label"], "points": f["points"], "kind": kind})

    people, many = extract_people(text)
    if people and people >= 10:
        reasons.append({"label": "Many people affected (about %d)" % people, "points": 25, "kind": "factor"})
        fired.add("multiple")
    elif people and people >= 5:
        reasons.append({"label": "Several people affected (about %d)" % people, "points": 20, "kind": "factor"})
        fired.add("multiple")
    elif people and people >= 2:
        reasons.append({"label": "Multiple people affected (%d)" % people, "points": 10, "kind": "factor"})
        fired.add("multiple")
    elif many:
        reasons.append({"label": "Several people affected", "points": 15, "kind": "factor"})
        fired.add("multiple")

    if had_negated_injury and "injury" not in fired:
        reasons.append({"label": NO_INJURY_LABEL, "points": NO_INJURY_POINTS, "kind": "mitigating"})

    if location and LOCATIONS[location]["sensitive"]:
        reasons.append({"label": "Busy location: %s" % location, "points": SENSITIVE_LOCATION_POINTS, "kind": "factor"})

    if night:
        reasons.append({"label": NIGHT_LABEL, "points": NIGHT_POINTS, "kind": "factor"})

    raw = sum(r["points"] for r in reasons)
    score = max(0, min(100, raw))
    flags = {
        "fire_words": bool(_FIRE_WORDS.search(t)),
        "electric": bool(_ELECTRIC.search(t)),
        "road": bool(location and LOCATIONS[location]["road"]),
    }
    # longest terms first, so the front-end highlights whole phrases before short words inside them
    terms_sorted = sorted(matched_terms, key=len, reverse=True)
    return {"score": score, "raw": raw, "tier": tier_for(score), "reasons": reasons,
            "keys": fired, "people": people, "flags": flags, "matched_terms": terms_sorted}


# ---------------------------------------------------------------------------
# Resource recommendation
# ---------------------------------------------------------------------------
def recommend_resources(incident_type: str, tier: str, keys: set, flags: dict):
    hurt = bool(keys & {"injury", "serious"})
    trapped = "trapped" in keys
    res = []

    if incident_type == "Fire":
        res.append("Fire Response")
        if hurt or trapped or "multiple" in keys:
            res.append("Medical Team")
        if hurt and tier == "Critical":
            res.append("Ambulance")
        if trapped:
            res.append("Rescue Team")
        if tier in ("Critical", "High"):
            res.append("Security")            # crowd control / evacuation

    elif incident_type == "Accident":
        if hurt or tier in ("Critical", "High"):
            res += ["Ambulance", "Medical Team"]
        if trapped:
            res.append("Rescue Team")
        if flags["fire_words"]:
            res.append("Fire Response")
        if flags["road"] or "access" in keys:
            res.append("Traffic/Security")
        if not res:
            res.append("Traffic/Security")

    elif incident_type == "Medical":
        if tier in ("Critical", "High"):
            res += ["Ambulance", "Medical Team"]
        else:
            res.append("Medical Team")
        if trapped:
            res.append("Rescue Team")

    elif incident_type == "Traffic":
        res.append("Traffic/Security")
        if "blocked" in keys:
            res.append("Maintenance")

    elif incident_type == "Infrastructure":
        res.append("Maintenance")
        if flags["electric"] and keys & {"hazard", "outage", "major_hazard"}:
            res.append("Electrician")
        if "water" in keys:
            res.append("Plumber")
        if trapped:
            res.append("Rescue Team")
        if "major_hazard" in keys:
            res += ["Fire Response", "Security"]
        if hurt or "concerning" in keys:
            res.append("Medical Team")
        if "serious" in keys:
            res.append("Ambulance")

    else:  # Other
        res.append("Security")
        if hurt:
            res.append("Medical Team")

    seen, out = set(), []
    for r in res:
        if r not in seen:
            seen.add(r)
            out.append({"name": r, "icon": RESOURCE_ICONS[r]})
    return out
