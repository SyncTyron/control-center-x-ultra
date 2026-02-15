import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/SupportStats.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function SupportStats({ user }) {
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const response = await axios.get(`${API_URL}/api/support_stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data.stats || []);
    } catch (error) {
      console.error('Error fetching support stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="support-stats-page" data-testid="support-stats">
      <div className="page-header">
        <h1>Support Team Statistiken</h1>
        <button onClick={fetchStats} className="btn btn-secondary">
          <i className="fas fa-sync-alt"></i> Aktualisieren
        </button>
      </div>

      <div className="stats-grid">
        {stats.map((supporter, index) => (
          <div key={supporter.supporter || index} className="supporter-card" data-testid={`supporter-${supporter.supporter}`}>
            <div className="supporter-header">
              <div className="supporter-avatar">
                {supporter.supporter?.[0]?.toUpperCase() || 'S'}
              </div>
              <div className="supporter-info">
                <h3>{supporter.supporter}</h3>
                <span className="supporter-rank">#{index + 1} Supporter</span>
              </div>
            </div>

            <div className="supporter-metrics">
              <div className="metric">
                <div className="metric-icon blue">
                  <i className="fas fa-ticket-alt"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{supporter.closed_tickets || 0}</div>
                  <div className="metric-label">Tickets geschlossen</div>
                </div>
              </div>

              <div className="metric">
                <div className="metric-icon green">
                  <i className="fas fa-tasks"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{supporter.total_tickets || 0}</div>
                  <div className="metric-label">Gesamt bearbeitet</div>
                </div>
              </div>

              <div className="metric">
                <div className="metric-icon purple">
                  <i className="fas fa-arrow-up"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{supporter.escalations || 0}</div>
                  <div className="metric-label">Eskalationen</div>
                </div>
              </div>

              <div className="metric">
                <div className="metric-icon red">
                  <i className="fas fa-exclamation-triangle"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{supporter.sla_breaches || 0}</div>
                  <div className="metric-label">SLA Verstöße</div>
                </div>
              </div>
            </div>

            <div className="supporter-footer">
              <div className="performance-score">
                <span>Performance Score</span>
                <div className="score-bar">
                  <div 
                    className="score-fill" 
                    style={{ 
                      width: `${supporter.score || 0}%`,
                      background: supporter.score < 50 ? '#ef4444' : supporter.score < 75 ? '#f59e0b' : '#10b981'
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {stats.length === 0 && (
        <div className="empty-state">
          <i className="fas fa-users"></i>
          <p>Keine Support-Daten verfügbar</p>
        </div>
      )}
    </div>
  );
}

export default SupportStats;