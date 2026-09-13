# Assetra

A web-based company asset tracking and management system. Register physical
assets (laptops, printers, monitors, tools, equipment), print a QR code for
each one, and scan it to instantly see what it is, where it is, who has it,
and its condition.

## Stack

- **Backend:** Flask (Python)
- **Database:** SQLite, accessed with plain SQL (no ORM) via Python's built-in
  `sqlite3` module — see `schema.sql` for the full schema
- **Frontend:** server-rendered HTML/CSS/JS (Jinja2 templates), no build step
- **QR codes:** generated client-side in the browser with `qrcode.js`
  (loaded from a CDN), encoding the direct URL to each asset's detail page

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Then open **http://localhost:5000** in your browser. The database
(`instance/assetra.db`) and a few starter departments/locations are created
automatically on first run.

To scan QR codes with an actual phone, the phone needs to reach the server's
address (not `localhost`) — see **Scanning from a phone** below.

## How it works

1. **Register an asset** (`+ Register asset`) — name, category, serial
   number, department, location, condition, purchase info, and optionally
   assign it to an employee right away. Assetra generates a sequential
   asset tag like `AST-00001`.
2. Each asset's **detail page** (`/assets/<id>`) is rendered with a QR code
   in the top-right of the tag card. That QR code encodes the direct link
   to that same page — print it and stick it on the physical item.
3. **Scanning the QR** with a phone opens the detail page directly, showing
   asset name, ID, serial number, department, location, assigned employee,
   condition, current status, purchase info, and maintenance history.
4. From that page you can **assign/unassign**, **transfer** (department or
   location), **change status/condition**, and **log maintenance** — every
   action is recorded in the asset's **history** timeline.
5. **Search** (`/assets`) filters by name, tag, serial number, assignee,
   status, category, or department.
6. **Employees** and **Departments & Locations** are managed under their own
   pages and used throughout as dropdowns.

## Scanning from a phone

By default Flask runs on `0.0.0.0:5000`, so any device on the same Wi-Fi
network can reach it at `http://<your-computer's-LAN-IP>:5000`. Find your
LAN IP (e.g. `ipconfig` on Windows, `ifconfig`/`ip addr` on Mac/Linux), then
the QR codes will encode `http://127.0.0.1:5000/...` by default — for
phone scanning to work, run the app in a way where `request.url_root`
resolves to that LAN IP (e.g. access the app yourself at
`http://<LAN-IP>:5000` in your browser first, since the QR code uses
whatever host you loaded the page from). For real deployment, put this
behind a proper domain/HTTPS and the QR codes will encode that instead.

## Project structure

```
assetra/
  app.py                 # Flask routes (all application logic)
  db.py                  # SQLite connection + init/seed helpers
  schema.sql             # Full database schema (plain SQL)
  requirements.txt
  templates/              # Jinja2 HTML templates
  static/css/style.css    # Design system (single stylesheet)
  instance/assetra.db     # SQLite database (created on first run)
```

## Notes on scope / what's included

- Full CRUD for assets, with sequential asset tags and QR codes
- Assign / unassign to employees
- Transfer between departments and locations
- Status (Available, Assigned, In Repair, Retired, Lost) and condition
  (New, Good, Fair, Poor, Damaged) tracking
- Maintenance log per asset
- Full audit history per asset (every change is timestamped and logged)
- Search and filtering
- Employee and department/location management
- Dashboard with counts by status/category and recent activity feed

## Things you'd likely want before production use

- Authentication / login and role-based permissions (currently anyone with
  network access can use the app — there's no user accounts yet)
- Switching `app.secret_key` to a real secret via environment variable
  (already reads `ASSETRA_SECRET_KEY` if set)
- A production WSGI server (gunicorn/waitress) instead of Flask's dev server
- Optionally moving from SQLite to PostgreSQL for multi-user concurrent
  write load (the SQL in `schema.sql`/`app.py` is close to portable, but
  `datetime('now')` and `AUTOINCREMENT` are SQLite-specific)
