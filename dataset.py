"""Synthetic (demo) emergency-report dataset generator.

IMPORTANT: everything produced here is made-up demo data. It is NOT real
emergency data and must never be presented as real statistics.

Run:  python -m resq.dataset
Output: data/emergency_reports.csv  (~600 labelled reports)

Team tip: open the CSV in Excel and add your own rows. Keep the same columns.
`template_id` is optional; it lets the evaluation script test on phrasings the
model has never seen during training.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from .locations import LOCATIONS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "emergency_reports.csv"

# (type, priority, text). {loc} = location phrase, {n} = number of people.
# Roughly half of the templates are Hinglish, because that is how people really write.
TEMPLATES = [
    # ------------------------------------------------------------------ FIRE
    ("Fire", "Critical", "Fire has broken out at {loc} and {n} people are trapped inside"),
    ("Fire", "Critical", "Smoke is coming out of a room at {loc}, please send help immediately"),
    ("Fire", "Critical", "Building on fire near {loc}, flames are spreading fast"),
    ("Fire", "Critical", "Huge fire at {loc}, students are running out"),
    ("Fire", "Critical", "{loc} mein aag lag gayi hai, log andar fase hue hain"),
    ("Fire", "Critical", "{loc} ke paas se dhuan nikal raha hai, aag phail rahi hai"),
    ("Fire", "Critical", "Aag lagi hai {loc} mein, jaldi fire brigade bhejo"),
    ("Fire", "Critical", "Gas cylinder caught fire at {loc}, {n} people injured"),
    ("Fire", "Critical", "Thick black smoke at {loc}, we can see flames from the window"),
    ("Fire", "High", "Bike is burning in the open near {loc}"),
    ("Fire", "High", "Fire alarm is ringing near {loc} and there is a smell of burning"),
    ("Fire", "High", "Smoke visible from the roof of the building near {loc}"),
    ("Fire", "Medium", "{loc} mein jalne ki smell aa rahi hai aur halka dhuan hai"),
    ("Fire", "High", "Electrical panel started burning near {loc}"),
    ("Fire", "Medium", "Small fire in a dustbin near {loc}, staff is trying to put it out"),
    ("Fire", "Medium", "Someone is burning dry leaves behind {loc}, smoke is drifting, minor"),
    ("Fire", "Medium", "Fire at {loc} but it is under control now"),
    ("Fire", "Low", "Chhoti si aag lagi thi {loc} ke paas, ab control mein hai"),
    ("Fire", "Low", "Mock fire drill will be conducted at {loc} today"),
    ("Fire", "Low", "Fire safety drill going on at {loc}, please ignore the alarm"),
    # -------------------------------------------------------------- ACCIDENT
    ("Accident", "Critical", "There has been a road accident near {loc} and {n} people are injured"),
    ("Accident", "Critical", "Bike collided with a car at {loc}, rider is bleeding heavily"),
    ("Accident", "Critical", "{loc} ke paas accident ho gaya hai, {n} log ghayal hain"),
    ("Accident", "Critical", "A speeding car hit a student near {loc}, he is not moving"),
    ("Accident", "Critical", "Serious crash at {loc}, several people hurt, need ambulance"),
    ("Accident", "Critical", "Bus and bike collision at {loc}, people trapped in the vehicle"),
    ("Accident", "Critical", "Accident hua hai {loc} pe, khoon beh raha hai, jaldi ambulance bhejo"),
    ("Accident", "High", "Car hit a bike near {loc}, rider is hurt but conscious"),
    ("Accident", "High", "Student fell off a scooter at {loc} and injured his leg"),
    ("Accident", "High", "{loc} ke paas do bikes takra gayi, ek ladke ko chot lagi hai"),
    ("Accident", "High", "Auto rickshaw hit a pole near {loc}, driver is hurt"),
    ("Accident", "Medium", "Two vehicles collided at {loc}, the road is damaged but nobody knows if anyone is hurt"),
    ("Accident", "Medium", "Car crashed into the wall near {loc}"),
    ("Accident", "Low", "Minor collision at {loc}, nobody is hurt but vehicles are damaged"),
    ("Accident", "Low", "Two cars scratched each other at {loc}, no injuries"),
    ("Accident", "Low", "Halki takkar hui hai {loc} pe, koi ghayal nahi"),
    ("Accident", "Low", "Vehicle dented in the parking near {loc}, no one was hurt"),
    # --------------------------------------------------------------- MEDICAL
    ("Medical", "Critical", "Student collapsed at {loc} and is not breathing"),
    ("Medical", "Critical", "Suspected heart attack at {loc}, please send an ambulance immediately"),
    ("Medical", "Critical", "{loc} mein ek student behosh ho gaya hai, saans nahi aa rahi"),
    ("Medical", "Critical", "Severe allergic reaction at {loc}, person has difficulty breathing"),
    ("Medical", "Critical", "Someone is unconscious at {loc} and not responding"),
    ("Medical", "Critical", "Student is having a seizure at {loc}"),
    ("Medical", "Critical", "Bleeding heavily after a fall at {loc}, need a doctor urgently"),
    ("Medical", "High", "Student has chest pain and dizziness at {loc}"),
    ("Medical", "High", "Someone fainted at {loc} but is conscious now"),
    ("Medical", "High", "{n} students are vomiting after eating at {loc}, possible food poisoning"),
    ("Medical", "High", "Student has a deep cut on his hand at {loc}"),
    ("Medical", "High", "{loc} mein ek ladki ko chakkar aa rahe hain aur ulti ho rahi hai"),
    ("Medical", "High", "Fracture suspected, student cannot walk at {loc}"),
    ("Medical", "Medium", "Student has high fever and needs a doctor at {loc}"),
    ("Medical", "Medium", "Someone twisted an ankle at {loc}"),
    ("Medical", "Medium", "{loc} mein ek student ko bukhar hai, doctor chahiye"),
    ("Medical", "Medium", "Student is feeling weak and needs first aid at {loc}"),
    ("Medical", "Low", "Mild headache, student needs some medicine at {loc}"),
    ("Medical", "Low", "Need a band-aid for a small scratch at {loc}"),
    ("Medical", "Low", "Halka sa sar dard hai, tablet chahiye {loc} mein"),
    # --------------------------------------------------------------- TRAFFIC
    ("Traffic", "High", "Road is completely blocked near {loc}, ambulance cannot pass"),
    ("Traffic", "High", "{loc} ke paas road blocked hai"),
    ("Traffic", "High", "A fallen tree is blocking the road at {loc}"),
    ("Traffic", "High", "{loc} pe gaadiyon ki line lagi hui hai, rasta band hai"),
    ("Traffic", "Medium", "Heavy traffic jam at {loc}"),
    ("Traffic", "Medium", "A broken down truck is blocking one lane at {loc}"),
    ("Traffic", "Medium", "{loc} pe bahut jam laga hai"),
    ("Traffic", "Medium", "Major traffic jam near {loc}, vehicles are not moving"),
    ("Traffic", "Low", "Some vehicles are wrongly parked near {loc}"),
    ("Traffic", "Low", "Slow moving vehicles at {loc}, please send someone to manage"),
    ("Traffic", "Low", "{loc} ke paas gaadiyan galat parking mein khadi hain"),
    # -------------------------------------------------------- INFRASTRUCTURE
    ("Infrastructure", "Critical", "Wall of the building has collapsed at {loc}, people are trapped under debris"),
    ("Infrastructure", "Critical", "Gas leak at {loc}, {n} students feeling dizzy"),
    ("Infrastructure", "Critical", "Explosion heard at {loc}, people injured"),
    ("Infrastructure", "Critical", "Ceiling collapsed in a classroom at {loc}, students injured"),
    ("Infrastructure", "High", "Live electric wire has fallen near {loc}"),
    ("Infrastructure", "High", "Lift is stuck with {n} people inside at {loc}"),
    ("Infrastructure", "High", "Big crack in the wall at {loc}, it might collapse"),
    ("Infrastructure", "High", "{loc} mein lift mein log fase hue hain"),
    ("Infrastructure", "High", "Transformer sparking near {loc}"),
    ("Infrastructure", "Medium", "Water leakage in the corridor at {loc}"),
    ("Infrastructure", "Medium", "Power cut at {loc}, computers are down"),
    ("Infrastructure", "Medium", "{loc} mein bijli nahi hai kaafi der se"),
    ("Infrastructure", "Medium", "Water tank overflowing near {loc}"),
    ("Infrastructure", "Medium", "Toilet drainage overflowing at {loc}"),
    ("Infrastructure", "Low", "Street light is not working near {loc}"),
    ("Infrastructure", "Low", "{loc} mein tube light kharab hai"),
    ("Infrastructure", "Low", "Broken bench at {loc}"),
    ("Infrastructure", "Low", "Projector is not working at {loc}"),
    ("Infrastructure", "Low", "Wifi is down at {loc}"),
    ("Infrastructure", "Low", "{loc} mein tap se paani tapak raha hai"),
    # ----------------------------------------------------------------- OTHER
    ("Other", "Critical", "Two groups of students are fighting at {loc}, someone has a weapon"),
    ("Other", "High", "Fight broke out at {loc}, one student is bleeding"),
    ("Other", "High", "{loc} mein ladai ho rahi hai, kuch log ghayal hain"),
    ("Other", "High", "Someone is harassing girls at {loc}"),
    ("Other", "Medium", "Suspicious person roaming near {loc}"),
    ("Other", "Medium", "Bike theft reported at {loc}"),
    ("Other", "Medium", "{loc} ke paas ek anjaan aadmi ghoom raha hai, suspicious lag raha hai"),
    ("Other", "Medium", "A snake was seen near {loc}"),
    ("Other", "Low", "Lost my wallet somewhere near {loc}"),
    ("Other", "Low", "Loud music playing at {loc} at night"),
    ("Other", "Low", "Found a set of keys at {loc}"),
    ("Other", "Low", "Need permission to organise an event at {loc}"),
    ("Other", "Low", "{loc} mein mera phone kho gaya hai"),
]

# A second batch with different wording, so the model learns ideas instead of memorising sentences.
TEMPLATES += [
    # FIRE
    ("Fire", "Critical", "Flames are coming out of a window at {loc} and people are shouting for help"),
    ("Fire", "Critical", "Kitchen fire at {loc}, a worker has burns on his arms"),
    ("Fire", "Critical", "{loc} mein aag lagi hai, bahut dhuan hai, students bahar bhaag rahe hain"),
    ("Fire", "Critical", "The whole floor at {loc} is filled with smoke and {n} students cannot get out"),
    ("Fire", "Critical", "Sparks turned into a big fire at {loc}, it is spreading to other rooms"),
    ("Fire", "Critical", "Ek room mein aag lag gayi hai {loc} mein, andar {n} log hain"),
    ("Fire", "Critical", "Explosion followed by fire at {loc}, several people injured"),
    ("Fire", "High", "A vehicle caught fire near {loc}"),
    ("Fire", "High", "Burning smell and smoke coming from the AC vent at {loc}"),
    ("Fire", "High", "Garbage pile is on fire behind {loc}"),
    ("Fire", "High", "{loc} ke paas gaadi mein aag lag gayi hai"),
    ("Fire", "High", "Smoke is coming from the generator room near {loc}"),
    ("Fire", "Low", "Small fire in a trash can at {loc}, put out with an extinguisher"),
    ("Fire", "Medium", "Chhota sa fire hua tha {loc} pe, bujha diya gaya"),
    ("Fire", "Low", "Routine fire safety drill at {loc} this afternoon"),
    ("Fire", "Low", "Mock evacuation and fire drill practice at {loc}, no real fire"),
    # ACCIDENT
    ("Accident", "Critical", "Student run over by a vehicle near {loc}, lying on the road and bleeding"),
    ("Accident", "Critical", "Car overturned near {loc}, the driver is stuck inside and injured"),
    ("Accident", "Critical", "Bike skidded at high speed near {loc}, rider is unconscious"),
    ("Accident", "Critical", "Truck rammed into a group of people near {loc}, many are hurt"),
    ("Accident", "Critical", "Serious accident on the road near {loc}, {n} students injured"),
    ("Accident", "High", "Cyclist knocked down by a car at {loc}, has a leg injury"),
    ("Accident", "High", "Scooter slipped near {loc}, girl has a hand fracture"),
    ("Accident", "High", "{loc} ke paas ek bike sadak par gir gayi, chalane wale ko chot aayi hai"),
    ("Accident", "Medium", "Truck hit the boundary wall near {loc}"),
    ("Accident", "Medium", "Car reversed into a pole at {loc}"),
    ("Accident", "Medium", "Do gaadiyan takra gayi {loc} pe, kisi ko chot nahi lagi"),
    ("Accident", "Low", "Someone hit my parked bike near {loc}, minor scratch only"),
    ("Accident", "Low", "Small dent on a car at {loc}, no one is injured"),
    # MEDICAL
    ("Medical", "Critical", "Man collapsed near {loc}, there is no pulse"),
    ("Medical", "Critical", "Girl has stopped breathing at {loc}, help please"),
    ("Medical", "Critical", "Student had an asthma attack at {loc} and cannot breathe"),
    ("Medical", "Critical", "{loc} mein ek banda gir gaya hai aur hil nahi raha, behosh hai"),
    ("Medical", "Critical", "Very heavy bleeding from a deep cut at {loc}, urgent"),
    ("Medical", "High", "Student has severe pain in the chest at {loc}"),
    ("Medical", "High", "Girl is dizzy and vomiting at {loc}"),
    ("Medical", "High", "A student slipped and has a swollen leg, cannot stand at {loc}"),
    ("Medical", "High", "{loc} mein ek student ka pair toot gaya lagta hai"),
    ("Medical", "Medium", "Stomach ache since morning, student needs to see a doctor at {loc}"),
    ("Medical", "Medium", "Student has cold and cough and wants a checkup at {loc}"),
    ("Medical", "Medium", "Someone is running a temperature at {loc}"),
    ("Medical", "Medium", "{loc} par ek ladke ko pet dard hai"),
    ("Medical", "Low", "Need medicine for a mild cold at {loc}"),
    ("Medical", "Low", "Minor cut on a finger at {loc}, needs a bandage"),
    # TRAFFIC
    ("Traffic", "High", "Both lanes closed at {loc} because of a broken down bus, ambulance is stuck"),
    ("Traffic", "High", "Road blockage near {loc}, emergency vehicles cannot reach"),
    ("Traffic", "High", "Road is jammed near {loc}, nothing is moving and an ambulance is trying to pass"),
    ("Traffic", "Medium", "Long queue of vehicles outside {loc}, traffic jam after the event"),
    ("Traffic", "Medium", "Bad traffic congestion near {loc} since morning"),
    ("Traffic", "Medium", "{loc} par jam hai, gaadiyan hil nahi rahi"),
    ("Traffic", "Low", "Vehicles are parked on the footpath at {loc}"),
    ("Traffic", "Low", "Someone parked in front of the entrance at {loc}"),
    ("Traffic", "Low", "Traffic is a bit slow near {loc}"),
    ("Traffic", "Low", "Bikes have been left in the wrong spot near {loc}"),
    ("Traffic", "Low", "Many scooters are parked untidily at {loc}"),
    # INFRASTRUCTURE
    ("Infrastructure", "Critical", "Roof has caved in at {loc}, people are under the debris"),
    ("Infrastructure", "Critical", "Strong smell of gas at {loc}, students are coughing and dizzy"),
    ("Infrastructure", "Critical", "Transformer exploded near {loc}, people are hurt"),
    ("Infrastructure", "High", "Electric pole fell near {loc} with live wires on the road"),
    ("Infrastructure", "High", "Electric shock reported near {loc}, wires are exposed"),
    ("Infrastructure", "High", "Wall seems about to fall at {loc}"),
    ("Infrastructure", "High", "Elevator is jammed at {loc} and {n} people are inside"),
    ("Infrastructure", "Medium", "Pipe burst near {loc}, water everywhere"),
    ("Infrastructure", "Medium", "No electricity at {loc} since morning"),
    ("Infrastructure", "Medium", "Sewage water overflowing at {loc}"),
    ("Infrastructure", "Medium", "{loc} mein pani bhar gaya hai"),
    ("Infrastructure", "Low", "Fan is not working at {loc}"),
    ("Infrastructure", "Low", "Door lock is broken at {loc}"),
    ("Infrastructure", "Low", "Water cooler at {loc} is not working"),
    ("Infrastructure", "Low", "{loc} mein bulb fuse ho gaya hai"),
    ("Infrastructure", "Low", "Dustbin is full and needs to be cleaned at {loc}"),
    # extra everyday scenes
    ("Medical", "High", "Student fell down the stairs at {loc} and cannot get up"),
    ("Medical", "High", "Someone slipped on the wet floor at {loc} and is in a lot of pain"),
    ("Medical", "Medium", "My friend is not feeling well and has a headache and fever at {loc}"),
    ("Traffic", "Medium", "A cow is standing in the middle of the road near {loc}"),
    ("Traffic", "Medium", "Stray cattle are blocking part of the road at {loc}"),
    ("Other", "Medium", "A drunk man is creating trouble near {loc} and shouting at students"),
    ("Other", "Medium", "Two students are arguing loudly at {loc}, others are gathering"),
    ("Other", "Low", "Dust and construction noise near {loc}"),
    # OTHER
    ("Other", "High", "Some outsiders are threatening students at {loc}"),
    ("Other", "High", "Someone is carrying a knife near {loc}"),
    ("Other", "High", "Boys are beating up a junior at {loc}, he is bleeding"),
    ("Other", "High", "{loc} mein ragging ho rahi hai, ek ladka ro raha hai"),
    ("Other", "Medium", "Stranger is taking photos of students at {loc}, looks suspicious"),
    ("Other", "Medium", "Laptop stolen from {loc}"),
    ("Other", "Medium", "Bees hive on the roof of {loc}"),
    ("Other", "High", "Someone is stalking a girl near {loc}"),
    ("Other", "Low", "Lost my ID card near {loc}"),
    ("Other", "Low", "Noise from a party at {loc}"),
    ("Other", "Low", "I found a water bottle at {loc}"),
    ("Other", "Low", "Question about booking a room for an event at {loc}"),
]

# A third batch, aimed at the two categories that confused each other most in
# testing (Accident vs Medical, and Other vs everything else): more templates
# that keep each type's own vocabulary distinct.
TEMPLATES += [
    # ACCIDENT: keep collision/vehicle words front and centre
    ("Accident", "Critical", "Vehicle hit a student crossing the road near {loc}, he is on the ground bleeding"),
    ("Accident", "Critical", "Two-wheeler collided head-on with a car at {loc}, both riders thrown off"),
    ("Accident", "Critical", "{loc} ke paas gaadi ne bike ko takkar maari, rider sadak par gira hua hai"),
    ("Accident", "Critical", "Car skidded and hit the divider near {loc}, driver trapped inside"),
    ("Accident", "High", "Motorcycle hit a pothole and skidded near {loc}, rider has a leg injury"),
    ("Accident", "High", "{loc} ke paas ek gaadi footpath par chadh gayi, koi ghayal hua hai"),
    ("Accident", "High", "Cyclist was hit by a car door opening suddenly near {loc}"),
    ("Accident", "Medium", "Two bikes brushed against each other at {loc}, minor damage to both"),
    ("Accident", "Low", "A car reversed and tapped another car in the parking near {loc}, no injuries"),
    ("Accident", "Low", "Cycle fell over near {loc}, rider is fine, just checking the wheel"),
    # MEDICAL: symptoms only, no collision or vehicle language
    ("Medical", "Critical", "Student clutching his chest and struggling to breathe near {loc}"),
    ("Medical", "Critical", "A teacher suddenly went pale and collapsed while lecturing at {loc}"),
    ("Medical", "High", "Student's hands are shaking and he looks very unwell at {loc}"),
    ("Medical", "Medium", "Someone has a bad stomach ache and wants to go to the doctor from {loc}"),
    ("Medical", "Medium", "{loc} mein ek ladki ko periods se related dard ho raha hai, rest chahiye"),
    ("Medical", "Low", "Someone has a mild sore throat and wants cough syrup at {loc}"),
    # TRAFFIC vs INFRASTRUCTURE: keep vehicle-flow language distinct from fixed-asset language
    ("Traffic", "High", "Delivery truck double-parked at {loc} is blocking one whole lane"),
    ("Traffic", "Medium", "Auto rickshaws are queued up haphazardly outside {loc}, blocking the path"),
    ("Traffic", "Medium", "{loc} ke bahar bahut saari gaadiyan khadi hain, rasta tang ho gaya hai"),
    ("Traffic", "Low", "A cyclist is going the wrong way on the one-way near {loc}"),
    # OTHER: sharpen the everyday, non-emergency character of this bucket
    ("Other", "Medium", "A vendor is selling food without permission outside {loc}"),
    ("Other", "Medium", "Group of outsiders clicking photos near {loc} without permission"),
    ("Other", "Medium", "{loc} ke paas kisi ne apna bag chhod diya hai, malik nahi mil raha"),
    ("Other", "Low", "Can somebody unlock the notice board near {loc}, key is missing"),
    ("Other", "Low", "Asking if we can use {loc} for a club meeting this weekend"),
    ("Other", "Low", "A stray dog is sleeping near the entrance of {loc}, quite friendly"),
    ("Other", "Low", "{loc} ke paas kabaadi wala shor macha raha hai subah subah"),
    ("Other", "Medium", "An unattended bag has been left near {loc} for over an hour"),
    ("Other", "High", "A heated argument between two staff members turned physical near {loc}"),
]

PREFIXES = ["", "", "", "", "Sir, ", "Hello, ", "Please note: ", "Report: "]
SUFFIXES = ["", "", "", "", ".", " Please check.", " Kindly look into it.", " Thank you."]
NUM_WORDS = ["two", "three", "four", "five", "six", "seven", "eight", "ten"]

DEFAULT_RESOURCES = {
    ("Fire", "Critical"): "Fire Response; Medical Team; Rescue Team",
    ("Fire", "High"): "Fire Response; Security",
    ("Accident", "Critical"): "Ambulance; Medical Team; Traffic/Security",
    ("Accident", "High"): "Ambulance; Medical Team",
    ("Medical", "Critical"): "Ambulance; Medical Team",
    ("Medical", "High"): "Ambulance; Medical Team",
    ("Medical", "Medium"): "Medical Team",
    ("Medical", "Low"): "Medical Team",
    ("Traffic", None): "Traffic/Security; Maintenance",
    ("Infrastructure", None): "Maintenance",
    ("Other", None): "Security",
}


def default_resources(type_, priority):
    return (DEFAULT_RESOURCES.get((type_, priority))
            or DEFAULT_RESOURCES.get((type_, None))
            or {"Fire": "Fire Response", "Accident": "Traffic/Security"}.get(type_, "Maintenance"))


def _typo(text, rng):
    words = text.split()
    idx = [i for i, w in enumerate(words) if len(w) > 5 and w.isalpha()]
    if not idx:
        return text
    i = rng.choice(idx)
    w = words[i]
    j = rng.randrange(1, len(w) - 2)
    words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def generate(variants_per_template: int = 5, seed: int = 42):
    rng = random.Random(seed)
    rows, seen = [], set()
    for tid, (type_, priority, tpl) in enumerate(TEMPLATES):
        for _ in range(variants_per_template * 3):          # a few retries to avoid duplicates
            loc_name = rng.choice(list(LOCATIONS))
            loc_text = rng.choice(LOCATIONS[loc_name]["display"])
            n = rng.choice([rng.randint(2, 12), rng.choice(NUM_WORDS)])
            text = tpl.format(loc=loc_text, n=n)
            text = rng.choice(PREFIXES) + (text[0].upper() + text[1:] if rng.random() < 0.6 else text)
            text = text.rstrip(".") + rng.choice(SUFFIXES)
            if rng.random() < 0.12:
                text = _typo(text, rng)
            if text in seen:
                continue
            seen.add(text)
            rows.append({
                "report": text, "type": type_, "priority": priority,
                "location": loc_name, "resources": default_resources(type_, priority),
                "template_id": tid,
            })
            if sum(1 for r in rows if r["template_id"] == tid) >= variants_per_template:
                break
    rng.shuffle(rows)
    return rows


def write_csv(path: Path = CSV_PATH):
    rows = generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["report", "type", "priority", "location", "resources", "template_id"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    n = write_csv()
    print(f"Wrote {n} synthetic demo reports to {CSV_PATH}")
