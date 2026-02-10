import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import TicketList from './components/TicketList';
import TicketDetail from './components/TicketDetail';
import Analytics from './components/Analytics';
import SupportStats from './components/SupportStats';
import Sidebar from './components/Sidebar';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('armesa_token');
    const userData = localStorage.getItem('armesa_user');
    
    if (token && userData) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, userData) => {
    localStorage.setItem('armesa_token', token);
    localStorage.setItem('armesa_user', JSON.stringify(userData));
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('armesa_token');
    localStorage.removeItem('armesa_user');
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return (
      <div className="loading-screen" data-testid="loading-screen">
        <div className="spinner"></div>
        <p>Laden...</p>
      </div>
    );
  }

  return (
    <Router>
      <div className="app" data-testid="app-container">
        {!isAuthenticated ? (
          <Routes>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        ) : (
          <div className="app-layout">
            <Sidebar user={user} onLogout={handleLogout} />
            <div className="main-content">
              <Routes>
                <Route path="/" element={<Dashboard user={user} />} />
                <Route path="/tickets" element={<TicketList user={user} />} />
                <Route path="/tickets/:ticketId" element={<TicketDetail user={user} />} />
                <Route path="/analytics" element={<Analytics user={user} />} />
                <Route path="/support" element={<SupportStats user={user} />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;