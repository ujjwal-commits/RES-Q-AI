# RESQ-AI (v2.0)

AI-powered emergency information prioritisation and response support.
PSIT TechExpo 2026 screening prototype (decision support, simulated data).

## What's new in v2.0

- **Full-screen sign-in.** Signing in is now its own screen (not a popup over a visible dashboard) — the dashboard is only shown after a successful login.
- **Distinct heading font.** Headings (the RESQ-AI wordmark, panel titles, incident titles) use a bold display font (Unbounded); body text stays in a clean, readable font (Space Grotesk). Falls back to system fonts automatically if offline.
- **More motion throughout.** Panels swipe up into place on load, the logo has a subtle ambulance-light pulse, dialogs swipe up/down on open and close, and switching the priority filter or selecting an incident swipes the panel instead of snapping.
- Greetings are English-only now (previously mixed in Hindi/Hinglish phrases).
- **Immediate first-step guidance.** Every incident now shows a simulated "help is on the way" message with an ETA, plus two or three safe, pre-written first-aid and safety points for whoever is at the scene. This text is fixed and reviewed, not AI-generated, so the AI only ever picks which card to show — it never invents safety advice.
- **Individual team-member logins.** Seven named demo accounts (two per team, one Admin), each with their own username and password. Signing in shows your name in the header, and the dashboard now records who reported and who resolved every incident — see the **Recently handled** panel and the CSV export's new `reported_by` / `handled_by` columns.
- **Live clock** in the header, showing the real date and time.
- **RESQ-AI logo** in the header (the team's own artwork, background removed).

See the **Limitations** section at the bottom of the dashboard: logins here are for demo accountability, not real security, and the dispatch message is simulated, not a real emergency-services call.

## What was new in v1.2

- **Role-based login.** Pick a team on sign-in (Fire, Medical, Traffic & Security, Maintenance, or Admin) — no password, just for the demo. Each team's queue, map and stats are filtered to what's relevant to them; Admin sees everything. A random greeting (one of 20) welcomes you each time you sign in.
- **Nearest response point.** Five simulated stations (Fire Station, Ambulance Bay, Security Post, Traffic Post, Maintenance Depot) sit on the map. Every incident now shows which station is nearest for each recommended resource, with a straight-line distance and estimated time.
- **Night mode, in looks and in logic.** The dashboard follows the real clock and switches to a dark theme at night (with a manual toggle for daytime demos). Separately, live reports made late at night get a small priority boost, because fewer staff are usually on duty — shown clearly in the "Why" breakdown.
- **Compare wording.** A new "Compare wording" tool runs the same incident through the AI twice, worded two different ways, side by side — showing exactly how many points "under control" or "spreading fast" is worth.
- **Better AI accuracy.** Training data grew from 960 to 1,105 synthetic reports, focused on the two categories that were confusing the model most (Accident vs Medical, and the catch-all Other category). A confusion matrix is now shown in "How it works" so judges can see exactly where mistakes happen.
- **Dedicated limitations section.** Always visible at the bottom of the page, not just inside a dialog.
- **Smoother, livelier interface.** New incidents pop into the queue instead of just appearing; the priority counters count up instead of snapping; a small spinner shows while a report is being analysed.

## What was new in v1.1

- **Exact infrastructure alerts.** Instead of a generic "Infrastructure" label, the dashboard shows the specific problem: Electrical hazard, Power outage, Water leakage or flooding, Lift or people trapped, Structural collapse / explosion risk, or General maintenance issue.
- **Signals detected in the text.** The exact words that drove the AI's decision (like "trapped", "smoke", "bleeding") are underlined in the quoted report and listed as chips.
- **More structured campus map.** Added a compass, a colour legend, and schematic access-road lines connecting every building to the main road.
- **Smoother interface.** Buttons, cards and the priority queue transition instead of snapping.

## Run it

**Windows:** double-click `run.bat`.
The first time it installs `pandas` and `scikit-learn` (internet needed once). After that it works offline.

**Mac / Linux:** `./run.sh`

**By hand:**

```
pip install -r requirements.txt
python server.py
```

Your browser opens the dashboard by itself. If it does not, open the address printed in the terminal (usually http://127.0.0.1:8000).
Keep the terminal window open while you present.

## Demo accounts

No password reset, no sign-up — just sign in with one of these (also shown on the login screen itself):

| Username | Password | Role |
|---|---|---|
| `arjun` / `divya` | `fire123` | Fire Team |
| `rohit` / `sneha` | `med123` | Medical Team |
| `vikram` | `sec123` | Traffic & Security |
| `aman` | `maint123` | Maintenance Team |
| `admin` | `admin123` | Admin (sees everything) |

To add a real team member, edit `USERS` in `resq/auth.py` and restart the server.

## Demo script (4 minutes)

1. Sign in as **arjun / fire123**. Notice the greeting and your name in the header.
2. Click **Load demo scenario**. Notice the queue, map, and stats only show fire-relevant incidents. Click your name in the header to sign out, then sign back in as **admin / admin123** to see all fifteen.
3. Click the top incident. Show **Why Critical?** and **Signals detected**: every point of the score is traced to an underlined phrase in the report. Point out the pink **response box**: a simulated dispatch ETA plus pre-written first-aid and safety points — say clearly that this text is fixed and reviewed, not written by the AI.
4. Type a new report live (or let the judge type one), for example:
   *"A fire has been reported in the academic block and several people may be trapped."*
   Press **Analyse report**. Watch it pop into the top of the queue and appear on the map.
5. Click **Compare wording**. Run the Fire pair. Say: "same incident, worded differently — look at the score difference." This is a strong "the AI isn't just keyword-matching" moment.
6. Click the night/day toggle to show the dark theme. Mention that live reports made late at night also get a small priority boost, since fewer staff are on duty.
7. Click **Mark handled** on one incident, then point at **Recently handled**: it names who closed it out. Say: "the system suggests, a named human decides — and we can always see who."
8. Open **How it works**, scroll to the confusion matrix, and read out the limitations at the bottom of the page honestly.

## What is inside

| File | What it does | Team role |
|---|---|---|
| `resq/dataset.py` | Makes the synthetic training set (`data/emergency_reports.csv`) | AI/ML |
| `resq/model.py` | TF-IDF + Logistic Regression models (scikit-learn) | AI/ML |
| `resq/engine.py` | Priority engine: signals, scoring, resource rules, infra sub-types, night bonus | AI/ML |
| `resq/guidance.py` | Fixed, pre-written first-aid/safety cards and the simulated dispatch message | AI/ML |
| `resq/pipeline.py` | Joins model + engine + nearest-station lookup + guidance into one analysis | Backend |
| `resq/auth.py` | Team-member accounts, login sessions | Backend |
| `resq/store.py` | SQLite database of incidents, including who reported/handled each one | Backend |
| `server.py` | Web server and JSON API (login, preview, resolve with accountability) | Backend |
| `static/index.html` | The dashboard (login, queue, map, explanation, compare tool) | Frontend |
| `resq/locations.py` | Simulated campus places, map layout, and resource stations | Frontend / Backend |
| `resq/evaluation.py`, `evaluate.py` | Accuracy checks and confusion matrix | Research |
| `tests/` | Checks for the four plan examples | Everyone |

## How the AI decides

1. **Type** (Accident, Fire, Medical, Traffic, Infrastructure, Other): a TF-IDF + logistic regression model, plus a small keyword safety net for unusual wording.
2. **Location, people, danger signals**: pattern matching for English and Hinglish, including negation ("nobody is injured" is not an injury). Every matched phrase is kept so the dashboard can underline exactly which words drove the decision.
3. **Infrastructure alerts**: for Infrastructure reports, the exact sub-problem (Electrical hazard, Power outage, Water leakage/flooding, Lift or people trapped, Structural risk, or General maintenance) is worked out from the same signals, instead of a generic label.
4. **Priority score (0-100)** = base risk of the type + points for each danger signal - points for reassuring signals + a small bonus if a live report comes in at night (fewer staff on duty).
   Critical 70+, High 40+, Medium 20+, Low below 20.
5. **Resources**: rules based on type, priority and signals, each matched to the nearest simulated station.
6. **Confidence**: how strongly the type model and a second severity model agree with the final decision.

The score is deliberately rule-based so it can be explained. The ML part decides *what* is happening; the engine decides *how urgent* it is.

## Honest numbers

Run `python evaluate.py` to reproduce these (it now also prints a confusion matrix).

- Training data: about 1,105 made-up reports (English + Hinglish). **Synthetic, not real.**
- Type accuracy on phrasings the model never saw in training: about 79% for the model alone, about 89% with the keyword safety net.
- The two weakest categories (Accident vs Medical, and the catch-all Other) were specifically targeted with more training examples between v1.1 and v1.2, raising their individual accuracy from 79%/79% to about 89%/82%.
- The 36-sentence check set in `resq/evaluation.py` scores 100%, but it was used while tuning, so it is a sanity check, not a fair test.

Say clearly to judges: the data is synthetic and small, so these are prototype numbers, not real-world accuracy.

## Making it better (good tasks to split)

- **More data:** open `data/emergency_reports.csv` in Excel and add rows (`report`, `type`, `priority`, `location`, `resources`). Leave `template_id` empty for new rows. The models retrain every time the server starts.
- **New places:** edit `resq/locations.py` (name, words people use for it, map position).
- **New resource stations:** edit `RESOURCE_POINTS` in `resq/locations.py`.
- **New danger signals:** add an entry to `FACTORS` in `resq/engine.py` (label, points, patterns).
- **New compare-wording pairs:** edit `COMPARE_PAIRS` in `static/index.html`.
- **New or changed first-aid/safety text:** edit `GUIDANCE` / `INFRA_OVERRIDES` in `resq/guidance.py`. Have a teacher or trained adult review any wording changes before using it for real.
- **New team members:** edit `USERS` in `resq/auth.py`.
- **Keep reports between runs:** `python server.py --keep`.
- **Different port:** `python server.py --port 9000`.

## Limits

This is a decision-support prototype. It does not contact ambulances, police or hospitals, and it does not replace trained responders. Locations, the map and resource stations are all simulated, not real GPS, so the dispatch message and ETA are simulated too. Accounts give accountability for the demo, but passwords are stored in plain text in `resq/auth.py` and sessions are lost on restart — this is not real security. The first-aid/safety text is fixed and reviewed, not written by the AI, but it is general awareness only, not a substitute for proper first-aid training. The full list is always visible at the bottom of the dashboard.

## Future version (V3)

Real GPS, IoT sensors, hospital capacity, ambulance availability and traffic data feeding the same priority engine; real authentication (hashed passwords, password reset); a persistent activity log across restarts.
