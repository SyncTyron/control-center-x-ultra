import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/Analytics.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function Analytics({ user }) {
  const [slaData, setSlaData] = useState({ compliance: 0, total: 0, breached: 0, by_priority: {}, daily: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSLAData();
  }, []);

  const fetchSLAData = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const response = await axios.get(`${API_URL}/api/sla`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSlaData(response.data || { compliance: 0, total: 0, breached: 0, by_priority: {}, daily: [] });
    } catch (error) {
      console.error('Error fetching SLA data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(Math.abs(seconds) / 3600);
    const minutes = Math.floor((Math.abs(seconds) % 3600) / 60);
    return `${seconds < 0 ? '-' : ''}${hours}h ${minutes}m`;
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="analytics-page" data-testid="analytics">
      <div className="page-header">
        <h1>SLA Analytics</h1>
        <button onClick={fetchSLAData} className="btn btn-secondary">
          <i className="fas fa-sync-alt"></i> Aktualisieren
        </button>
      </div>

      <div className="sla-summary">
        <div className="summary-card">
          <i className="fas fa-chart-pie"></i>
          <div>
            <div className="summary-value">{slaData.compliance || 0}%</div>
            <div className="summary-label">SLA Compliance</div>
          </div>
        </div>
        <div className="summary-card">
          <i className="fas fa-ticket-alt"></i>
          <div>
            <div className="summary-value">{slaData.total || 0}</div>
            <div className="summary-label">Gesamt Tickets</div>
          </div>
        </div>
        <div className="summary-card danger">
          <i className="fas fa-exclamation-triangle"></i>
          <div>
            <div className="summary-value">{slaData.breached || 0}</div>
            <div className="summary-label">SLA Verstöße</div>
          </div>
        </div>
      </div>

      <div className="sla-section">
        <h2>SLA nach Priorität</h2>
        <div className="priority-grid">
          {Object.entries(slaData.by_priority || {}).map(([priority, data]) => (
            <div key={priority} className={`priority-card priority-${priority}`}>
              <div className="priority-header">
                <span className={`badge badge-${priority}`}>{priority.toUpperCase()}</span>
              </div>
              <div className="priority-stats">
                <div className="stat">
                  <span className="stat-value">{data.total}</span>
                  <span className="stat-label">Gesamt</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{data.breached}</span>
                  <span className="stat-label">Verstöße</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{data.compliance}%</span>
                  <span className="stat-label">Compliance</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="sla-section">
        <h2>Tägliche Übersicht</h2>
        <div className="sla-table-container">
          <table className="sla-table">
            <thead>
              <tr>
                <th>Datum</th>
                <th>Gesamt</th>
                <th>Verstöße</th>
                <th>Compliance</th>
              </tr>
            </thead>
            <tbody>
              {(slaData.daily || []).map((day) => (
                <tr key={day.date}>
                  <td>{day.date}</td>
                  <td>{day.total}</td>
                  <td className={day.breached > 0 ? 'text-danger' : ''}>{day.breached}</td>
                  <td>{day.total > 0 ? Math.round(((day.total - day.breached) / day.total) * 100) : 100}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {slaData.total === 0 && (
        <div className="empty-state">
          <i className="fas fa-check-double"></i>
          <p>Keine aktiven Tickets</p>
        </div>
      )}
    </div>
  );
}

export default Analytics;