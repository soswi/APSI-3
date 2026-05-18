import { startTransition, useEffect, useState } from 'react';
import AuthPage from './components/AuthPage';
import MapView from './components/MapView';
import PathsPage from './components/PathsPage';
import RoutePanel from './components/RoutePanel';
import SavePathDialog from './components/SavePathDialog';
import { reverseGeocodeWarsawPoint, searchWarsawAddresses } from './services/geocoding';

const SAVED_PATHS_KEY = 'apsi.savedPaths';
const RECENT_PATHS_KEY = 'apsi.recentPaths';
const CURRENT_USER_KEY = 'apsi.currentUser';

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
    saved: false,
    preferences: {
      greenery: greeneryPreference,
      noise: noiseAvoidance,
      airQuality: airQualityPreference,
    },
  };
}

function App() {
  const [startPoint, setStartPoint] = useState(null);
  const [endPoint, setEndPoint] = useState(null);
  const [startLabel, setStartLabel] = useState('');
  const [endLabel, setEndLabel] = useState('');
  const [route, setRoute] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [greeneryPreference, setGreeneryPreference] = useState(70);
  const [noiseAvoidance, setNoiseAvoidance] = useState(55);
  const [airQualityPreference, setAirQualityPreference] = useState(60);
  const [savedPaths, setSavedPaths] = useState([]);
  const [recentPaths, setRecentPaths] = useState([]);
  const [activePage, setActivePage] = useState('planner');
  const [currentUser, setCurrentUser] = useState(null);
  const [isStorageReady, setIsStorageReady] = useState(false);
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
    try {
      const storedSavedPaths = window.localStorage.getItem(SAVED_PATHS_KEY);
      const storedRecentPaths = window.localStorage.getItem(RECENT_PATHS_KEY);
      const storedCurrentUser = window.localStorage.getItem(CURRENT_USER_KEY);

      if (storedSavedPaths) {
        setSavedPaths(JSON.parse(storedSavedPaths));
      }

      if (storedRecentPaths) {
        setRecentPaths(JSON.parse(storedRecentPaths));
      }

      if (storedCurrentUser) {
        setCurrentUser(JSON.parse(storedCurrentUser));
      }
    } catch (storageError) {
      console.error('Unable to restore frontend data from local storage.', storageError);
    }

    setIsStorageReady(true);
  }, []);

  useEffect(() => {
    if (!isStorageReady) {
      return;
    }

    window.localStorage.setItem(SAVED_PATHS_KEY, JSON.stringify(savedPaths));
  }, [isStorageReady, savedPaths]);

  useEffect(() => {
    if (!isStorageReady) {
      return;
    }

    window.localStorage.setItem(RECENT_PATHS_KEY, JSON.stringify(recentPaths));
  }, [isStorageReady, recentPaths]);

  useEffect(() => {
    if (!isStorageReady) {
      return;
    }

    if (currentUser) {
      window.localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(currentUser));
      return;
    }

    window.localStorage.removeItem(CURRENT_USER_KEY);
  }, [currentUser, isStorageReady]);

  function clearAddressLookup(field) {
    setAddressResults((currentState) => ({ ...currentState, [field]: [] }));
    setAddressLookupError((currentState) => ({ ...currentState, [field]: null }));
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

  function rememberRecentPath(snapshot) {
    setRecentPaths((currentPaths) => [snapshot, ...currentPaths]);
  }

  function handleUseStoredPath(path) {
    setStartPoint(path.startPoint);
    setEndPoint(path.endPoint);
    setStartLabel(path.startLabel ?? '');
    setEndLabel(path.endLabel ?? '');
    setRoute(path.route ?? [path.startPoint, path.endPoint]);
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
      greeneryPreference,
      noiseAvoidance,
      airQualityPreference,
    });

    rememberRecentPath(fallbackSnapshot);
    setActivePathId(fallbackSnapshot.id);
    setPathToSave(fallbackSnapshot);
    setError(null);
  }

  function handleConfirmSavePath(pathName) {
    if (!pathToSave) {
      return;
    }

    const savedSnapshot = {
      ...pathToSave,
      name: pathName,
      saved: true,
    };

    setRecentPaths((currentPaths) => currentPaths.map((path) => (
      path.id === savedSnapshot.id
        ? { ...path, name: pathName, saved: true }
        : path
    )));

    setSavedPaths((currentPaths) => {
      const filteredPaths = currentPaths.filter((path) => path.id !== savedSnapshot.id);
      return [savedSnapshot, ...filteredPaths];
    });

    setPathToSave(null);
  }

  function handleCancelSavePath() {
    setPathToSave(null);
  }

  function handleRemoveSavedPath(pathId) {
    setSavedPaths((currentPaths) => currentPaths.filter((path) => path.id !== pathId));
    setRecentPaths((currentPaths) => currentPaths.map((path) => (
      path.id === pathId
        ? { ...path, saved: false }
        : path
    )));
  }

  function handleAuthSubmit(formData) {
    const displayName = formData.name?.trim()
      || formData.email.split('@')[0]
      || 'Walker';

    setCurrentUser({
      name: displayName,
      email: formData.email,
    });
    setActivePage('planner');
  }

  function handleLogout() {
    setCurrentUser(null);
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
      const response = await fetch('/api/routes/walking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start: startPoint,
          end: endPoint,
        }),
      });

      const responsePayload = await response.json();

      if (!response.ok) {
        throw new Error(responsePayload.message || 'Unable to calculate the route.');
      }

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
        greeneryPreference,
        noiseAvoidance,
        airQualityPreference,
      });

      startTransition(() => {
        setRoute(computedRoute);
      });

      rememberRecentPath(snapshot);
      setActivePathId(snapshot.id);
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
