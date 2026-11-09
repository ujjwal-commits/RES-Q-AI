# RESQ-AI

**AI-assisted emergency information prioritisation and response-support prototype.**

RESQ-AI is an educational prototype that analyses submitted incident descriptions, assigns an indicative category and priority, and presents simulated response-support information through a browser dashboard.

> **Important:** This is a demonstration/academic prototype. It is not connected to emergency services, dispatch systems, live responders, or verified real-world incident data. It must not be used to make real emergency decisions. In an actual emergency, contact the appropriate local emergency services.

## Features

- Text-based incident report analysis
- Indicative incident category and priority classification
- Dashboard for viewing and managing demo incidents
- Simulated response resources and location information
- Public demo access without a login or password
- CSV export of demonstration records
- Synthetic sample dataset and evaluation utilities

## Technology

- Python
- pandas
- scikit-learn
- SQLite
- HTML, CSS and JavaScript

## Run locally

1. Install Python 3.10 or later.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. No account, username, or password is required. The dashboard opens directly.

5. Start the application:

   ```bash
   python server.py
   ```

6. Open the local URL printed in the terminal (normally `http://127.0.0.1:8000`).

## Public demo access

The demo is intentionally open: visitors do not need an account or password. Anyone with the public demo URL can submit reports, load or clear the shared demonstration queue, and export demo records. Do not enter real personal, sensitive, or emergency information. This is an academic prototype, not a production emergency service.

## Deploying a public demo

A Render blueprint is included in `render.yaml`.

1. Push this repository to GitHub.
2. Create a new Blueprint on Render and select the repository.
3. Deploy and open the generated public URL. No login configuration is required.

## Data and model limitations

- The included training data is synthetic demonstration data.
- Classification results are indicative and may be wrong or incomplete.
- Response points, dispatch messages, travel estimates and related dashboard elements are simulated.
- Any guidance displayed is predefined demonstration content and is not a substitute for advice from qualified emergency personnel.
- The application has not been validated for real-world emergency operations.

## Repository contents

- `server.py` — built-in Python HTTP server and API routes
- `resq/` — classification, pipeline, guidance, location and storage modules
- `static/index.html` — browser dashboard
- `data/` — included synthetic demonstration dataset
- `tests/` — project tests
- `evaluate.py` — model evaluation entry point

## Testing

Run the available tests with:

```bash
python -m unittest discover -s tests -v
```

## Credits

Academic project developed as a computer science project. Update this section with the verified team members, institutional details and acknowledgements before publishing.
