import React, { useState } from 'react';
import axios from 'axios';
import '../styles/Login.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, {
        username,
        password
      });

      onLogin(response.data.token, response.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container" data-testid="login-container">
      <div className="login-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>
      
      <div className="login-card" data-testid="login-card">
        <div className="login-header">
          <div className="logo-container">
            <svg className="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1>Armesa Ticket System</h1>
          <p>Enterprise Control Center</p>
        </div>

        <form onSubmit={handleSubmit} data-testid="login-form">
          {error && (
            <div className="error-message" data-testid="error-message">
              <i className="fas fa-exclamation-circle"></i>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Benutzername</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              required
              data-testid="username-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Passwort</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              data-testid="password-input"
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary btn-login" 
            disabled={loading}
            data-testid="login-button"
          >
            {loading ? 'Anmeldung läuft...' : 'Anmelden'}
          </button>
        </form>

        <div className="login-footer">
          <p>Standard Login: admin / admin</p>
        </div>
      </div>
    </div>
  );
}

export default Login;