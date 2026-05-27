function formatPoint(point) {
  if (!point) {
    return 'Not selected';
  }

  return `${point.lat}, ${point.lng}`;
}

function AddressField({
  field,
  label,
  value,
  results,
  isLoading,
  error,
  onInputChange,
  onSearch,
  onSelect,
}) {
  function handleSubmit(event) {
    event.preventDefault();
    onSearch(field);
  }

  return (
    <div className="address-field">
      <form className="address-field__form" onSubmit={handleSubmit}>
        <label className="field">
          <span>{label}</span>
          <div className="address-field__row">
            <input
              type="text"
              value={value}
              placeholder="Type a Warsaw address"
              onChange={(event) => onInputChange(field, event.target.value)}
            />
            <button type="submit" className="button button--ghost address-field__button" disabled={isLoading}>
              {isLoading ? 'Searching...' : 'Find'}
            </button>
          </div>
        </label>
      </form>

      {error ? <p className="status status--error">{error}</p> : null}

      {results.length ? (
        <div className="address-results">
          {results.map((result) => (
            <button
              key={result.id}
              type="button"
              className="address-result"
              onClick={() => onSelect(field, result)}
            >
              <span className="address-result__title">{result.shortLabel}</span>
              <span className="address-result__meta">{result.label}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PointValue({ point, label }) {
  if (!point) {
    return <span>Not selected</span>;
  }

  return (
    <>
      {label ? <span className="point-card__label">{label}</span> : null}
      <strong className="point-card__coords">{formatPoint(point)}</strong>
    </>
  );
}

function RoutePanel({
  startPoint,
  endPoint,
  startLabel,
  endLabel,
  currentUser,
  isLoading,
  hasRoute,
  error,
  addressInputs,
  addressResults,
  addressLookupLoading,
  addressLookupError,
  greeneryPreference,
  noiseAvoidance,
  airQualityPreference,
  onAddressInputChange,
  onAddressSearch,
  onAddressSelect,
  onGreeneryPreferenceChange,
  onNoiseAvoidanceChange,
  onAirQualityPreferenceChange,
  onReset,
  onCalculateRoute,
  onSaveRoute,
}) {
  const canCalculate = Boolean(startPoint && endPoint && !isLoading);
  const canSave = Boolean(currentUser && hasRoute && !isLoading);
  const saveDisabledReason = !currentUser
    ? 'Sign in to save this route.'
    : !hasRoute
      ? 'Calculate a route before saving it.'
      : isLoading
        ? 'Wait for the route calculation to finish.'
        : '';

  return (
    <section className="panel">
      <div className="panel__block">
        <h2>How it works</h2>
        <ol className="steps">
          <li>Type a Warsaw address or click on the map to choose the start point.</li>
          <li>Pick the destination the same way.</li>
          <li>Adjust your route preferences and calculate the route.</li>
        </ol>
      </div>

      <div className="panel__block">
        <h2>Choose locations</h2>
        <div className="address-field-group">
          <AddressField
            field="start"
            label="Start address"
            value={addressInputs.start}
            results={addressResults.start}
            isLoading={addressLookupLoading.start}
            error={addressLookupError.start}
            onInputChange={onAddressInputChange}
            onSearch={onAddressSearch}
            onSelect={onAddressSelect}
          />

          <AddressField
            field="end"
            label="Destination address"
            value={addressInputs.end}
            results={addressResults.end}
            isLoading={addressLookupLoading.end}
            error={addressLookupError.end}
            onInputChange={onAddressInputChange}
            onSearch={onAddressSearch}
            onSelect={onAddressSelect}
          />
        </div>
      </div>

      <div className="panel__block">
        <h2>Selected points</h2>
        <dl className="point-list">
          <div className="point-card point-card--start">
            <dt>Start</dt>
            <dd><PointValue point={startPoint} label={startLabel} /></dd>
          </div>
          <div className="point-card point-card--end">
            <dt>End</dt>
            <dd><PointValue point={endPoint} label={endLabel} /></dd>
          </div>
        </dl>
      </div>

      <div className="panel__block">
        <h2>Route preferences</h2>
        <div className="slider-group">
          <label className="slider-field" htmlFor="greeneryPreference">
            <span className="slider-field__top">
              <span>Prefer greener areas</span>
              <strong>{greeneryPreference}%</strong>
            </span>
            <input
              id="greeneryPreference"
              type="range"
              min="0"
              max="100"
              step="10"
              value={greeneryPreference}
              onChange={(event) => onGreeneryPreferenceChange(Number(event.target.value))}
            />
          </label>

          <label className="slider-field" htmlFor="noiseAvoidance">
            <span className="slider-field__top">
              <span>Prefer lit areas</span>
              <strong>{noiseAvoidance}%</strong>
            </span>
            <input
              id="noiseAvoidance"
              type="range"
              min="0"
              max="100"
              step="10"
              value={noiseAvoidance}
              onChange={(event) => onNoiseAvoidanceChange(Number(event.target.value))}
            />
          </label>

          <label className="slider-field" htmlFor="airQualityPreference">
            <span className="slider-field__top">
              <span>Prefer better air quality</span>
              <strong>{airQualityPreference}%</strong>
            </span>
            <input
              id="airQualityPreference"
              type="range"
              min="0"
              max="100"
              step="10"
              value={airQualityPreference}
              onChange={(event) => onAirQualityPreferenceChange(Number(event.target.value))}
            />
          </label>
        </div>
      </div>

      <div className="panel__actions">
        <button type="button" className="button button--ghost" onClick={onReset}>
          Reset
        </button>
        <button
          type="button"
          className="button button--primary"
          onClick={onCalculateRoute}
          disabled={!canCalculate}
        >
          {isLoading ? 'Calculating...' : 'Calculate route'}
        </button>
        <span
          className="button-tooltip-wrapper"
          data-tooltip={saveDisabledReason}
        >
          <button
            type="button"
            className="button button--secondary"
            onClick={onSaveRoute}
            disabled={!canSave}
          >
            Save route
          </button>
        </span>
      </div>

      {error ? <p className="status status--error">{error}</p> : null}
    </section>
  );
}

export default RoutePanel;
