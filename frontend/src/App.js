import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { VotingProvider } from './contexts/VotingContext';
import { PWAInstallProvider } from './contexts/PWAInstallContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import Content from './pages/Content';
import News from './pages/News';
import Essentials from './pages/Essentials';
import Apps from './pages/Apps';
import Merch from './pages/Merch';
import Admin from './pages/Admin';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import DriverEssentials from './pages/DriverEssentials';
import HelpfulToolsGuide from './pages/HelpfulToolsGuide';
import PWABenefits from './pages/PWABenefits';
import SuggestChannel from './pages/SuggestChannel';
import SuggestNews from './pages/SuggestNews';
import SuggestGear from './pages/SuggestGear';
import SuggestApp from './pages/SuggestApp';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <VotingProvider>
        <PWAInstallProvider>
          <Router>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="content" element={<Content />} />
                <Route path="news" element={<News />} />
                <Route path="essentials" element={<Essentials />} />
                <Route path="apps" element={<Apps />} />
                <Route path="merch" element={<Merch />} />
                <Route path="admin" element={<Admin />} />
                <Route path="settings" element={<Settings />} />
                <Route path="profile-page" element={<Profile />} />
                <Route path="driver-essentials" element={<DriverEssentials />} />
                <Route path="helpful-tools-guide" element={<HelpfulToolsGuide />} />
                <Route path="pwa-benefits" element={<PWABenefits />} />
                <Route path="suggest-channel" element={<SuggestChannel />} />
                <Route path="suggest-news" element={<SuggestNews />} />
                <Route path="suggest-gear" element={<SuggestGear />} />
                <Route path="suggest-app" element={<SuggestApp />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </Router>
        </PWAInstallProvider>
      </VotingProvider>
    </ThemeProvider>
  );
}

export default App;
