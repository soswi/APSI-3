import { startTransition, useEffect, useState } from 'react';
import AuthPage from './components/AuthPage';
import MapView from './components/MapView';
import PathsPage from './components/PathsPage';
import RoutePanel from './components/RoutePanel';
import SavePathDialog from './components/SavePathDialog';
import { reverseGeocodeWarsawPoint, searchWarsawAddresses } from './services/geocoding';

const CSRF_ENDPOINT = '/api/auth/csrf';
const LOGIN_ENDPOINT = '/api/auth/login';
const SIGNUP_ENDPOINT = '/api/auth/signup';
const LOGOUT_ENDPOINT = '/api/auth/logout';
const ME_ENDPOINT = '/api/auth/me';
const RECENT_ENDPOINT = '/api/routes/recent';
const SAVED_ENDPOINT = '/api/routes/saved';

function getCookieValue(name) {
  const match = document.cookie.match(new RegExp(`(^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[2]) : null;
}

async function ensureCsrfCookie() {
  await fetch(CSRF_ENDPOINT, { credentials: 'include' });
}

async function apiFetchJson(url, options = {}) {
  const isUnsafeMethod = options.method && options.method !== 'GET';
  const headers = new Headers(options.headers || {});

  if (isUnsafeMethod) {
    await ensureCsrfCookie();
    const csrfToken = getCookieValue('csrftoken');
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken);
    }
  }

  const response = await fetch(url, {
    credentials: 'include',
    ...options,
    headers,
  });

  const payload = await response.json();

  if (!response.ok) {
    const message = payload?.message || payload?.detail || 'Request failed.';
    throw new Error(message);
  }

  return payload;
}

function formatTimestampLabel(timestamp) {
  return new Date(timestamp).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function createPathSnapshot({
  startPoint,
  endPoint,
  startLabel,
  endLabel,
  route,
  distance,
  greeneryPreference,
  noiseAvoidance,
  airQualityPreference,
}) {
  const createdAt = new Date().toISOString();

  return {
    id: `path-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt,
    name: `Route ${formatTimestampLabel(createdAt)}`,
    startPoint,
    endPoint,
    startLabel,
    endLabel,
    route,
    distance,
    saved: false,
    preferences: {
      greenery: greeneryPreference,
      noise: noiseAvoidance,
      airQuality: airQualityPreference,
    },
  };
}

function buildRouteSummary(responsePayload) {
  const distance = Number(responsePayload.distance_m ?? 0);
  const estimatedDuration = Number(responsePayload.estimated_duration_s ?? 0);

  return {
    distance,
    estimatedDuration,
    scores: responsePayload.scores ?? null,
  };
}

function routeWeightsFromPreferences({
  greeneryPreference,
  noiseAvoidance,
  airQualityPreference,
}) {
  return {
    greenery: greeneryPreference / 100,
    noise: noiseAvoidance / 100,
    air_quality: airQualityPreference / 100,
  };
}

async function readJsonResponse(response) {
  const responseText = await response.text();

  if (!responseText) {
    return {};
  }

  try {
    return JSON.parse(responseText);
  } catch {
    if (!response.ok) {
      return {
        message: 'The routing backend did not return JSON. Make sure the Django server is running.',
      };
    }

    throw new Error('The routing backend returned an invalid response.');
  }
}

function App() {
  const [startPoint, setStartPoint] = useState(null);
  const [endPoint, setEndPoint] = useState(null);
  const [startLabel, setStartLabel] = useState('');
  const [endLabel, setEndLabel] = useState('');
  const [route, setRoute] = useState(null);
  const [routeSummary, setRouteSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [greeneryPreference, setGreeneryPreference] = useState(70);
  const [noiseAvoidance, setNoiseAvoidance] = useState(55);
  const [airQualityPreference, setAirQualityPreference] = useState(60);
  const [savedPaths, setSavedPaths] = useState([]);
  const [recentPaths, setRecentPaths] = useState([]);
  const [activePage, setActivePage] = useState('planner');
  const [currentUser, setCurrentUser] = useState(null);
  const [activePathId, setActivePathId] = useState(null);
  const [pathToSave, setPathToSave] = useState(null);
  const [addressInputs, setAddressInputs] = useState({ start: '', end: '' });
  const [addressResults, setAddressResults] = useState({ start: [], end: [] });
  const [addressLookupLoading, setAddressLookupLoading] = useState({ start: false, end: false });
  const [addressLookupError, setAddressLookupError] = useState({ start: null, end: null });

  useEffect(() => {
    if (!startPoint || startLabel !== 'Pinned on map') {
      return undefined;
    }

    let ignore = false;

    async function hydrateStartLabel() {
      try {
        const result = await reverseGeocodeWarsawPoint(startPoint);

        if (ignore) {
          return;
        }

        setStartLabel(result.shortLabel);
        setAddressInputs((currentState) => ({ ...currentState, start: result.label }));
      } catch {
        // Keep the fallback pin label when reverse geocoding is unavailable.
      }
    }

    void hydrateStartLabel();

    return () => {
      ignore = true;
    };
  }, [startPoint, startLabel]);

  useEffect(() => {
    if (!endPoint || endLabel !== 'Pinned on map') {
      return undefined;
    }

    let ignore = false;

    async function hydrateEndLabel() {
      try {
        const result = await reverseGeocodeWarsawPoint(endPoint);

        if (ignore) {
          return;
        }

        setEndLabel(result.shortLabel);
        setAddressInputs((currentState) => ({ ...currentState, end: result.label }));
      } catch {
        // Keep the fallback pin label when reverse geocoding is unavailable.
      }
    }

    void hydrateEndLabel();

    return () => {
      ignore = true;
    };
  }, [endPoint, endLabel]);

  useEffect(() => {
    let ignore = false;

    async function hydrateSession() {
      try {
        const payload = await apiFetchJson(ME_ENDPOINT);
        if (ignore) {
          return;
        }
        setCurrentUser(payload.user);

        const [recent, saved] = await Promise.all([
          apiFetchJson(RECENT_ENDPOINT),
          apiFetchJson(SAVED_ENDPOINT),
        ]);

        if (ignore) {
          return;
        }

        setRecentPaths(recent.routes || []);
        setSavedPaths(saved.routes || []);
      } catch {
        if (!ignore) {
          setCurrentUser(null);
          setRecentPaths([]);
          setSavedPaths([]);
        }
      }
    }

    void hydrateSession();

    return () => {
      ignore = true;
    };
  }, []);

  function clearAddressLookup(field) {
    setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
    setAddressLookupError((currentState) => ({ ...currentState, [field]: null }));
  }

  async function refreshRouteHistory() {
    const [recent, saved] = await Promise.all([
      apiFetchJson(RECENT_ENDPOINT),
      apiFetchJson(SAVED_ENDPOINT),
    ]);
    setRecentPaths(recent.routes || []);
    setSavedPaths(saved.routes || []);
  }

  function assignPoint(field, point, label) {
    if (field === 'start') {
      setStartPoint(point);
      setStartLabel(label);
    } else {
      setEndPoint(point);
      setEndLabel(label);
    }

    setRoute(null);
    setRouteSummary(null);
    setActivePathId(null);
    setError(null);
  }

  function handleMapClick(latlng) {
    const nextPoint = {
      lat: Number(latlng.lat.toFixed(6)),
      lng: Number(latlng.lng.toFixed(6)),
    };

    if (!startPoint) {
      assignPoint('start', nextPoint, 'Pinned on map');
      setAddressInputs((currentState) => ({ ...currentState, start: '' }));
      clearAddressLookup('start');
      return;
    }

    if (!endPoint) {
      assignPoint('end', nextPoint, 'Pinned on map');
      setAddressInputs((currentState) => ({ ...currentState, end: '' }));
      clearAddressLookup('end');
      return;
    }

    setError('Two points are already selected. Reset the selection to choose new ones.');
  }

  function handleAddressInputChange(field, value) {
    setAddressInputs((currentState) => ({ ...currentState, [field]: value }));
    setAddressLookupError((currentState) => ({ ...currentState, [field]: null }));

    if (!value.trim()) {
      setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
    }
  }

  async function handleAddressSearch(field) {
    const query = addressInputs[field].trim();

    if (!query) {
      setAddressLookupError((currentState) => ({
        ...currentState,
        [field]: 'Type a Warsaw address first.',
      }));
      setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
      return;
    }

    setAddressLookupLoading((currentState) => ({ ...currentState, [field]: true }));
    setAddressLookupError((currentState) => ({ ...currentState, [field]: null }));

    try {
      const results = await searchWarsawAddresses(query);

      if (!results.length) {
        setAddressLookupError((currentState) => ({
          ...currentState,
          [field]: 'No matching Warsaw address was found.',
        }));
        setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
        return;
      }

      setAddressResults((currentState) => ({ ...currentState, [field]: results }));
    } catch (lookupError) {
      setAddressLookupError((currentState) => ({
        ...currentState,
        [field]: lookupError instanceof Error
          ? lookupError.message
          : 'Unable to search for that address.',
      }));
      setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
    } finally {
      setAddressLookupLoading((currentState) => ({ ...currentState, [field]: false }));
    }
  }

  function handleAddressSelect(field, result) {
    const nextPoint = {
      lat: Number(result.lat.toFixed(6)),
      lng: Number(result.lng.toFixed(6)),
    };

    assignPoint(field, nextPoint, result.shortLabel);
    setAddressInputs((currentState) => ({ ...currentState, [field]: result.label }));
    setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
    setAddressLookupError((currentState) => ({ ...currentState, [field]: null }));
  }

  function resetSelection() {
    setStartPoint(null);
    setEndPoint(null);
    setStartLabel('');
    setEndLabel('');
    setRoute(null);
    setRouteSummary(null);
    setError(null);
    setIsLoading(false);
    setActivePathId(null);
    setAddressInputs({ start: '', end: '' });
    setAddressResults({ start: [], end: [] });
    setAddressLookupLoading({ start: false, end: false });
    setAddressLookupError({ start: null, end: null });
  }

  function openPathsPage() {
    setActivePage('paths');
  }

  function openAuthPage(mode) {
    setActivePage(mode);
  }

  function closeOverlayPage() {
    setActivePage('planner');
  }

  function handleUseStoredPath(path) {
    setStartPoint(path.startPoint);
    setEndPoint(path.endPoint);
    setStartLabel(path.startLabel ?? '');
    setEndLabel(path.endLabel ?? '');
    setRoute(path.route ?? [path.startPoint, path.endPoint]);
    setRouteSummary({
      distance: Number(path.distance ?? 0),
      estimatedDuration: Math.round(Number(path.distance ?? 0) / 1.25),
      scores: null,
    });
    setGreeneryPreference(path.preferences?.greenery ?? 70);
    setNoiseAvoidance(path.preferences?.noise ?? 55);
    setAirQualityPreference(path.preferences?.airQuality ?? 60);
    setAddressInputs({
      start: path.startLabel ?? '',
      end: path.endLabel ?? '',
    });
    setAddressResults({ start: [], end: [] });
    setAddressLookupError({ start: null, end: null });
    setActivePathId(path.id);
    setError(null);
    setActivePage('planner');
  }

  function handleRequestSavePath(path) {
    setPathToSave(path);
  }

  function handleSaveCurrentRoute() {
    if (!currentUser) {
      setError('Sign in to save routes to your account.');
      return;
    }

    const activePath = recentPaths.find((path) => path.id === activePathId);

    if (activePath) {
      setPathToSave(activePath);
      return;
    }

    if (!startPoint || !endPoint || !route) {
      setError('Calculate a route before saving it.');
      return;
    }

    const fallbackSnapshot = createPathSnapshot({
      startPoint,
      endPoint,
      startLabel,
      endLabel,
      route,
      distance: 0,
      greeneryPreference,
      noiseAvoidance,
      airQualityPreference,
    });

    setRecentPaths((currentPaths) => [fallbackSnapshot, ...currentPaths]);
    setActivePathId(fallbackSnapshot.id);
    setPathToSave(fallbackSnapshot);
    setError(null);
  }

  async function handleConfirmSavePath(pathName) {
    if (!pathToSave) {
      return;
    }

    if (!currentUser) {
      setError('Sign in to save routes to your account.');
      return;
    }

    try {
      const response = await apiFetchJson(`${SAVED_ENDPOINT}/${pathToSave.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: pathName,
          saved: true,
        }),
      });

      const savedSnapshot = response.route;

      setRecentPaths((currentPaths) => currentPaths.map((path) => (
        path.id === savedSnapshot.id
          ? { ...path, name: savedSnapshot.name, saved: true }
          : path
      )));

      setSavedPaths((currentPaths) => {
        const filteredPaths = currentPaths.filter((path) => path.id !== savedSnapshot.id);
        return [savedSnapshot, ...filteredPaths];
      });

      setPathToSave(null);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save this route.');
    }
  }

  function handleCancelSavePath() {
    setPathToSave(null);
  }

  async function handleRemoveSavedPath(pathId) {
    if (!currentUser) {
      return;
    }

    try {
      const response = await apiFetchJson(`${SAVED_ENDPOINT}/${pathId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ saved: false }),
      });

      const updated = response.route;

      setSavedPaths((currentPaths) => currentPaths.filter((path) => path.id !== pathId));
      setRecentPaths((currentPaths) => currentPaths.map((path) => (
        path.id === pathId
          ? { ...path, saved: false, name: updated.name }
          : path
      )));
    } catch (removeError) {
      setError(removeError instanceof Error ? removeError.message : 'Unable to update this route.');
    }
  }

  async function handleAuthSubmit(formData) {
    const isSignup = activePage === 'signup';
    const endpoint = isSignup ? SIGNUP_ENDPOINT : LOGIN_ENDPOINT;
    const payload = isSignup
      ? {
        username: formData.name?.trim() || formData.email.split('@')[0],
        email: formData.email,
        password: formData.password,
      }
      : {
        email: formData.email,
        password: formData.password,
      };

    try {
      const response = await apiFetchJson(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      setCurrentUser(response.user);
      await refreshRouteHistory();
      setActivePage('planner');
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : 'Authentication failed.');
    }
  }

  async function handleLogout() {
    try {
      await apiFetchJson(LOGOUT_ENDPOINT, { method: 'POST' });
    } catch {
      // Ignore logout failures to avoid locking users in the UI.
    }

    setCurrentUser(null);
    setRecentPaths([]);
    setSavedPaths([]);
    setActivePage('planner');
  }

  async function calculateRoute() {
    if (!startPoint || !endPoint) {
      setError('Select both a start point and an end point first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const responsePayload = await apiFetchJson('/api/routes/walking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start: startPoint,
          end: endPoint,
          weights: routeWeightsFromPreferences({
            greeneryPreference,
            noiseAvoidance,
            airQualityPreference,
          }),
        }),
      });

      const computedRoute = Array.isArray(responsePayload.route) ? responsePayload.route : null;

      if (!computedRoute?.length) {
        throw new Error('The backend returned no route.');
      }

      const snapshot = createPathSnapshot({
        startPoint,
        endPoint,
        startLabel,
        endLabel,
        route: computedRoute,
        distance: responsePayload.distance_m ?? 0,
        greeneryPreference,
        noiseAvoidance,
        airQualityPreference,
      });

      startTransition(() => {
        setRoute(computedRoute);
        setRouteSummary(buildRouteSummary(responsePayload));
      });

      if (currentUser) {
        try {
          const recentResponse = await apiFetchJson(RECENT_ENDPOINT, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              createdAt: snapshot.createdAt,
              name: snapshot.name,
              startPoint: snapshot.startPoint,
              endPoint: snapshot.endPoint,
              startLabel: snapshot.startLabel,
              endLabel: snapshot.endLabel,
              preferences: snapshot.preferences,
              route: snapshot.route,
              distance: snapshot.distance,
              saved: false,
            }),
          });

          const recentRoute = recentResponse.route;
          setRecentPaths((currentPaths) => [recentRoute, ...currentPaths]);
          setActivePathId(recentRoute.id);
        } catch (historyError) {
          setRecentPaths((currentPaths) => [snapshot, ...currentPaths]);
          setActivePathId(snapshot.id);
        }
      } else {
        setRecentPaths((currentPaths) => [snapshot, ...currentPaths]);
        setActivePathId(snapshot.id);
      }
    } catch (routeError) {
      setError(routeError instanceof Error ? routeError.message : 'Unable to calculate the route.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__header">
          <div className="sidebar__toolbar">
            <button
              type="button"
              className="icon-button"
              onClick={openPathsPage}
              aria-label="Open saved and recent paths page"
            >
              <span className="icon-lines" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
            </button>

            <button
              type="button"
              className="icon-button icon-button--user"
              onClick={() => openAuthPage(currentUser ? 'account' : 'login')}
              aria-label={currentUser ? 'Open account page' : 'Open login page'}
            >
              {currentUser ? (
                <span className="user-badge" aria-hidden="true">
                  {currentUser.name.charAt(0).toUpperCase()}
                </span>
              ) : (
                <span className="user-icon" aria-hidden="true">
                  <span className="user-icon__head" />
                  <span className="user-icon__body" />
                </span>
              )}
            </button>
          </div>

          <h1>Warsaw Walking Route Planner</h1>
          <p className="lead">
            Choose your start and destination, then tailor the route toward greener streets and
            lower noise exposure and better air quality across Warsaw.
          </p>
          {currentUser ? (
            <p className="session-label">Signed in as {currentUser.name}</p>
          ) : null}
        </div>

        <RoutePanel
          startPoint={startPoint}
          endPoint={endPoint}
          startLabel={startLabel}
          endLabel={endLabel}
          currentUser={currentUser}
          isLoading={isLoading}
          hasRoute={Boolean(route)}
          routeSummary={routeSummary}
          error={error}
          addressInputs={addressInputs}
          addressResults={addressResults}
          addressLookupLoading={addressLookupLoading}
          addressLookupError={addressLookupError}
          greeneryPreference={greeneryPreference}
          noiseAvoidance={noiseAvoidance}
          airQualityPreference={airQualityPreference}
          onAddressInputChange={handleAddressInputChange}
          onAddressSearch={handleAddressSearch}
          onAddressSelect={handleAddressSelect}
          onGreeneryPreferenceChange={setGreeneryPreference}
          onNoiseAvoidanceChange={setNoiseAvoidance}
          onAirQualityPreferenceChange={setAirQualityPreference}
          onReset={resetSelection}
          onCalculateRoute={calculateRoute}
          onSaveRoute={handleSaveCurrentRoute}
        />
      </aside>

      <main className="map-stage">
        <MapView
          startPoint={startPoint}
          endPoint={endPoint}
          route={route}
          onMapClick={handleMapClick}
        />
      </main>

      {activePage === 'paths' ? (
        <PathsPage
          recentPaths={recentPaths}
          savedPaths={savedPaths}
          currentUser={currentUser}
          onClose={closeOverlayPage}
          onUsePath={handleUseStoredPath}
          onRequestSavePath={handleRequestSavePath}
          onRemoveSavedPath={handleRemoveSavedPath}
        />
      ) : null}

      {activePage === 'login' || activePage === 'signup' || activePage === 'account' ? (
        <AuthPage
          mode={activePage}
          currentUser={currentUser}
          onClose={closeOverlayPage}
          onModeChange={setActivePage}
          onSubmit={handleAuthSubmit}
          onLogout={handleLogout}
        />
      ) : null}

      <SavePathDialog
        path={pathToSave}
        onCancel={handleCancelSavePath}
        onSave={handleConfirmSavePath}
      />
    </div>
  );
}

export default App;
