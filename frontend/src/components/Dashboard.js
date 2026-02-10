import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import '../styles/Dashboard.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function Dashboard({ user }) {
  const [kpi, setKpi] = useState(null);
  const [recentTickets, setRecentTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [kpiRes, ticketsRes] = await Promise.all([
        axios.get(`${API_URL}/api/kpi`, { headers }),
        axios.get(`${API_URL}/api/tickets?limit=5`, { headers })
      ]);

      setKpi(kpiRes.data);
      setRecentTickets(ticketsRes.data.tickets || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="dashboard" data-testid="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Willkommen zurück, {user?.username}!</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card" data-testid="kpi-total">
          <div className="kpi-icon blue">
            <i className="fas fa-ticket-alt"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{kpi?.totalTickets || 0}</div>
            <div className="kpi-label">Gesamt Tickets</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-open">
          <div className="kpi-icon green">
            <i className="fas fa-folder-open"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{kpi?.openTickets || 0}</div>
            <div className="kpi-label">Offen</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-claimed">
          <div className="kpi-icon purple">
            <i className="fas fa-user-check"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{kpi?.claimedTickets || 0}</div>
            <div className="kpi-label">In Bearbeitung</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-closed">
          <div className="kpi-icon gray">
            <i className="fas fa-check-circle"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{kpi?.closedTickets || 0}</div>
            <div className="kpi-label">Geschlossen</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-response">
          <div className="kpi-icon orange">
            <i className="fas fa-clock"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{Math.round((kpi?.avgResponseTime || 0) / 60)}m</div>
            <div className="kpi-label">Ø Antwortzeit</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-resolution">
          <div className="kpi-icon teal">
            <i className="fas fa-hourglass-half"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{Math.round((kpi?.avgResolutionTime || 0) / 3600)}h</div>
            <div className="kpi-label">Ø Lösungszeit</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-sla">
          <div className="kpi-icon red">
            <i className="fas fa-exclamation-triangle"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{kpi?.slaViolations || 0}</div>
            <div className="kpi-label">SLA Verstöße</div>
          </div>
        </div>

        <div className="kpi-card" data-testid="kpi-escalations">
          <div className="kpi-icon yellow">
            <i className="fas fa-level-up-alt"></i>
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{kpi?.escalations || 0}</div>
            <div className="kpi-label">Eskalationen</div>
          </div>
        </div>
      </div>

      <div className="recent-section">
        <div className="section-header">
          <h2>Neueste Tickets</h2>
          <Link to="/tickets" className="btn btn-secondary">Alle anzeigen</Link>
        </div>

        <div className="tickets-table-container">
          <table className="tickets-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Betreff</th>
                <th>Typ</th>
                <th>Priorität</th>
                <th>Status</th>
                <th>Erstellt</th>
              </tr>
            </thead>
            <tbody>
              {recentTickets.map((ticket) => (
                <tr key={ticket.ticketId}>
                  <td>#{String(ticket.ticketId).padStart(4, '0')}</td>
                  <td>
                    <Link to={`/tickets/${ticket.ticketId}`} className="ticket-link">
                      {ticket.subject}
                    </Link>
                  </td>
                  <td>{ticket.type}</td>
                  <td>
                    <span className={`badge badge-${ticket.priority}`}>
                      {ticket.priority.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${ticket.status}`}>
                      {ticket.status.toUpperCase()}
                    </span>
                  </td>
                  <td>{new Date(ticket.createdAt).toLocaleString('de-DE')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;