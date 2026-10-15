# Weather-Aware Truck Routing

React + Django app that helps a truck driver pick the safest route using weather
along the route, load weight, and travel time.

- **Live app:** https://YOUR-APP.vercel.app
- **API:** https://YOUR-APP.onrender.com/api/ping/
- **Demo video:** YOUR_LOOM_LINK

> The backend runs on Render's free tier and sleeps when idle. The first request
> can take ~50 s to wake it up.

## What it does

The user enters origin, destination, departure date/time and load weight. The app:

1. Geocodes both addresses and generates 3 route options.
2. Places checkpoints along each route and computes the truck's ETA at each one.
3. Fetches the forecast for each checkpoint **at its ETA** (not at departure).
4. Classifies each checkpoint (Low / Moderate / High / Severe / No Travel) using the
   wind, rain, snow and load rules.
5. Ranks the routes and recommends one, with a written reason.
6. Shows routes, risk-colored checkpoints, ETAs and summaries on a map, plus a
   0-48 hour weather heatmap with a slider.

## Stack

| Part | Choice |
|---|---|
| Frontend | React (Vite), react-leaflet, leaflet.heat |
| Backend | Django, Django REST Framework |
| Routing + geocoding | Mapbox Directions / Geocoding |
| Weather | Open-Meteo (free, hourly, mph and inch units) |
| Hosting | Render (API), Vercel (frontend) |

## Architecture

```
POST /api/plan/
  geocode -> get_routes -> sample_route (checkpoints + ETAs)
          -> fetch_hourly (batched weather) -> analyze_route (risk per checkpoint)
          -> recommend -> build_heatmap -> JSON
```

All logic lives in `backend/planner/services/`; the view only handles HTTP.

| File | Responsibility |
|---|---|
| `risk.py` | Threshold and load rules for one checkpoint |
| `sampling.py` | Haversine distance, checkpoint spacing, ETAs |
| `weather.py` | Batched Open-Meteo calls, retries, 1 h cache |
| `analysis.py` | Risk per checkpoint, miles per risk level |
| `recommend.py` | Route ranking and explanation text |
| `routing.py` | Mapbox routes, de-duplication, detour fallback |
| `heatmap.py` | Corridor points and 49 hourly risk levels |

## Risk rules

Thresholds are taken exactly from the task. The worst of wind, rain and snow wins,
then the load rules can only raise the level:

- Wind >= 55 mph: No Travel for any load
- Wind 45-54 mph and load > 30,000 lb: No Travel
- Wind 35-44 mph and load > 40,000 lb: Severe

**Boundary decision:** the table overlaps at values like 0.25 in/hr. Lower bounds are
inclusive, so 0.25 is High. "No Travel" for rain and snow is written as `> 1.00` and
`> 3.0`, so exactly 1.00 in/hr rain is still Severe. Wind No Travel is `>= 55`.
Every threshold is unit tested on both sides.

## Route recommendation

Routes are compared in this order (lexicographic tuple, lowest wins):

1. **No Travel miles** (my addition: worse than Severe, so it comes first)
2. Severe miles
3. High miles
4. Average risk (0 = Low ... 4 = No Travel, mile-weighted)
5. Travel time

Miles are rounded to whole miles before comparing, so checkpoint-spacing noise
(for example 0.4 mi) can't decide a winner. Each checkpoint "owns" the road halfway
to its neighbours, which is how miles per risk level are computed. The winning
route gets a sentence such as "Route B: High miles 0 vs 50 on Route A".

## Assumptions

- **ETA is proportional to distance:** a checkpoint 40% of the way is reached 40%
  of the way through the drive time. A refinement would use per-step durations.
- **Truck speed:** Mapbox's driving profile uses car speeds, so average speed is
  capped at 55 mph (`TRUCK_MAX_AVG_MPH` in `routing.py`).
- **Checkpoint spacing:** 10 mi for trips up to 200 mi, 25 mi up to 600 mi, 50 mi
  beyond. This keeps weather lookups to roughly 20-60 per route.
- **Weather:** hourly sustained 10 m wind, rain, and snowfall from Open-Meteo, treated as
  in/hr for that hour. The nearest forecast hour to the ETA is used. Gusts are
  not used.
- **3 routes:** Mapbox often returns only 2. A third is forced by routing through a
  point offset perpendicular to the midpoint. Near-duplicate routes are removed.
- Missing weather values default to Low.
- Trips are US only (mph and inches).

## Performance

- Weather for all route checkpoints and the heatmap corridor is requested in batched
  calls and cached for an hour.
- The heatmap for all 49 hours (0-48) is computed once on the server and sent with
  the response, so the slider only swaps data in the browser: no refetch.
- Route geometry is thinned before sending.

## Run locally

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # add your MAPBOX_TOKEN
python manage.py test planner
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

Environment variables:

| Name | Where | Purpose |
|---|---|---|
| `MAPBOX_TOKEN` | backend | Routing and geocoding |
| `SECRET_KEY`, `DEBUG` | backend | Django settings |
| `CORS_ORIGINS` | backend | Comma-separated allowed frontend origins |
| `VITE_API_URL` | frontend | Backend base URL (build time) |

## Tests

`python manage.py test planner` covers every risk threshold on both sides, the load
rules, checkpoint spacing and ETAs, owned-miles math, route ranking order, duplicate
detection, heatmap shape, and API validation and error codes (400 / 502). External
APIs are mocked, so tests run offline.

## Known limitations

- Mapbox's driving profile is not truck-specific (no height, weight or hazmat
  restrictions); only the average speed is capped.
- Forecast covers about 16 days, so departures are limited to 13 days ahead to
  leave room for the 48-hour heatmap.
- Open-Meteo's free tier can return 429/503 when busy; the backend retries with
  backoff, but a trip may occasionally fail and need a retry.
- Heatmap uses about 60 sample points, so it is a coarse corridor view.
