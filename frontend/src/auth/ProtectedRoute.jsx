import { Navigate, useLocation } from "react-router-dom";

import Spinner from "../components/Spinner";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ children }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") return <Spinner fullPage />;
  if (status !== "authenticated") return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}
