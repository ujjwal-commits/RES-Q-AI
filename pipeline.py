"""Full analysis pipeline: report text in, structured decision-support record out.

    report -> type model (ML) -> location + signal extraction -> priority engine
           -> resource recommendation -> nearest station -> confidence
"""
from __future__ import annotations

import time

from .engine import TIERS, infra_subtype, is_night_hour, keyword_type_prior, recommend_resources, score_report
from .guidance import dispatch_message, guidance_for
from .locations import extract_location, nearest_resource

# Type decision = 70% ML model + 30% keyword evidence. The keywords act as a safety
# net for sentences that are worded differently from anything in the training data.
ML_WEIGHT = 0.7
# Below this confidence the dashboard asks for a human to double-check.
REVIEW_BELOW = 60


class Analyzer:
    def __init__(self, brain):
        self.brain = brain

    def analyze(self, text: str, night: bool | None = None) -> dict:
        """`night`: True/False to force it (used by tests and the demo scenario),
        or None to detect it from the server's real clock (used for live reports)."""
        text = " ".join(str(text).split())
        if night is None:
            night = is_night_hour(time.localtime().tm_hour)
        type_probs = self.brain.type_probs(text)
        sev_probs = self.brain.severity_probs(text)

        ml_top = max(type_probs, key=type_probs.get)
        prior = keyword_type_prior(text)
        if prior:
            type_probs = {t: ML_WEIGHT * p + (1 - ML_WEIGHT) * prior.get(t, 0.0) for t, p in type_probs.items()}
        incident_type = max(type_probs, key=type_probs.get)
        assisted = incident_type != ml_top

        location = extract_location(text)
        scored = score_report(text, incident_type, location, night=night)
        tier = scored["tier"]

        # Confidence = how well the two ML models agree with the final decision.
        type_p = type_probs.get(incident_type, 0.0)
        sev_p = sev_probs.get(tier, 0.0)
        confidence = int(round(100 * (0.5 * type_p + 0.5 * sev_p)))
        confidence = max(25, min(99, confidence))

        resources = recommend_resources(incident_type, tier, scored["keys"], scored["flags"])
        subtype = infra_subtype(scored["keys"]) if incident_type == "Infrastructure" else None

        nearest = []
        for r in resources:
            n = nearest_resource(r["name"], location)
            if n:
                nearest.append({"resource": r["name"], "icon": r["icon"], **n})

        guidance = guidance_for(incident_type, subtype)
        dispatch = dispatch_message(nearest)

        notes = []
        if assisted:
            notes.append("Keyword rules overrode the first guess of the AI model.")
        if not location:
            notes.append("Location not recognised. Ask the reporter where this is.")
        if confidence < REVIEW_BELOW:
            notes.append("Low confidence. A human should double-check this one.")
        if night:
            notes.append("Reported during night hours: fewer staff are usually on duty.")

        top3 = sorted(type_probs.items(), key=lambda kv: -kv[1])[:3]
        return {
            "type": incident_type,
            "subtype": subtype,
            "priority": tier,
            "score": int(round(scored["score"])),
            "confidence": confidence,
            "location": location,
            "people": scored["people"],
            "resources": resources,
            "nearest": nearest,
            "guidance": guidance,
            "dispatch": dispatch,
            "night": night,
            "reasons": scored["reasons"],
            "matched_terms": scored["matched_terms"],
            "needs_review": confidence < REVIEW_BELOW or not location,
            "notes": notes,
            "model": {
                "type_top3": [[k, round(v, 3)] for k, v in top3],
                "severity": [[t, round(sev_probs.get(t, 0.0), 3)] for t in TIERS],
                "rule_assisted": assisted,
            },
        }

