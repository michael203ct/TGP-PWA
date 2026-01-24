import React, { createContext, useContext, useState, useEffect } from 'react';

const darkColors = {
  background: '#0F172A',
  surface: '#1E293B',
  card: '#1E293B',
  text: '#F1F5F9',
  textSecondary: '#94A3B8',
  accent: '#38BDF8',
  accentLight: '#0EA5E9',
  border: '#334155',
  cardBorder: 'transparent',
  error: '#EF4444',
  success: '#22C55E',
};

const lightColors = {
  background: '#F8FAFC',
  surface: '#FFFFFF',
  card: '#FFFFFF',
  text: '#0F172A',
  textSecondary: '#64748B',
  accent: '#0EA5E9',
  accentLight: '#38BDF8',
  border: '#E2E8F0',
  cardBorder: '#E2E8F0',
  error: '#DC2626',
  success: '#16A34A',
};

const ThemeContext = createContext(undefined);

export const ThemeProvider = ({ children }) => {
  const [mode, setMode] = useState('dark');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      setMode(savedTheme);
    }
  }, []);

  const toggleTheme = () => {
    const newMode = mode === 'dark' ? 'light' : 'dark';
    setMode(newMode);
    localStorage.setItem('theme', newMode);
  };

  const colors = mode === 'dark' ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ mode, colors, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
