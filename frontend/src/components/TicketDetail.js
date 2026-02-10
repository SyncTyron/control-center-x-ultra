import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import '../styles/TicketDetail.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function TicketDetail({ user }) {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchTicket();
  }, [ticketId]);

  const fetchTicket = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const response = await axios.get(`${API_URL}/api/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTicket(response.data.ticket || response.data);
    } catch (error) {
      console.error('Error fetching ticket:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTicket = async (updates) => {
    setUpdating(true);
    try {
      const token = localStorage.getItem('armesa_token');
      await axios.put(`${API_URL}/api/tickets/${ticketId}/notes`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchTicket();
    } catch (error) {
      console.error('Error updating ticket:', error);
      alert('Fehler beim Aktualisieren des Tickets');
    } finally {
      setUpdating(false);
    }
  };

  const addNote = async () => {
    if (!newNote.trim()) return;
    await updateTicket({ notes: newNote });
    setNewNote('');
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  if (!ticket) {
    return <div className="error">Ticket nicht gefunden</div>;
  }

  return (
    <div className="ticket-detail-page" data-testid="ticket-detail">
      <div className="detail-header">
        <button onClick={() => navigate('/tickets')} className="btn btn-secondary">
          <i className="fas fa-arrow-left"></i> Zurück
        </button>
        <h1>Ticket #{ticket.id ? ticket.id.substring(0, 8) : 'N/A'}</h1>
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          <div className="card ticket-info">
            <div className="ticket-info-header">
              <h2>{ticket.subject}</h2>
              <div className="ticket-badges">
                <span className={`badge badge-${ticket.priority || 'medium'}`}>{(ticket.priority || 'medium').toUpperCase()}</span>
                <span className={`badge badge-${ticket.status || 'open'}`}>{(ticket.status || 'open').toUpperCase()}</span>
                {ticket.escalation_flag && <span className="badge badge-critical">ESKALIERT</span>}
              </div>
            </div>

            <div className="ticket-description">
              <h3>Beschreibung</h3>
              <p>{ticket.description || 'Keine Beschreibung'}</p>
            </div>

            <div className="ticket-metadata">
              <div className="meta-item">
                <i className="fas fa-tag"></i>
                <span>Typ: {ticket.type}</span>
              </div>
              <div className="meta-item">
                <i className="fas fa-globe"></i>
                <span>Sprache: {(ticket.lang || 'de').toUpperCase()}</span>
              </div>
              <div className="meta-item">
                <i className="fas fa-user"></i>
                <span>Ersteller: {ticket.username}</span>
              </div>
              <div className="meta-item">
                <i className="fas fa-calendar"></i>
                <span>Erstellt: {ticket.created_at ? new Date(ticket.created_at).toLocaleString('de-DE') : 'N/A'}</span>
              </div>
            </div>
          </div>

          <div className="card notes-section">
            <h3>Interne Notizen</h3>
            
            <div className="notes-content">
              {ticket.notes ? (
                <p className="current-notes">{ticket.notes}</p>
              ) : (
                <p className="no-notes">Keine Notizen vorhanden</p>
              )}
            </div>

            {user.role !== 'viewer' && (
              <div className="add-note">
                <textarea
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Notiz hinzufügen oder aktualisieren..."
                  rows="3"
                  data-testid="note-input"
                />
                <button onClick={addNote} className="btn btn-primary" disabled={updating}>
                  <i className="fas fa-save"></i> Notiz speichern
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="detail-sidebar">
          {user.role !== 'viewer' && (
            <div className="card actions-card">
              <h3>Aktionen</h3>
              
              <div className="action-group">
                <label>Status ändern</label>
                <select
                  value={ticket.status || 'open'}
                  onChange={(e) => updateTicket({ status: e.target.value })}
                  disabled={updating}
                  data-testid="status-select"
                >
                  <option value="open">Offen</option>
                  <option value="claimed">In Bearbeitung</option>
                  <option value="closed">Geschlossen</option>
                </select>
              </div>

              <div className="action-group">
                <label>Priorität ändern</label>
                <select
                  value={ticket.priority || 'medium'}
                  onChange={(e) => updateTicket({ priority: e.target.value })}
                  disabled={updating}
                  data-testid="priority-select"
                >
                  <option value="low">Niedrig</option>
                  <option value="medium">Mittel</option>
                  <option value="high">Hoch</option>
                  <option value="critical">Kritisch</option>
                </select>
              </div>
            </div>
          )}

          <div className="card timeline-card">
            <h3>Timeline</h3>
            <div className="timeline">
              <div className="timeline-item">
                <i className="fas fa-plus-circle"></i>
                <div>
                  <strong>Erstellt</strong>
                  <span>{ticket.created_at ? new Date(ticket.created_at).toLocaleString('de-DE') : 'N/A'}</span>
                </div>
              </div>
              {ticket.claimed_at && (
                <div className="timeline-item">
                  <i className="fas fa-hand-paper"></i>
                  <div>
                    <strong>Übernommen von {ticket.claimed_by}</strong>
                    <span>{new Date(ticket.claimed_at).toLocaleString('de-DE')}</span>
                  </div>
                </div>
              )}
              {ticket.first_response_at && (
                <div className="timeline-item">
                  <i className="fas fa-reply"></i>
                  <div>
                    <strong>Erste Antwort</strong>
                    <span>{new Date(ticket.first_response_at).toLocaleString('de-DE')}</span>
                  </div>
                </div>
              )}
              {ticket.closed_at && (
                <div className="timeline-item">
                  <i className="fas fa-check-circle"></i>
                  <div>
                    <strong>Geschlossen von {ticket.closed_by}</strong>
                    <span>{new Date(ticket.closed_at).toLocaleString('de-DE')}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TicketDetail;