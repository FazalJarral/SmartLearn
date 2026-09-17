import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { LearningPackage } from "./pages/LearningPackage";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Upload } from "./pages/Upload";
import { AuthProvider } from "./lib/auth";
import { ApiWakingBanner } from "./components/ApiWakingBanner";
import "./styles/index.css";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-paper text-ink">
            <ApiWakingBanner />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/packages/:packageId" element={<LearningPackage />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Routes>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
