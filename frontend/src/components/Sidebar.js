import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/Sidebar.css';

function Sidebar({ user, onLogout }) {
  const location = useLocation();

  const menuItems = [
    { path: '/', icon: 'fas fa-th-large', label: 'Dashboard' },
    { path: '/tickets', icon: 'fas fa-ticket-alt', label: 'Tickets' },
    { path: '/analytics', icon: 'fas fa-chart-line', label: 'Analytics' },
    { path: '/support', icon: 'fas fa-users', label: 'Support Stats' },
    { path: '/live', icon: 'fas fa-comments', label: 'Live Chat' },
    { path: '/users', icon: 'fas fa-user-cog', label: 'Benutzerverwaltung' },
    { path: '/settings', icon: 'fas fa-cog', label: 'Einstellungen' }
  ];

  return (
    <div className="sidebar" data-testid="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <svg className="logo-icon" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2"/>
          </svg>
          <span>Armesa</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
            data-testid={`nav-${item.label.toLowerCase()}`}
          >
            <i className={item.icon}></i>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="user-details">
            <div className="user-name">{user?.username}</div>
            <div className="user-role">{user?.role}</div>
          </div>
        </div>
        <button 
          onClick={onLogout} 
          className="btn-logout"
          data-testid="logout-button"
        >
          <i className="fas fa-sign-out-alt"></i>
        </button>
      </div>
    </div>
  );
}

export default Sidebar;