import { useEffect, useState } from 'react';

function SavePathDialog({ path, onCancel, onSave }) {
  const [pathName, setPathName] = useState('');

  useEffect(() => {
    if (path) {
      setPathName(path.name);
    }
  }, [path]);

  if (!path) {
    return null;
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSave(pathName.trim() || path.name);
  }

  return (
    <div className="overlay-dialog" role="presentation" onClick={onCancel}>
      <section
        className="dialog-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="save-path-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="dialog-card__header">
          <div>
            <p className="page-card__eyebrow">Save route</p>
            <h2 id="save-path-title">Choose a name for this path</h2>
          </div>
          <button type="button" className="icon-button icon-button--small" onClick={onCancel} aria-label="Close dialog">
            x
          </button>
        </div>

        <form className="form-stack dialog-card__body" onSubmit={handleSubmit}>
          <label className="field">
            <span>Path name</span>
            <input
              type="text"
              value={pathName}
              onChange={(event) => setPathName(event.target.value)}
              required
            />
          </label>

          <div className="page-card__actions">
            <button type="button" className="button button--ghost" onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" className="button button--primary">
              Save path
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default SavePathDialog;
