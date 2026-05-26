# Frontend to Backend Notes

This frontend now includes UI for:

- route calculation
- full recent paths page
- full saved paths page
- login page
- sign-up page
- account page
- naming saved routes
- showing saved routes with a heart marker
- login-gated route saving

## What the frontend already does

### Recent paths

Every calculated route is added to `recentPaths` on the frontend.

Right now this is only local frontend storage. In the real version, recent paths should be stored per logged-in user in the backend.

Each recent path contains:

```json
{
  "id": "path-123",
  "createdAt": "2026-05-16T10:15:00Z",
  "name": "Route 16 May 10:15",
  "saved": false,
  "startPoint": { "lat": 52.2297, "lng": 21.0122 },
  "endPoint": { "lat": 52.2100, "lng": 21.0300 },
  "preferences": {
    "greenery": 70,
    "noise": 50,
    "airQuality": 60
  },
  "route": [
    { "lat": 52.2297, "lng": 21.0122 },
    { "lat": 52.2250, "lng": 21.0180 },
    { "lat": 52.2100, "lng": 21.0300 }
  ]
}
```

### Saved paths

When the user saves a route, they must provide a name.

Saving should only be available for logged-in users. The frontend already reflects this:

- if the user is not logged in, the `Save route` button is greyed out
- hovering it shows that login is required
- if someone bypasses that state, `App.jsx` still blocks the save action

Frontend behavior:

- the route stays in `recentPaths`
- the route is also added to `savedPaths`
- the same route gets `saved: true`
- a heart is shown next to the route name

Saved paths use the same shape, but:

```json
{
  "saved": true,
  "name": "Evening Vistula Walk"
}
```

## Main integration points

## Where to connect backend

The main places to replace frontend-only mock/local logic are:

- `src/App.jsx`
  - `calculateRoute()`: replace mock route calculation with backend call
  - `handleAuthSubmit()`: replace mock login/sign-up with backend auth call
  - `rememberRecentPath()`: later save recent routes through backend
  - `handleSaveCurrentRoute()` and `handleConfirmSavePath()`: later save named routes through backend
  - `useEffect(...)` blocks using `localStorage`: replace with backend fetch/load when session is known

- `src/components/RoutePanel.jsx`
  - save button is already login-gated in the UI

- `src/components/AuthPage.jsx`
  - login and sign-up form submit points

- `src/components/PathsPage.jsx`
  - shows the recent/saved route data returned from backend

### 1. Route calculation

Current live frontend behavior in `src/App.jsx`:

- `calculateRoute()` already calls the backend
- current endpoint is:

```http
POST /api/routes/walking
```

Current request body used by the frontend:

```json
{
  "start": { "lat": 52.2297, "lng": 21.0122 },
  "end": { "lat": 52.2100, "lng": 21.0300 },
  "weights": {
    "greenery": 0.7,
    "noise": 0.5,
    "air_quality": 0.6
  }
}
```

Current goal:

- calculate real routes on the walking graph
- use preference weights when the backend graph has environmental scores
- fall back to distance-only behavior when only the base graph is available

Current expected response body:

```json
{
  "route": [
    { "lat": 52.2297, "lng": 21.0122 },
    { "lat": 52.2250, "lng": 21.0180 },
    { "lat": 52.2100, "lng": 21.0300 }
  ],
  "distance_m": 2400.5,
  "estimated_duration_s": 1920,
  "scores": {
    "greenery": 0.5,
    "air_quality": 0.5,
    "noise": 0.5
  },
  "debug": {
    "start_snapped_distance_m": 18.3,
    "end_snapped_distance_m": 12.7,
    "algorithm": "dijkstra",
    "cost_model_version": "..."
  }
}
```

The frontend only needs `route` to draw the polyline, but the extra fields are already accepted.

The frontend sliders are stored as 0-100 percentages and sent to the backend as normalized 0-1 weights.

### 2. Login

Suggested endpoint:

```http
POST /api/auth/login
```

Suggested request body:

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Suggested frontend wiring:

- call this from `handleAuthSubmit()` when mode is `login`
- store returned user/session token
- then load recent and saved paths for that user

Suggested response body:

```json
{
  "user": {
    "id": "user-1",
    "name": "Anna",
    "email": "user@example.com"
  },
  "token": "jwt-or-session-token"
}
```

### 3. Sign up

Suggested endpoint:

```http
POST /api/auth/signup
```

Suggested request body:

```json
{
  "name": "Anna",
  "email": "user@example.com",
  "password": "secret"
}
```

Suggested frontend wiring:

- call this from `handleAuthSubmit()` when mode is `signup`
- after success, treat the user as logged in

Suggested response body:

```json
{
  "user": {
    "id": "user-1",
    "name": "Anna",
    "email": "user@example.com"
  },
  "token": "jwt-or-session-token"
}
```

### 4. Current session / account

Suggested endpoint:

```http
GET /api/auth/me
```

Suggested response body:

```json
{
  "user": {
    "id": "user-1",
    "name": "Anna",
    "email": "user@example.com"
  }
}
```

Suggested frontend wiring:

- call on app start if a token/session exists
- use this to restore the signed-in user and then load their paths

### 4a. Logout

Suggested endpoint:

```http
POST /api/auth/logout
```

Suggested frontend wiring:

- clear local user state
- clear user-specific recent/saved path state

### 5. Recent paths

Right now recent paths use `localStorage`.

If backend persistence is added:

```http
GET /api/routes/recent
POST /api/routes/recent
```

Suggested behavior:

- every calculated route should be saved to recent automatically
- backend should return all recent routes for the logged-in user
- recent routes should be tied to the authenticated user, not global

Suggested create request:

```json
{
  "createdAt": "2026-05-16T10:15:00Z",
  "startPoint": { "lat": 52.2297, "lng": 21.0122 },
  "endPoint": { "lat": 52.2100, "lng": 21.0300 },
  "startLabel": "Marszalkowska 12",
  "endLabel": "Krakowskie Przedmiescie 5",
  "preferences": {
    "greenery": 70,
    "noise": 50,
    "airQuality": 60
  },
  "route": [
    { "lat": 52.2297, "lng": 21.0122 },
    { "lat": 52.2250, "lng": 21.0180 },
    { "lat": 52.2100, "lng": 21.0300 }
  ]
}
```

### 6. Saved paths

Right now saved paths also use `localStorage`.

If backend persistence is added:

```http
GET /api/routes/saved
POST /api/routes/saved
PUT /api/routes/saved/{id}
DELETE /api/routes/saved/{id}
```

Suggested save request:

```json
{
  "id": "path-123",
  "name": "Evening Vistula Walk",
  "saved": true
}
```

Suggested full saved route shape:

```json
{
  "id": "path-123",
  "createdAt": "2026-05-16T10:15:00Z",
  "name": "Evening Vistula Walk",
  "saved": true,
  "startPoint": { "lat": 52.2297, "lng": 21.0122 },
  "endPoint": { "lat": 52.2100, "lng": 21.0300 },
  "startLabel": "Marszalkowska 12",
  "endLabel": "Krakowskie Przedmiescie 5",
  "preferences": {
    "greenery": 70,
    "noise": 50,
    "airQuality": 60
  },
  "route": [
    { "lat": 52.2297, "lng": 21.0122 },
    { "lat": 52.2250, "lng": 21.0180 },
    { "lat": 52.2100, "lng": 21.0300 }
  ]
}
```

Suggested behavior:

- only logged-in users can save paths
- saved paths should also stay visible in recent paths
- the backend should return both the route name and `saved: true`

## Frontend files involved

- `src/App.jsx`
  route request, page switching, local storage, recent/saved route state
- `src/components/RoutePanel.jsx`
  sliders, calculate route, save current route button
- `src/components/PathsPage.jsx`
  full recent/saved paths page
- `src/components/SavePathDialog.jsx`
  custom name entry when saving a path
- `src/components/AuthPage.jsx`
  login, sign-up, and account pages
