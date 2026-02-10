import React, { useState, useEffect, useRef } from 'react';
import '../styles/LiveChat.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function LiveChat({ user }) {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const [filter, setFilter] = useState('all');
  const eventSourceRef = useRef(null);
  const eventsEndRef = useRef(null);

  useEffect(() => {
    fetchRecentEvents();
    connectSSE();
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [events]);

  const fetchRecentEvents = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const response = await fetch(`${API_URL}/api/recent_events`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setEvents(data.events || []);
    } catch (error) {
      console.error('Error fetching recent events:', error);
    }
  };

  const connectSSE = () => {
    try {
      const eventSource = new EventSource(`${API_URL}/api/events`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event_type !== 'heartbeat') {
            setEvents(prev => [data, ...prev].slice(0, 100));
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e);
        }
      };

      eventSource.onerror = () => {
        setConnected(false);
        eventSource.close();
        setTimeout(connectSSE, 5000);
      };
    } catch (error) {
      console.error('SSE connection error:', error);
      setConnected(false);
    }
  };

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'ticket_open': return 'fa-plus-circle';
      case 'ticket_claim': return 'fa-hand-paper';
      case 'ticket_close': return 'fa-check-circle';
      case 'escalation': return 'fa-exclamation-triangle';
      case 'notes_update': return 'fa-edit';
      default: return 'fa-info-circle';
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'ticket_open': return 'event-new';
      case 'ticket_claim': return 'event-claimed';
      case 'ticket_close': return 'event-closed';
      case 'escalation': return 'event-escalated';
      default: return 'event-default';
    }
  };

  const getEventLabel = (type) => {
    switch (type) {
      case 'ticket_open': return 'Neues Ticket';
      case 'ticket_claim': return 'Übernommen';
      case 'ticket_close': return 'Geschlossen';
      case 'escalation': return 'Eskaliert';
      case 'notes_update': return 'Notiz aktualisiert';
      default: return type;
    }
  };

  const filteredEvents = events.filter(event => {
    if (filter === 'all') return true;
    return event.event_type === filter;
  });

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('de-DE');
  };

  return (
    <div className="live-chat-page" data-testid="live-chat-page">
      <div className="page-header">
        <div className="header-left">
          <h1>Live Events</h1>
          <span className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            <i className={`fas ${connected ? 'fa-wifi' : 'fa-wifi-slash'}`}></i>
            {connected ? 'Verbunden' : 'Getrennt'}
          </span>
        </div>
        <div className="header-right">
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
            data-testid="event-filter"
          >
            <option value="all">Alle Events</option>
            <option value="ticket_open">Neue Tickets</option>
            <option value="ticket_claim">Übernommen</option>
            <option value="ticket_close">Geschlossen</option>
            <option value="escalation">Eskalationen</option>
          </select>
          <button onClick={fetchRecentEvents} className="btn btn-secondary">
            <i className="fas fa-sync-alt"></i>
          </button>
        </div>
      </div>

      <div className="events-container">
        <div className="events-stats">
          <div className="stat-card">
            <i className="fas fa-bolt"></i>
            <div>
              <span className="stat-value">{events.length}</span>
              <span className="stat-label">Events (letzte 100)</span>
            </div>
          </div>
          <div className="stat-card new">
            <i className="fas fa-plus-circle"></i>
            <div>
              <span className="stat-value">{events.filter(e => e.event_type === 'ticket_open').length}</span>
              <span className="stat-label">Neue Tickets</span>
            </div>
          </div>
          <div className="stat-card closed">
            <i className="fas fa-check-circle"></i>
            <div>
              <span className="stat-value">{events.filter(e => e.event_type === 'ticket_close').length}</span>
              <span className="stat-label">Geschlossen</span>
            </div>
          </div>
          <div className="stat-card escalated">
            <i className="fas fa-exclamation-triangle"></i>
            <div>
              <span className="stat-value">{events.filter(e => e.event_type === 'escalation').length}</span>
              <span className="stat-label">Eskalationen</span>
            </div>
          </div>
        </div>

        <div className="events-list" data-testid="events-list">
          {filteredEvents.length === 0 ? (
            <div className="empty-state">
              <i className="fas fa-stream"></i>
              <p>Keine Events gefunden</p>
              <span>Neue Events erscheinen hier in Echtzeit</span>
            </div>
          ) : (
            filteredEvents.map((event, index) => (
              <div 
                key={event.id || index} 
                className={`event-item ${getEventColor(event.event_type)}`}
                data-testid={`event-${event.id || index}`}
              >
                <div className="event-icon">
                  <i className={`fas ${getEventIcon(event.event_type)}`}></i>
                </div>
                <div className="event-content">
                  <div className="event-header">
                    <span className="event-type">{getEventLabel(event.event_type)}</span>
                    <span className="event-time">
                      {formatDate(event.timestamp)} {formatTime(event.timestamp)}
                    </span>
                  </div>
                  <div className="event-details">
                    {event.data?.subject && (
                      <span className="event-subject">{event.data.subject}</span>
                    )}
                    {event.data?.username && (
                      <span className="event-user">
                        <i className="fas fa-user"></i> {event.data.username}
                      </span>
                    )}
                    {event.data?.claimed_by && (
                      <span className="event-user">
                        <i className="fas fa-hand-paper"></i> {event.data.claimed_by}
                      </span>
                    )}
                    {event.data?.closed_by && (
                      <span className="event-user">
                        <i className="fas fa-check"></i> {event.data.closed_by}
                      </span>
                    )}
                    {event.data?.ticket_id && (
                      <span className="event-ticket-id">
                        ID: {event.data.ticket_id.substring(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={eventsEndRef} />
        </div>
      </div>
    </div>
  );
}

export default LiveChat;
