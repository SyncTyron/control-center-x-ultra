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
          <i className="fas fa-clock"></i>
          <div>
            <div className="summary-value">{slaData.length}</div>
            <div className="summary-label">Aktive Tickets</div>
          </div>
        </div>
        <div className="summary-card danger">
          <i className="fas fa-exclamation-triangle"></i>
          <div>
            <div className="summary-value">{slaData.filter(t => t.violated).length}</div>
            <div className="summary-label">SLA Verstöße</div>
          </div>
        </div>
        <div className="summary-card warning">
          <i className="fas fa-hourglass-half"></i>
          <div>
            <div className="summary-value">{slaData.filter(t => !t.violated && t.slaRemaining < 600).length}</div>
            <div className="summary-label">Kritisch</div>
          </div>
        </div>
      </div>

      <div className="sla-table-container">
        <table className="sla-table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Betreff</th>
              <th>Priorität</th>
              <th>Verstrichene Zeit</th>
              <th>SLA Verbleibend</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {slaData.map((ticket) => (
              <tr key={ticket.ticketId} className={ticket.violated ? 'sla-violated' : ''}>
                <td>#{String(ticket.ticketId).padStart(4, '0')}</td>
                <td>{ticket.subject}</td>
                <td>
                  <span className={`badge badge-${ticket.priority}`}>
                    {ticket.priority.toUpperCase()}
                  </span>
                </td>
                <td>{formatTime(ticket.elapsed)}</td>
                <td className={ticket.violated ? 'text-danger' : ticket.slaRemaining < 600 ? 'text-warning' : ''}>
                  {formatTime(ticket.slaRemaining)}
                </td>
                <td>
                  {ticket.violated ? (
                    <span className="status-badge violated">
                      <i className="fas fa-times-circle"></i> Verstoßen
                    </span>
                  ) : ticket.slaRemaining < 600 ? (
                    <span className="status-badge warning">
                      <i className="fas fa-exclamation-circle"></i> Kritisch
                    </span>
                  ) : (
                    <span className="status-badge ok">
                      <i className="fas fa-check-circle"></i> OK
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {slaData.length === 0 && (
        <div className="empty-state">
          <i className="fas fa-check-double"></i>
          <p>Keine aktiven Tickets</p>
        </div>
      )}
    </div>
  );
}

export default Analytics;