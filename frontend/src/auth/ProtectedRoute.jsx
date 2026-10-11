import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ roles, children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="page-state" role="status">Checking your session...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return (
      <section className="empty-state">
        <p className="section-label">Access restricted</p>
        <h1>This page is not available for your role.</h1>
        <p>Your account is signed in as {user.role}.</p>
      </section>
    );
  }
  return children;
}

