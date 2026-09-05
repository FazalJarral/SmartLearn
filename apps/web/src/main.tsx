import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { BookOpen, LogIn, LogOut } from "lucide-react";

import { Dashboard } from "./pages/Dashboard";
import { LearningPackage } from "./pages/LearningPackage";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Upload } from "./pages/Upload";
import { AuthProvider, useAuth } from "./lib/auth";
import "./styles/index.css";

const queryClient = new QueryClient();

function AuthNav() {
  const { user, signOut } = useAuth();
  if (user) {
    return (
      <button className="inline-flex items-center gap-2 rounded-md bg-sage px-3 py-2 text-sm font-semibold text-white" onClick={signOut}>
        <LogOut aria-hidden="true" className="h-4 w-4" />
        Log out
      </button>
    );
  }
  return (
    <Link className="inline-flex items-center gap-2 rounded-md bg-sage px-3 py-2 text-sm font-semibold text-white" to="/login">
      <LogIn aria-hidden="true" className="h-4 w-4" />
      Sign in
    </Link>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-paper text-ink">
            <header className="border-b border-mist bg-white">
              <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4" aria-label="Primary">
                <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
                  <BookOpen aria-hidden="true" className="h-5 w-5 text-sage" />
                  SmartLearn
                </Link>
                <div className="flex items-center gap-2">
                  <Link className="rounded-md px-3 py-2 text-sm font-medium hover:bg-mist" to="/upload">Upload</Link>
                  <AuthNav />
                </div>
              </nav>
            </header>
            <main className="mx-auto max-w-6xl px-4 py-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/packages/:packageId" element={<LearningPackage />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Routes>
            </main>
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
