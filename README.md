
# Weather-Aware Truck Routing

A full-stack web application that helps truck drivers compare route alternatives using travel time, distance, weather conditions, and weather-related driving risk.

The application combines route planning, checkpoint-level weather analysis, risk-based route recommendations, an interactive map, and a time-based weather forecast heatmap.

## Live Demo

- **Live Application:** https://weather-truck-routing-app.onrender.com
- **Backend API:** https://weather-truck-routing-pyq0.onrender.com/
- **GitHub Repository:** https://github.com/AnUsHkAIT/weather-truck-routing

## Features

- **Route planning:** Enter an origin, destination, departure date and time, and truck load weight.
- **Multiple route alternatives:** Compare three available route options by distance, estimated travel time, and arrival time.
- **Weather-aware recommendations:** Rank routes using weather-related risk, higher-risk mileage, and travel duration.
- **Checkpoint weather analysis:** View estimated arrival times, wind speed, rainfall, snowfall, and risk classifications at points along a route.
- **Risk classification:** Categorize weather conditions into Low, Moderate, High, Severe, and No Travel levels according to the configured risk rules.
- **Load-aware risk assessment:** Incorporate truck load weight into applicable weather-risk calculations.
- **Interactive route map:** View route alternatives and checkpoints on a map.
- **Weather forecast heatmap:** Explore forecast conditions over time using an interactive slider.
- **Dynamic recalculation:** Update route alternatives and map results when trip inputs change.
- **Input and forecast validation:** Reject invalid inputs and handle missing required weather measurements or forecast times outside the available data range.

## Technology Stack

### Frontend
- React
- Vite
- JavaScript
- Leaflet and React Leaflet
- Leaflet heatmap visualization

### Backend
- Python
- Django
- Django REST Framework

### External Services
- Mapbox for geocoding and route directions
- Open-Meteo for weather forecast data
- OpenStreetMap map tiles and map data attribution

### Deployment
- Render for the hosted frontend and backend
- GitHub for source control

## How It Works

1. **Enter trip details.** Provide the origin, destination, departure date and time, and truck load weight.
2. **Generate route alternatives.** The backend obtains available route options and their distances and travel durations.
3. **Estimate checkpoint arrival times.** The application estimates when the truck reaches checkpoints along each route.
4. **Retrieve weather data.** Weather conditions are evaluated against the estimated arrival times.
5. **Calculate weather-related risk.** The backend applies the configured risk rules to the available weather measurements and relevant load information.
6. **Compare route alternatives.** Routes are evaluated using risk severity and mileage, average risk, and travel time.
7. **Display the results.** The frontend presents route summaries, checkpoint weather details, the interactive map, and the weather forecast heatmap.

## Route Recommendation

The application compares routes using a safety-first approach.

The recommendation considers:
- Mileage associated with No Travel conditions
- Severe-risk mileage
- High-risk mileage
- Average route risk
- Estimated travel time

When routes have comparable risk metrics, shorter travel time can help determine the recommended option.

The recommendation is based on the application's configured risk rules and the weather data available for the evaluated trip.

## Weather Risk Assessment

Weather conditions are evaluated at route checkpoints using the available forecast data, including:

- Wind speed
- Rainfall
- Snowfall
- Estimated checkpoint arrival time
- Truck load weight, where applicable to the configured rules

The application classifies risk into five categories:

| Category | Meaning |
|---|---|
| Low | Lower weather-related driving risk |
| Moderate | Conditions requiring additional caution |
| High | Elevated weather-related driving risk |
| Severe | Serious weather-related driving risk |
| No Travel | Conditions classified by the configured rules as unsuitable for travel |

Risk classifications depend on the implemented thresholds and available weather measurements. Missing required weather data is not automatically treated as safe.

## Local Development

### Prerequisites

Install the following:

- Python 3.10 or a compatible version supported by the project
- Node.js and npm
- Git
- A Mapbox access token for routing and geocoding functionality

### 1. Clone the repository

```bash
git clone https://github.com/AnUsHkAIT/weather-truck-routing.git
cd weather-truck-routing
```

### 2. Set up the backend

Open a terminal in the project root:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

Configure the required backend environment variables using the project's environment example and Django settings. Add your Mapbox access token and any other required configuration. Do not commit secrets to GitHub.

Apply migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

The backend should now be available at:

http://127.0.0.1:8000/

### 3. Set up the frontend

Open a second terminal and navigate to the frontend directory:

```bash
cd frontend
npm install
```

Configure the frontend API base URL using the variable documented in the frontend environment example. For local development, it should point to the local Django backend.

Start the development server:

```bash
npm run dev
```

Open the local URL printed by Vite in the terminal.

> Note: If your frontend directory or environment-variable names differ, follow the actual project structure and the provided `.env.example` file.

## Running Tests

From the backend directory, activate the virtual environment and run:

```bash
python manage.py test planner
```

Run Django's system check with:

```bash
python manage.py check
```

The project's backend test suite covers route-planning and weather-risk functionality, including validation of weather inputs and risk calculations.

## Deployment

The application is deployed using Render.

- Frontend: https://weather-truck-routing-app.onrender.com
- Backend: https://weather-truck-routing-pyq0.onrender.com/

For deployment, configure the frontend API base URL to point to the deployed backend. Configure the backend's required environment variables, allowed hosts, and CORS settings in Render.

Keep API tokens and other secrets in environment variables rather than committing them to the repository.

After deploying new changes, verify that the backend is live and that the frontend can successfully request route-planning results.

## Project Structure

The repository contains the React frontend and Django backend.

```text
weather-truck-routing/
├── backend/
│   ├── config/
│   ├── planner/
│   │   ├── services/
│   │   └── tests/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   └── ...
├── .gitignore
└── README.md
```

The backend contains the route-planning API, weather and risk-analysis services, and automated tests. The frontend contains the trip input form, route comparison interface, map, checkpoint information, and forecast heatmap.

## Limitations

- Weather results depend on the coverage, availability, and time range of the external forecast service.
- Estimated arrival times and checkpoint weather conditions may differ from actual conditions during a trip.
- Risk classifications depend on the implemented thresholds and available weather measurements.
- Route availability depends on the routing service and the locations supplied.
- This application is a route-planning aid, not a substitute for official road closures, current weather warnings, applicable driving regulations, or professional safety judgment.

## Future Improvements

- Add more detailed truck-specific restrictions, including height, weight, and hazardous-material constraints.
- Incorporate live traffic and road-closure data.
- Expand weather-risk validation using additional scenarios and forecast conditions.
- Improve route comparison with additional operational costs and fuel-consumption estimates.
- Add historical trip analysis and downloadable route reports.

## License

No license has been specified for this project. Contact the repository owner for permission before redistributing or reusing the code.
