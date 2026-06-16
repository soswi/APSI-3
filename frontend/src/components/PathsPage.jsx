function formatPoint(point, label) {
  const coordinates = `${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`;
  return label ? `${label} (${coordinates})` : coordinates;
}

function formatDistance(distance) {
  const value = Number(distance ?? 0);
  if (!Number.isFinite(value) || value <= 0) {
    return '0 km';
  }
  return `${(value / 1000).toFixed(2)} km`;
}

function formatDuration(seconds) {
  const value = Number(seconds ?? 0);
  if (!Number.isFinite(value) || value <= 0) {
    return '0 min';
  }

  const totalMinutes = Math.max(1, Math.round(value / 60));

  if (totalMinutes < 60) {
    return `${totalMinutes} min`;
  }

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return minutes ? `${hours} h ${minutes} min` : `${hours} h`;
}

function estimatedDurationFromDistance(distance) {
  return Number(distance ?? 0) / 1.25;
}

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function collectRouteStats(recentPaths, savedPaths) {
  const uniquePaths = new Map();

  [...recentPaths, ...savedPaths].forEach((path) => {
    uniquePaths.set(path.id, path);
  });

  const routes = Array.from(uniquePaths.values());

  if (!routes.length) {
    return null;
  }

  const distances = routes.map((path) => Number(path.distance ?? 0)).filter((distance) => Number.isFinite(distance));
  if (!distances.length) {
    return null;
  }
  const averageDistance = distances.reduce((sum, value) => sum + value, 0) / distances.length;
  const greeneryAverage = routes.reduce((sum, path) => sum + Number(path.preferences?.greenery ?? 0), 0) / routes.length;
  const noiseAverage = routes.reduce((sum, path) => sum + Number(path.preferences?.noise ?? 0), 0) / routes.length;
  const airQualityAverage = routes.reduce((sum, path) => sum + Number(path.preferences?.airQuality ?? 0), 0) / routes.length;

  const preferenceEntries = [
    ['greener areas', greeneryAverage],
    ['lighter areas', noiseAverage],
    ['better air quality', airQualityAverage],
  ];
  preferenceEntries.sort((left, right) => right[1] - left[1]);

  return {
    totalRoutes: routes.length,
    averageDistance,
    shortestDistance: Math.min(...distances),
    longestDistance: Math.max(...distances),
    averageDuration: estimatedDurationFromDistance(averageDistance),
    preferences: {
      greenery: Math.round(greeneryAverage),
      noise: Math.round(noiseAverage),
      airQuality: Math.round(airQualityAverage),
      favoriteLabel: preferenceEntries[0][0],
    },
  };
}

function PathCard({ path, savedView, currentUser, onUsePath, onRequestSavePath, onRemoveSavedPath, onRequestSharePath }) {
  const durationSeconds = estimatedDurationFromDistance(path.distance);
  const canSave = Boolean(currentUser);
  const saveDisabledReason = canSave ? '' : 'Sign in to save routes to your account.';

  return (
    <article className="path-card">
      <div className="path-card__top">
        <div>
          <div className="path-card__title-row">
            <h3>{path.name}</h3>
            {path.saved ? <span className="heart-chip" aria-label="Saved route">&hearts;</span> : null}
          </div>
          <p className="path-card__meta">{savedView ? 'Saved route' : 'Recent route'} - {formatDate(path.createdAt)}</p>
        </div>
        <span className="path-chip">
          G {path.preferences?.greenery ?? 70}% | Q {path.preferences?.noise ?? 55}% | AQ {path.preferences?.airQuality ?? 60}%
        </span>
      </div>

      <div className="path-card__stats">
        <div className="path-stat">
          <span>Length</span>
          <strong>{formatDistance(path.distance)}</strong>
        </div>
        <div className="path-stat">
          <span>Estimated time</span>
          <strong>{formatDuration(durationSeconds)}</strong>
        </div>
      </div>

      <dl className="path-card__points">
        <div>
          <dt>Start</dt>
          <dd>{formatPoint(path.startPoint, path.startLabel)}</dd>
        </div>
        <div>
          <dt>End</dt>
          <dd>{formatPoint(path.endPoint, path.endLabel)}</dd>
        </div>
      </dl>

      <div className="path-card__actions">
        <button type="button" className="button button--ghost" onClick={() => onUsePath(path)}>
          Open
        </button>
        {savedView ? (
          <>
            <button type="button" className="button button--ghost" onClick={() => onRequestSharePath(path)}>
              Share
            </button>
            <button type="button" className="button button--danger" onClick={() => onRemoveSavedPath(path.id)}>
              Remove
            </button>
          </>
        ) : path.saved ? (
          <button type="button" className="button button--secondary" disabled>
            Saved &hearts;
          </button>
        ) : (
          <span
            className="button-tooltip-wrapper"
            data-tooltip={saveDisabledReason}
          >
            <button
              type="button"
              className="button button--primary"
              onClick={() => onRequestSavePath(path)}
              disabled={!canSave}
            >
              Save
            </button>
          </span>
        )}
      </div>
    </article>
  );
}

function InboxCard({ share, onAccept, onReject, onBlock }) {
  const { route, sender, id } = share;
  const durationSeconds = estimatedDurationFromDistance(route.distance);

  return (
    <article className="path-card share-card">
      <div className="path-card__top">
        <div>
          <div className="path-card__title-row">
            <h3>{route.name}</h3>
          </div>
          <p className="path-card__meta">Shared by: {sender.name} ({sender.email}) - {formatDate(share.createdAt)}</p>
        </div>
        <span className="path-chip">
          G {route.preferences?.greenery ?? 70}% | Q {route.preferences?.noise ?? 55}% | AQ {route.preferences?.airQuality ?? 60}%
        </span>
      </div>
      
      <div className="path-card__stats">
        <div className="path-stat">
          <span>Length</span>
          <strong>{formatDistance(route.distance)}</strong>
        </div>
        <div className="path-stat">
          <span>Estimated time</span>
          <strong>{formatDuration(durationSeconds)}</strong>
        </div>
      </div>
      
      <dl className="path-card__points">
        <div>
          <dt>Start</dt>
          <dd>{formatPoint(route.startPoint, route.startLabel)}</dd>
        </div>
        <div>
          <dt>End</dt>
          <dd>{formatPoint(route.endPoint, route.endLabel)}</dd>
        </div>
      </dl>
      
      <div className="path-card__actions" style={{gap: '0.5rem', flexWrap: 'wrap'}}>
        <button type="button" className="button button--primary" onClick={() => onAccept(id)}>Accept</button>
        <button type="button" className="button button--ghost" onClick={() => onReject(id)}>Reject</button>
        <button type="button" className="button button--danger" style={{marginLeft: 'auto'}} onClick={() => onBlock(sender.id)}>Block Sender</button>
      </div>
    </article>
  );
}

function PathsPage({ recentPaths, savedPaths, pendingShares, currentUser, onClose, onUsePath, onRequestSavePath, onRemoveSavedPath, onRequestSharePath, onAcceptShare, onRejectShare, onBlockSender }) {
  const routeStats = collectRouteStats(recentPaths, savedPaths);

  return (
    <div className="overlay-page" role="presentation">
      <section className="page-card paths-page" role="dialog" aria-modal="true" aria-labelledby="paths-page-title">
        <div className="page-card__header">
          <div>
            <p className="page-card__eyebrow">Routes</p>
            <h2 id="paths-page-title">Recent and saved paths</h2>
          </div>
          <button type="button" className="icon-button icon-button--small" onClick={onClose} aria-label="Close page">
            x
          </button>
        </div>

        <div className="page-card__body page-card__body--scrollable">
        
          {currentUser && pendingShares && pendingShares.length > 0 && (
            <section className="page-section">
              <div className="page-section__header">
                <h3>Shared with you</h3>
                <span>{pendingShares.length}</span>
              </div>
              <div className="path-list">
                {pendingShares.map((share) => (
                  <InboxCard
                    key={share.id}
                    share={share}
                    onAccept={onAcceptShare}
                    onReject={onRejectShare}
                    onBlock={onBlockSender}
                  />
                ))}
              </div>
            </section>
          )}

          <section className="page-section">
            <div className="page-section__header">
              <h3>Route statistics</h3>
              <span>{routeStats?.totalRoutes ?? 0}</span>
            </div>
            {routeStats ? (
              <div className="stats-card">
                <div className="stats-card__grid">
                  <div className="stats-card__item">
                    <span>Average route</span>
                    <strong>{formatDistance(routeStats.averageDistance)}</strong>
                    <small>{formatDuration(routeStats.averageDuration)}</small>
                  </div>
                  <div className="stats-card__item">
                    <span>Shortest route</span>
                    <strong>{formatDistance(routeStats.shortestDistance)}</strong>
                  </div>
                  <div className="stats-card__item">
                    <span>Longest route</span>
                    <strong>{formatDistance(routeStats.longestDistance)}</strong>
                  </div>
                </div>
                <div className="stats-card__preferences">
                  <p>You usually prefer <strong>{routeStats.preferences.favoriteLabel}</strong>.</p>
                  <span>Greenery {routeStats.preferences.greenery}%</span>
                  <span>Light {routeStats.preferences.noise}%</span>
                  <span>Air quality {routeStats.preferences.airQuality}%</span>
                </div>
              </div>
            ) : (
              <p className="empty-state">Calculate a few routes and your summary stats will appear here.</p>
            )}
          </section>

          <section className="page-section">
            <div className="page-section__header">
              <h3>Saved paths</h3>
              <span>{savedPaths.length}</span>
            </div>
            {savedPaths.length ? (
              <div className="path-list">
                {savedPaths.map((path) => (
                  <PathCard
                    key={path.id}
                    path={path}
                    savedView
                    currentUser={currentUser}
                    onUsePath={onUsePath}
                    onRequestSavePath={onRequestSavePath}
                    onRemoveSavedPath={onRemoveSavedPath}
                    onRequestSharePath={onRequestSharePath}
                  />
                ))}
              </div>
            ) : (
              <p className="empty-state">Saved paths with custom names will appear here.</p>
            )}
          </section>

          <section className="page-section">
            <div className="page-section__header">
              <h3>Recent paths</h3>
              <span>{recentPaths.length}</span>
            </div>
            {recentPaths.length ? (
              <div className="path-list">
                {recentPaths.map((path) => (
                  <PathCard
                    key={path.id}
                    path={path}
                    savedView={false}
                    currentUser={currentUser}
                    onUsePath={onUsePath}
                    onRequestSavePath={onRequestSavePath}
                    onRemoveSavedPath={onRemoveSavedPath}
                  />
                ))}
              </div>
            ) : (
              <p className="empty-state">Every calculated route will be added to this recent list.</p>
            )}
          </section>
        </div>
      </section>
    </div>
  );
}

export default PathsPage;
