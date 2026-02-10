import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/UserManagement.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function UserManagement({ user }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'viewer' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('armesa_token');
      const response = await axios.get(`${API_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      if (error.response?.status === 403) {
        setError('Keine Berechtigung. Nur Admins können Benutzer verwalten.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    if (!newUser.username || !newUser.password) {
      setError('Benutzername und Passwort sind erforderlich.');
      return;
    }

    try {
      const token = localStorage.getItem('armesa_token');
      await axios.post(`${API_URL}/api/admin/users`, newUser, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Benutzer erfolgreich erstellt!');
      setNewUser({ username: '', password: '', role: 'viewer' });
      setShowModal(false);
      fetchUsers();
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Erstellen des Benutzers.');
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Möchtest du den Benutzer "${username}" wirklich löschen?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('armesa_token');
      await axios.delete(`${API_URL}/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Benutzer erfolgreich gelöscht!');
      fetchUsers();
    } catch (error) {
      setError('Fehler beim Löschen des Benutzers.');
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'admin': return 'badge-admin';
      case 'support': return 'badge-support';
      default: return 'badge-viewer';
    }
  };

  if (loading) {
    return <div className="loading">Laden...</div>;
  }

  return (
    <div className="user-management-page" data-testid="user-management-page">
      <div className="page-header">
        <h1>Benutzerverwaltung</h1>
        {user?.role === 'admin' && (
          <button 
            onClick={() => setShowModal(true)} 
            className="btn btn-primary"
            data-testid="add-user-btn"
          >
            <i className="fas fa-user-plus"></i> Neuer Benutzer
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert-error" data-testid="error-alert">
          <i className="fas fa-exclamation-circle"></i> {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success" data-testid="success-alert">
          <i className="fas fa-check-circle"></i> {success}
        </div>
      )}

      <div className="users-table-container">
        <table className="users-table" data-testid="users-table">
          <thead>
            <tr>
              <th>Benutzer</th>
              <th>Rolle</th>
              <th>Erstellt am</th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} data-testid={`user-row-${u.id}`}>
                <td>
                  <div className="user-cell">
                    <div className="user-avatar">
                      {u.username?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <span>{u.username}</span>
                  </div>
                </td>
                <td>
                  <span className={`role-badge ${getRoleBadgeClass(u.role)}`}>
                    {u.role === 'admin' && <i className="fas fa-crown"></i>}
                    {u.role === 'support' && <i className="fas fa-headset"></i>}
                    {u.role === 'viewer' && <i className="fas fa-eye"></i>}
                    {u.role}
                  </span>
                </td>
                <td>{u.created_at ? new Date(u.created_at).toLocaleDateString('de-DE') : '-'}</td>
                <td>
                  {user?.role === 'admin' && u.username !== user.username && (
                    <button
                      onClick={() => handleDeleteUser(u.id, u.username)}
                      className="btn btn-danger btn-sm"
                      data-testid={`delete-user-${u.id}`}
                    >
                      <i className="fas fa-trash"></i>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {users.length === 0 && (
        <div className="empty-state">
          <i className="fas fa-users"></i>
          <p>Keine Benutzer gefunden</p>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" data-testid="create-user-modal">
          <div className="modal">
            <div className="modal-header">
              <h2>Neuen Benutzer erstellen</h2>
              <button onClick={() => setShowModal(false)} className="btn-close">
                <i className="fas fa-times"></i>
              </button>
            </div>
            <form onSubmit={handleCreateUser}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Benutzername</label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    placeholder="Benutzername eingeben"
                    data-testid="new-username-input"
                  />
                </div>
                <div className="form-group">
                  <label>Passwort</label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    placeholder="Passwort eingeben"
                    data-testid="new-password-input"
                  />
                </div>
                <div className="form-group">
                  <label>Rolle</label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    data-testid="new-role-select"
                  >
                    <option value="viewer">Viewer (Nur Lesen)</option>
                    <option value="support">Support (Tickets bearbeiten)</option>
                    <option value="admin">Admin (Voller Zugriff)</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">
                  Abbrechen
                </button>
                <button type="submit" className="btn btn-primary" data-testid="submit-create-user">
                  <i className="fas fa-user-plus"></i> Erstellen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserManagement;
