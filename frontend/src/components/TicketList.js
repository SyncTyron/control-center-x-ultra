import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import '../styles/TicketList.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function TicketList({ user }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: ''
  });

  useEffect(() => {
    fetchTickets();
  }, [filters.status, filters.priority]);

  const fetchTickets = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);

      const response = await axios.get(`${API_URL}/api/tickets?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setTickets(response.data.tickets || []);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!filters.search.trim()) {
      fetchTickets();
      return;
    }

    try {
      const token = localStorage.getItem('armesa_token');
      const response = await axios.get(`${API_URL}/api/search?q=${filters.search}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTickets(response.data.results || []);
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="ticket-list-page" data-testid="ticket-list">
      <div className="page-header">
        <h1>Alle Tickets</h1>
        <button onClick={fetchTickets} className="btn btn-secondary">
          <i className="fas fa-sync-alt"></i> Aktualisieren
        </button>
      </div>

      <div className="filters-section">
        <div className="search-box">
          <input
            type="text"
            placeholder="Tickets durchsuchen..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            data-testid="search-input"
          />
          <button onClick={handleSearch} className="btn btn-primary">
            <i className="fas fa-search"></i>
          </button>
        </div>

        <div className="filter-group">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            data-testid="status-filter"
          >
            <option value="">Alle Status</option>
            <option value="open">Offen</option>
            <option value="claimed">In Bearbeitung</option>
            <option value="closed">Geschlossen</option>
          </select>

          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
            data-testid="priority-filter"
          >
            <option value="">Alle Prioritäten</option>
            <option value="low">Niedrig</option>
            <option value="medium">Mittel</option>
            <option value="high">Hoch</option>
            <option value="critical">Kritisch</option>
          </select>
        </div>
      </div>

      <div className="tickets-grid">
        {tickets.map((ticket) => (
          <Link to={`/tickets/${ticket.ticketId}`} key={ticket.ticketId} className="ticket-card" data-testid={`ticket-${ticket.ticketId}`}>
            <div className="ticket-card-header">
              <span className="ticket-id">#{String(ticket.ticketId).padStart(4, '0')}</span>
              <span className={`badge badge-${ticket.priority}`}>{ticket.priority.toUpperCase()}</span>
            </div>
            
            <h3 className="ticket-subject">{ticket.subject}</h3>
            <p className="ticket-description">{ticket.description.substring(0, 100)}...</p>
            
            <div className="ticket-card-footer">
              <div className="ticket-meta">
                <span className={`badge badge-${ticket.status}`}>{ticket.status.toUpperCase()}</span>
                <span className="ticket-type">{ticket.type}</span>
              </div>
              <div className="ticket-date">{new Date(ticket.createdAt).toLocaleDateString('de-DE')}</div>
            </div>
          </Link>
        ))}
      </div>

      {tickets.length === 0 && (
        <div className="empty-state">
          <i className="fas fa-inbox"></i>
          <p>Keine Tickets gefunden</p>
        </div>
      )}
    </div>
  );
}

export default TicketList;