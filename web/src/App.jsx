import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import SetupPage from './pages/SetupPage';
import ChatPage from './pages/ChatPage';
import ChatDetailsPage from './pages/ChatDetailsPage';
import RolesPage from './pages/RolesPage';
import ProvidersPage from './pages/ProvidersPage';
import ProfilePage from './pages/ProfilePage';
import SecurityPage from './pages/SecurityPage';
import LogsPage from './pages/LogsPage';
import HistoryPage from './pages/HistoryPage';
import ArchivePage from './pages/ArchivePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/chat" element={<Layout><ChatPage /></Layout>} />
        <Route path="/chat-details" element={<Layout><ChatDetailsPage /></Layout>} />
        <Route path="/roles" element={<Layout><RolesPage /></Layout>} />
        <Route path="/providers" element={<Layout><ProvidersPage /></Layout>} />
        <Route path="/profile" element={<Layout><ProfilePage /></Layout>} />
        <Route path="/security" element={<Layout><SecurityPage /></Layout>} />
        <Route path="/logs" element={<Layout><LogsPage /></Layout>} />
        <Route path="/history" element={<Layout><HistoryPage /></Layout>} />
        <Route path="/archive" element={<Layout><ArchivePage /></Layout>} />
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}
