import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/Settings.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function Settings({ user }) {
  const [settings, setSettings] = useState({
    sla_first_response: 30,
    sla_resolution: 240,
    auto_close_hours: 48,
    max_tickets_per_user: 3,
    notification_email: '',
    discord_webhook: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const response = await axios.get(`${API_URL}/api/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data) {
        setSettings(prev => ({ ...prev, ...response.data }));
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });
    try {
      const token = localStorage.getItem('armesa_token');
      await axios.put(`${API_URL}/api/settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage({ type: 'success', text: 'Einstellungen erfolgreich gespeichert!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Fehler beim Speichern der Einstellungen.' });
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="settings-page" data-testid="settings-page">
      <div className="page-header">
        <h1>Einstellungen</h1>
      </div>

      {message.text && (
        <div className={`alert alert-${message.type}`} data-testid="settings-message">
          {message.text}
        </div>
      )}

      <div className="settings-grid">
        <div className="settings-card">
          <div className="card-header">
            <i className="fas fa-clock"></i>
            <h2>SLA Einstellungen</h2>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label>Erste Antwort (Minuten)</label>
              <input
                type="number"
                value={settings.sla_first_response}
                onChange={(e) => handleChange('sla_first_response', parseInt(e.target.value))}
                min="1"
                data-testid="sla-first-response-input"
              />
              <span className="help-text">Zeit bis zur ersten Antwort auf ein Ticket</span>
            </div>
            <div className="form-group">
              <label>Lösungszeit (Minuten)</label>
              <input
                type="number"
                value={settings.sla_resolution}
                onChange={(e) => handleChange('sla_resolution', parseInt(e.target.value))}
                min="1"
                data-testid="sla-resolution-input"
              />
              <span className="help-text">Maximale Zeit bis zur Ticket-Lösung</span>
            </div>
          </div>
        </div>

        <div className="settings-card">
          <div className="card-header">
            <i className="fas fa-ticket-alt"></i>
            <h2>Ticket Einstellungen</h2>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label>Auto-Schließen nach (Stunden)</label>
              <input
                type="number"
                value={settings.auto_close_hours}
                onChange={(e) => handleChange('auto_close_hours', parseInt(e.target.value))}
                min="1"
                data-testid="auto-close-input"
              />
              <span className="help-text">Inaktive Tickets automatisch schließen</span>
            </div>
            <div className="form-group">
              <label>Max. Tickets pro Benutzer</label>
              <input
                type="number"
                value={settings.max_tickets_per_user}
                onChange={(e) => handleChange('max_tickets_per_user', parseInt(e.target.value))}
                min="1"
                max="10"
                data-testid="max-tickets-input"
              />
              <span className="help-text">Maximale offene Tickets gleichzeitig</span>
            </div>
          </div>
        </div>

        <div className="settings-card">
          <div className="card-header">
            <i className="fas fa-bell"></i>
            <h2>Benachrichtigungen</h2>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label>E-Mail für Benachrichtigungen</label>
              <input
                type="email"
                value={settings.notification_email}
                onChange={(e) => handleChange('notification_email', e.target.value)}
                placeholder="admin@example.com"
                data-testid="notification-email-input"
              />
            </div>
            <div className="form-group">
              <label>Discord Webhook URL</label>
              <input
                type="url"
                value={settings.discord_webhook}
                onChange={(e) => handleChange('discord_webhook', e.target.value)}
                placeholder="https://discord.com/api/webhooks/..."
                data-testid="discord-webhook-input"
              />
            </div>
          </div>
        </div>

        <div className="settings-card">
          <div className="card-header">
            <i className="fas fa-info-circle"></i>
            <h2>System Info</h2>
          </div>
          <div className="card-body">
            <div className="info-row">
              <span>Version</span>
              <span>Control Center X Ultra v2.0</span>
            </div>
            <div className="info-row">
              <span>Benutzer</span>
              <span>{user?.username}</span>
            </div>
            <div className="info-row">
              <span>Rolle</span>
              <span className="badge">{user?.role}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="settings-actions">
        <button 
          onClick={handleSave} 
          className="btn btn-primary"
          disabled={saving}
          data-testid="save-settings-btn"
        >
          {saving ? (
            <>
              <i className="fas fa-spinner fa-spin"></i> Speichern...
            </>
          ) : (
            <>
              <i className="fas fa-save"></i> Einstellungen speichern
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default Settings;
