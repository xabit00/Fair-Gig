import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Certificate,
  ChartLineUp,
  ClockCounterClockwise,
  House,
  List,
  ListChecks,
  NotePencil,
  SignOut,
  TrendUp,
  Wallet,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageToggle from "./LanguageToggle";

const roleLinks = {
  worker: [
    { to: "/worker", labelKey: "dashboard", icon: House },
    { to: "/earnings", labelKey: "earningsLogger", icon: Wallet },
    { to: "/grievances", labelKey: "grievances", icon: WarningCircle },
    { to: "/certificate", labelKey: "incomeCertificate", icon: Certificate },
  ],
  verifier: [
    { to: "/verifier", labelKey: "verificationQueue", icon: ListChecks, end: true },
    { to: "/verifier/pending", labelKey: "pendingReviews", icon: NotePencil },
    { to: "/verifier/history", labelKey: "reviewHistory", icon: ClockCounterClockwise },
  ],
  advocate: [
    { to: "/analytics", labelKey: "analyticsDashboard", icon: ChartLineUp },
    { to: "/grievance-board", labelKey: "grievanceBoard", icon: WarningCircle },
    { to: "/income-trends", labelKey: "incomeTrends", icon: TrendUp },
  ],
};

function Brand() {
  return (
    <NavLink className="app-brand" to="/" aria-label="FairGig home">
      <span className="app-brand__mark" aria-hidden="true">FG</span>
      <span>FairGig</span>
    </NavLink>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const firstLinkRef = useRef(null);
  const links = roleLinks[user.role] || [];

  useEffect(() => setDrawerOpen(false), [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.setTimeout(() => firstLinkRef.current?.focus(), 0);
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [drawerOpen]);

  const initials = user.name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <button className="icon-button" type="button" onClick={() => setDrawerOpen(true)} aria-label="Open navigation" aria-expanded={drawerOpen}>
          <List size={24} />
        </button>
        <Brand />
        <span className="mobile-avatar" aria-label={`Signed in as ${user.name}`}>{initials}</span>
      </header>

      {drawerOpen && <button className="drawer-backdrop" type="button" aria-label="Close navigation" onClick={() => setDrawerOpen(false)} />}

      <aside className={`sidebar ${drawerOpen ? "sidebar--open" : ""}`} aria-label="Application sidebar">
        <div>
          <div className="sidebar__head">
            <Brand />
            <button className="icon-button sidebar__close" type="button" onClick={() => setDrawerOpen(false)} aria-label="Close navigation"><X size={22} /></button>
          </div>
          <div className="sidebar__utilities"><p className="sidebar__role">{user.role} {t("workspace")}</p><LanguageToggle /></div>
          <nav className="app-nav" aria-label="Primary navigation">
            {links.map(({ to, labelKey, icon: Icon, end }, index) => (
              <NavLink
                key={to}
                ref={index === 0 ? firstLinkRef : undefined}
                to={to}
                end={end}
                className={({ isActive }) => `app-nav__link${isActive ? " app-nav__link--active" : ""}`}
              >
                <Icon size={20} aria-hidden="true" />
                <span>{t(labelKey)}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="account-panel">
          <span className="account-panel__avatar" aria-hidden="true">{initials}</span>
          <span className="account-panel__copy">
            <strong>{user.name}</strong>
            <span>{user.email}</span>
          </span>
          <button className="account-panel__logout" type="button" onClick={logout}>
            <SignOut size={18} aria-hidden="true" />
            {t("signOut")}
          </button>
        </div>
      </aside>

      <main className="app-content" id="main-content"><Outlet /></main>
    </div>
  );
}
