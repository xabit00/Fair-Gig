import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const roleLinks = {
  worker: [
    ["/worker", "Dashboard"],
    ["/earnings", "Earnings logger"],
    ["/grievances", "My grievances"],
    ["/certificate", "Income certificate"],
  ],
  verifier: [["/verifier", "Verification queue"]],
  advocate: [
    ["/grievance-board", "Grievance board"],
    ["/analytics", "Advocate analytics"],
  ],
};

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <NavLink className="brand" to="/" aria-label="FairGig home">
            <span className="brand-mark" aria-hidden="true">FG</span>
            <span>FairGig</span>
          </NavLink>
          <nav aria-label="Primary navigation">
            {roleLinks[user.role].map(([to, label]) => (
              <NavLink key={to} to={to} className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="account-panel">
          <div className="avatar" aria-hidden="true">{user.name.charAt(0).toUpperCase()}</div>
          <div className="account-copy">
            <strong>{user.name}</strong>
            <span>{user.role}</span>
          </div>
          <button className="text-button" type="button" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="content"><Outlet /></main>
    </div>
  );
}

