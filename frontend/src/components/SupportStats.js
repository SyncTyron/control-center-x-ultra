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
      setStats(response.data);
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
          <div key={supporter.supporterId} className="supporter-card" data-testid={`supporter-${supporter.supporterId}`}>
            <div className="supporter-header">
              <div className="supporter-avatar">
                {supporter.supporterName[0]?.toUpperCase() || 'S'}
              </div>
              <div className="supporter-info">
                <h3>{supporter.supporterName}</h3>
                <span className="supporter-rank">#{index + 1} Supporter</span>
              </div>
            </div>

            <div className="supporter-metrics">
              <div className="metric">
                <div className="metric-icon blue">
                  <i className="fas fa-ticket-alt"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{supporter.ticketsClosed}</div>
                  <div className="metric-label">Tickets geschlossen</div>
                </div>
              </div>

              <div className="metric">
                <div className="metric-icon green">
                  <i className="fas fa-clock"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{Math.round(supporter.avgResponseTime / 60)}m</div>
                  <div className="metric-label">Ø Antwortzeit</div>
                </div>
              </div>

              <div className="metric">
                <div className="metric-icon purple">
                  <i className="fas fa-hourglass-half"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{formatTime(supporter.avgResolutionTime)}</div>
                  <div className="metric-label">Ø Lösungszeit</div>
                </div>
              </div>

              <div className="metric">
                <div className="metric-icon red">
                  <i className="fas fa-exclamation-triangle"></i>
                </div>
                <div className="metric-content">
                  <div className="metric-value">{supporter.slaViolations}</div>
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
                      width: `${Math.max(0, Math.min(100, 100 - (supporter.slaViolations * 10)))}%`,
                      background: supporter.slaViolations > 5 ? '#ef4444' : supporter.slaViolations > 2 ? '#f59e0b' : '#10b981'
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