import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { useRecommendationSummary } from "../hooks/queries";
import Icon from "./Icon";
import SyncButton from "./SyncButton";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { to: "/products", label: "Products", icon: "box" },
  { to: "/recommendations", label: "Recommendations", icon: "bulb", badge: true },
  { to: "/sync", label: "Sync history", icon: "sync" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { data: recSummary } = useRecommendationSummary();
  const [navOpen, setNavOpen] = useState(false);
  const location = useLocation();
  const query = location.search; // keep ?days= when moving between pages

  return (
    <div className="shell">
      <aside className={`sidebar ${navOpen ? "is-open" : ""}`}>
        <div className="brand-mark">
          <img src="/favicon.svg" alt="" width="28" height="28" />
          <span>ShelfSense</span>
        </div>
        <nav className="nav" onClick={() => setNavOpen(false)}>
          {NAV.map((item) => (
            <NavLink key={item.to} to={`${item.to}${query}`} className="nav-link">
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.badge && recSummary?.open_total > 0 && <span className="nav-badge">{recSummary.open_total}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip">
            <div className="avatar">{user?.username?.[0]?.toUpperCase()}</div>
            <div>
              <div className="user-name">{user?.username}</div>
              <div className="user-brand">{user?.brand?.name}</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-block" onClick={logout}>
            <Icon name="logout" size={16} /> Log out
          </button>
        </div>
      </aside>
      {navOpen && <div className="scrim" onClick={() => setNavOpen(false)} />}

      <div className="main">
        <header className="topbar">
          <button className="btn btn-icon menu-toggle" aria-label="Open menu" onClick={() => setNavOpen(true)}>
            <Icon name="menu" />
          </button>
          <div className="topbar-brand">{user?.brand?.name}</div>
          <SyncButton />
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
