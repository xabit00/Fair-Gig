import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import { useAuth } from "./auth/AuthContext";
import AppLayout from "./components/AppLayout";
import { LoginPage, RegisterPage } from "./pages/AuthPage";
import {
  AdvocateAnalytics,
  EarningsLogger,
  GrievanceBoard,
  IncomeCertificate,
  VerifierQueue,
  WorkerDashboard,
} from "./pages/Pages";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-state">Checking your session...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "verifier") return <Navigate to="/verifier" replace />;
  if (user.role === "advocate") return <Navigate to="/analytics" replace />;
  return <Navigate to="/worker" replace />;
}

function Guard({ roles, children }) {
  return <ProtectedRoute roles={roles}>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/worker" element={<Guard roles={["worker"]}><WorkerDashboard /></Guard>} />
        <Route path="/earnings" element={<Guard roles={["worker"]}><EarningsLogger /></Guard>} />
        <Route path="/grievances" element={<Guard roles={["worker"]}><GrievanceBoard workerView /></Guard>} />
        <Route path="/certificate" element={<Guard roles={["worker"]}><IncomeCertificate /></Guard>} />
        <Route path="/verifier" element={<Guard roles={["verifier"]}><VerifierQueue /></Guard>} />
        <Route path="/grievance-board" element={<Guard roles={["advocate"]}><GrievanceBoard /></Guard>} />
        <Route path="/analytics" element={<Guard roles={["advocate"]}><AdvocateAnalytics /></Guard>} />
      </Route>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

