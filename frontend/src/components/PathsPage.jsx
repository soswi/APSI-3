function formatPoint(point, label) {
  const coordinates = `${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`;
  return label ? `${label} (${coordinates})` : coordinates;
}

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function PathCard({ path, savedView, onUsePath, onRequestSavePath, onRemoveSavedPath }) {
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
          G {path.preferences?.greenery ?? 70}% | L {path.preferences?.noise ?? 55}% | AQ {path.preferences?.airQuality ?? 60}% 
        </span>
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
          <button type="button" className="button button--danger" onClick={() => onRemoveSavedPath(path.id)}>
            Remove
          </button>
        ) : path.saved ? (
          <button type="button" className="button button--secondary" disabled>
            Saved &hearts;
          </button>
        ) : (
          <button type="button" className="button button--primary" onClick={() => onRequestSavePath(path)}>
            Save with name
          </button>
        )}
      </div>
    </article>
  );
}

function PathsPage({ recentPaths, savedPaths, onClose, onUsePath, onRequestSavePath, onRemoveSavedPath }) {
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
                    onUsePath={onUsePath}
                    onRequestSavePath={onRequestSavePath}
                    onRemoveSavedPath={onRemoveSavedPath}
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
