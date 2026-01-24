import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoArrowBack, IoMoon, IoSunny, IoNotifications, IoGlobe, IoShield } from 'react-icons/io5';

const Settings = () => {
  const { colors, mode, toggleTheme } = useTheme();
  const navigate = useNavigate();

  return (
    <div style={{ backgroundColor: colors.background }} className="min-h-screen">
      <header 
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: colors.border }}
      >
        <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center">
          <IoArrowBack size={24} style={{ color: colors.text }} />
        </button>
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Settings</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <div className="space-y-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="w-full flex items-center gap-4 p-4 rounded-xl"
            style={{ backgroundColor: colors.surface }}
          >
            {mode === 'dark' ? (
              <IoSunny size={24} style={{ color: colors.accent }} />
            ) : (
              <IoMoon size={24} style={{ color: colors.accent }} />
            )}
            <div className="flex-1 text-left">
              <p className="font-semibold" style={{ color: colors.text }}>Appearance</p>
              <p className="text-sm" style={{ color: colors.textSecondary }}>
                {mode === 'dark' ? 'Dark mode' : 'Light mode'}
              </p>
            </div>
          </button>

          {/* Other Settings */}
          <div className="p-4 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <div className="flex items-center gap-4">
              <IoNotifications size={24} style={{ color: colors.accent }} />
              <div className="flex-1">
                <p className="font-semibold" style={{ color: colors.text }}>Notifications</p>
                <p className="text-sm" style={{ color: colors.textSecondary }}>Coming soon</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <div className="flex items-center gap-4">
              <IoGlobe size={24} style={{ color: colors.accent }} />
              <div className="flex-1">
                <p className="font-semibold" style={{ color: colors.text }}>Language</p>
                <p className="text-sm" style={{ color: colors.textSecondary }}>English (US)</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <div className="flex items-center gap-4">
              <IoShield size={24} style={{ color: colors.accent }} />
              <div className="flex-1">
                <p className="font-semibold" style={{ color: colors.text }}>Privacy</p>
                <p className="text-sm" style={{ color: colors.textSecondary }}>We respect your privacy</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm" style={{ color: colors.textSecondary }}>the gig pulse v1.0.0</p>
          <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>Educate. Elevate. Motivate.</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
