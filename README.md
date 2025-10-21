
# GeoEco Tracker (Django + MySQL)

A prototype platform for Oman’s mining sector with environmental & geological focus.

## Quick Start (Windows / macOS / Linux)

1) Create a virtual environment and install deps:
```
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell
# or: source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

> If `mysqlclient` fails on Windows, install MySQL/MariaDB + C headers or use SQLite fallback (remove DB_* envs).

2) Create `.env` from template and set DB credentials (MariaDB 10.5+ or MySQL 8+ recommended):
```
copy .env.example .env   # Windows
# or: cp .env.example .env
```

3) Export env vars (PowerShell):
```
$env:SECRET_KEY="change-me"
$env:DB_NAME="geoeco"
$env:DB_USER="root"
$env:DB_PASSWORD="yourpassword"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
```

4) Create DB (MariaDB/MySQL):
```
CREATE DATABASE geoeco CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

5) Migrate & load demo data:
```
python manage.py makemigrations geoeco
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata seed.json
# or: python manage.py seed_geoeco
```

6) Run server:
```
python manage.py runserver
```

Pages:
- `/` Landing
- `/dashboard/`
- `/map/`
- `/investors/`
- `/search/`
- `/admin/`

## Data Notes
Demo dataset is illustrative. For real data, import official releases from:
- Oman National Center for Statistics & Information (NCSI) — mining & industry stats
- Ministry of Energy & Minerals publications
- OpenStreetMap for base map tiles (© contributors)

## License
Prototype for demonstration. Use at your own risk.
