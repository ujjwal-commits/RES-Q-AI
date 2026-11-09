"""Honest accuracy checks.

1. Template-grouped cross-validation on the synthetic dataset. Each fold is
   tested on phrasings (templates) the model never saw in training. This is
   much stricter than a normal random split, which would look unrealistically
   perfect because synthetic data repeats itself.

2. A small hand-written check set (CHECK_SET below): sentences we wrote
   separately from the dataset templates, with the answer we expect.

Neither number is a real-world accuracy. The data is synthetic and small.
Say that clearly when presenting.
"""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import GroupKFold, StratifiedKFold

from .engine import TIERS
from .model import Brain, build_pipeline
from .pipeline import Analyzer

# (report, expected type, expected priority)
CHECK_SET = [
    ("A building is on fire and 10 people are trapped.", "Fire", "Critical"),
    ("Thick smoke coming from the chemistry lab, students are running out.", "Fire", "Critical"),
    ("Fire drill scheduled at the academic block at 11 am.", "Fire", "Low"),
    ("Bike is burning in the parking area.", "Fire", "High"),
    ("Canteen kitchen caught fire, cook has burns on his arm.", "Fire", "Critical"),
    ("Ek chhoti si aag lagi thi library ke peeche, ab bujh gayi hai.", "Fire", "Low"),
    ("Two students got hit by a speeding car near Gate 2, one is bleeding badly.", "Accident", "Critical"),
    ("A student fell from his bike near the hostel and hurt his knee.", "Accident", "High"),
    ("Two cars touched each other in the parking, nobody is hurt, just minor scratches.", "Accident", "Low"),
    ("Truck overturned on the main road, driver stuck inside the cabin.", "Accident", "Critical"),
    ("Bus se takkar ho gayi hai gate 2 ke paas, kai log ghayal hain.", "Accident", "Critical"),
    ("A girl fainted in the classroom and is now awake and conscious.", "Medical", "High"),
    ("Professor suffered a heart attack in the staff room.", "Medical", "Critical"),
    ("Student complaining about stomach pain since morning.", "Medical", "Medium"),
    ("Need first aid for a small paper cut at the library.", "Medical", "Low"),
    ("Hostel mein ek ladke ko dora pada hai, wo behosh hai.", "Medical", "Critical"),
    ("Someone is having trouble breathing after an asthma attack near the canteen.", "Medical", "Critical"),
    ("Huge traffic jam in front of Gate 2, cars honking.", "Traffic", "Medium"),
    ("A fallen tree is blocking the main road and an ambulance is waiting behind it.", "Traffic", "High"),
    ("Bikes are parked in the wrong place near the library.", "Traffic", "Low"),
    ("Gate 1 pe vehicles ki line lagi hui hai, road band hai.", "Traffic", "High"),
    ("The corridor lights on the second floor are not working.", "Infrastructure", "Low"),
    ("Electric wire is hanging low near the parking and a child touched it.", "Infrastructure", "High"),
    ("Water tank overflowing near the hostel, floor is slippery.", "Infrastructure", "Medium"),
    ("Power cut in the computer lab since morning.", "Infrastructure", "Medium"),
    ("Roof of the canteen has partially collapsed, two workers are under the debris.", "Infrastructure", "Critical"),
    ("AC in room 204 is not cooling.", "Infrastructure", "Low"),
    ("Smell of gas in the lab, several students coughing.", "Infrastructure", "Critical"),
    ("Someone stole my laptop from the library.", "Other", "Medium"),
    ("Group of boys are fighting near the ground with sticks.", "Other", "High"),
    ("Found a black wallet near the canteen.", "Other", "Low"),
    ("Unknown person is roaming around girls hostel.", "Other", "Medium"),
    ("Loud DJ music from hostel roof, students are disturbed.", "Other", "Low"),
    ("Ragging incident reported in the hostel, a junior is crying.", "Other", "High"),
    ("Mera phone kho gaya hai, kisi ko mile toh batana.", "Other", "Low"),
    ("Sir there is a snake in the boys hostel corridor.", "Other", "Medium"),
]


def _cv_type_accuracy(df):
    """Accuracy on phrasings the model never saw: (ML alone, ML + keyword rules),
    plus a confusion matrix (actual type -> predicted type -> count) for the hybrid decision."""
    df = df.reset_index(drop=True)
    if "template_id" in df.columns and df["template_id"].notna().all():
        splits = GroupKFold(n_splits=5).split(df, df["type"], groups=df["template_id"])
    else:
        splits = StratifiedKFold(n_splits=5, shuffle=True, random_state=0).split(df, df["type"])
    ml_ok = hybrid_ok = total = 0
    types = sorted(df["type"].unique())
    confusion = {a: {p: 0 for p in types} for a in types}
    for tr, te in splits:
        brain = Brain(df=df.iloc[tr])
        analyzer = Analyzer(brain)
        for text, truth in zip(df.iloc[te]["report"], df.iloc[te]["type"]):
            probs = brain.type_probs(text)
            ml_ok += max(probs, key=probs.get) == truth
            pred = analyzer.analyze(text, night=False)["type"]
            hybrid_ok += pred == truth
            confusion[truth][pred] += 1
            total += 1
    return round(ml_ok / total, 3), round(hybrid_ok / total, 3), {"types": types, "matrix": confusion}


def run_checks(brain: Brain, analyzer: Analyzer, with_cv: bool = True):
    tier_index = {t: i for i, t in enumerate(TIERS)}
    type_ok = prio_ok = prio_close = 0
    misses = []
    for text, want_type, want_prio in CHECK_SET:
        out = analyzer.analyze(text, night=False)
        type_ok += out["type"] == want_type
        prio_ok += out["priority"] == want_prio
        prio_close += abs(tier_index[out["priority"]] - tier_index[want_prio]) <= 1
        if out["type"] != want_type or out["priority"] != want_prio:
            misses.append({"report": text, "expected": [want_type, want_prio],
                           "got": [out["type"], out["priority"]]})
    n = len(CHECK_SET)
    result = {
        "dataset_rows": int(len(brain.df)),
        "check_set_size": n,
        "check_type_accuracy": round(type_ok / n, 3),
        "check_priority_exact": round(prio_ok / n, 3),
        "check_priority_within_one": round(prio_close / n, 3),
        "misses": misses,
    }
    if with_cv:
        ml_only, hybrid, confusion = _cv_type_accuracy(brain.df)
        result["cv_type_ml_only_unseen_phrasing"] = ml_only
        result["cv_type_ml_plus_rules_unseen_phrasing"] = hybrid
        result["confusion_matrix"] = confusion
    return result
