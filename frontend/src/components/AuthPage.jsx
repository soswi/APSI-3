import { useState } from 'react';

function AuthPage({ mode, currentUser, notice, onClose, onModeChange, onSubmit, onLogout }) {
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
  });
  const [signUpForm, setSignUpForm] = useState({
    name: '',
    email: '',
    password: '',
  });

  function handleLoginSubmit(event) {
    event.preventDefault();
    onSubmit(loginForm);
  }

  function handleSignUpSubmit(event) {
    event.preventDefault();
    onSubmit(signUpForm);
  }

  return (
    <div className="overlay-page" role="presentation">
      <section className="page-card auth-page" role="dialog" aria-modal="true" aria-labelledby="auth-page-title">
        <div className="page-card__header">
          <div>
            <p className="page-card__eyebrow">Account</p>
            <h2 id="auth-page-title">
              {mode === 'account' ? 'Your account' : mode === 'signup' ? 'Create account' : 'Login'}
            </h2>
          </div>
          <button type="button" className="icon-button icon-button--small" onClick={onClose} aria-label="Close page">
            x
          </button>
        </div>

        {mode === 'account' && currentUser ? (
          <div className="page-card__body">
            <div className="account-card">
              <p className="account-card__name">{currentUser.name}</p>
              <p className="account-card__email">{currentUser.email}</p>
            </div>
            <div className="page-card__actions">
              <button type="button" className="button button--ghost" onClick={onClose}>
                Back to planner
              </button>
              <button type="button" className="button button--primary" onClick={onLogout}>
                Log out
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="page-tabs" role="tablist" aria-label="Authentication pages">
              <button
                type="button"
                className={mode === 'login' ? 'page-tabs__button is-active' : 'page-tabs__button'}
                onClick={() => onModeChange('login')}
              >
                Login
              </button>
              <button
                type="button"
                className={mode === 'signup' ? 'page-tabs__button is-active' : 'page-tabs__button'}
                onClick={() => onModeChange('signup')}
              >
                Sign up
              </button>
            </div>

            {notice ? <p className="helper-text">{notice}</p> : null}

            {mode === 'login' ? (
              <form className="form-stack page-card__body" onSubmit={handleLoginSubmit}>
                <label className="field">
                  <span>Email</span>
                  <input
                    type="email"
                    value={loginForm.email}
                    onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))}
                    required
                  />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={loginForm.password}
                    onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))}
                    required
                  />
                </label>
                <p className="helper-text">Forgot your password? Password recovery will be available soon.</p>
                <div className="page-card__actions">
                  <button type="button" className="button button--ghost" onClick={onClose}>
                    Back
                  </button>
                  <button type="submit" className="button button--primary">
                    Login
                  </button>
                </div>
              </form>
            ) : (
              <form className="form-stack page-card__body" onSubmit={handleSignUpSubmit}>
                <label className="field">
                  <span>Name</span>
                  <input
                    type="text"
                    value={signUpForm.name}
                    onChange={(event) => setSignUpForm((current) => ({ ...current, name: event.target.value }))}
                    required
                  />
                </label>
                <label className="field">
                  <span>Email</span>
                  <input
                    type="email"
                    value={signUpForm.email}
                    onChange={(event) => setSignUpForm((current) => ({ ...current, email: event.target.value }))}
                    required
                  />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={signUpForm.password}
                    onChange={(event) => setSignUpForm((current) => ({ ...current, password: event.target.value }))}
                    required
                  />
                </label>
                <div className="page-card__actions">
                  <button type="button" className="button button--ghost" onClick={onClose}>
                    Back
                  </button>
                  <button type="submit" className="button button--primary">
                    Create account
                  </button>
                </div>
              </form>
            )}
          </>
        )}
      </section>
    </div>
  );
}

export default AuthPage;
