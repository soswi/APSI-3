import { useState } from 'react';

function SharePathDialog({ path, onCancel, onShare }) {
  const [recipient, setRecipient] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');

    const target = recipient.trim();
    if (!target) {
      setError('Please enter a username or email.');
      return;
    }

    setIsLoading(true);
    try {
      await onShare(path.id, target);
    } catch (err) {
      setError(err.message || 'Failed to share the route. Please check the recipient and try again.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="overlay-page overlay-page--centered" role="presentation">
      <section className="dialog-card" role="dialog" aria-modal="true" aria-labelledby="share-dialog-title">
        <div className="dialog-card__header">
          <h2 id="share-dialog-title">Share Route: {path.name}</h2>
          <button type="button" className="icon-button icon-button--small" onClick={onCancel} aria-label="Close dialog">
            x
          </button>
        </div>

        <form className="dialog-card__form" onSubmit={handleSubmit}>
          {error && <p className="status status--error">{error}</p>}
          <div className="field">
            <label htmlFor="share-recipient">Email or Username</label>
            <input
              id="share-recipient"
              type="text"
              name="recipient"
              placeholder="Friend's email or username"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>

          <div className="dialog-card__actions">
            <button type="button" className="button button--ghost" onClick={onCancel} disabled={isLoading}>
              Cancel
            </button>
            <button type="submit" className="button button--primary" disabled={isLoading}>
              {isLoading ? 'Sharing...' : 'Share'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default SharePathDialog;
