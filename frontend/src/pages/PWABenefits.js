import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { usePWAInstall } from '../contexts/PWAInstallContext';
import { IoArrowBack, IoDownload, IoNotifications, IoFlash, IoCloud, IoCheckmarkCircle } from 'react-icons/io5';

const PWABenefits = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const { isInstallable, isInstalled, promptInstall } = usePWAInstall();

  const benefits = [
    {
      icon: IoFlash,
      title: 'Lightning Fast',
      description: 'Opens instantly like a native app'
    },
    {
      icon: IoNotifications,
      title: 'Push Notifications',
      description: 'Get notified about new content'
    },
    {
      icon: IoCloud,
      title: 'Works Offline',
      description: 'Access content without internet'
    },
    {
      icon: IoDownload,
      title: 'No App Store',
      description: 'Install directly from your browser'
    }
  ];

  return (
    <div style={{ backgroundColor: colors.background }} className="min-h-screen">
      <header 
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: colors.border }}
      >
        <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center">
          <IoArrowBack size={24} style={{ color: colors.text }} />
        </button>
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Install App</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <div className="text-center mb-8">
          <div 
            className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ backgroundColor: colors.accent + '20' }}
          >
            <IoDownload size={40} style={{ color: colors.accent }} />
          </div>
          <h2 className="text-2xl font-bold mb-2" style={{ color: colors.text }}>
            Get the App Experience
          </h2>
          <p className="text-sm" style={{ color: colors.textSecondary }}>
            Install the gig pulse for a better experience
          </p>
        </div>

        <div className="space-y-4 mb-8">
          {benefits.map((benefit, idx) => (
            <div 
              key={idx}
              className="flex items-center gap-4 p-4 rounded-xl"
              style={{ backgroundColor: colors.surface }}
            >
              <div 
                className="w-12 h-12 rounded-full flex items-center justify-center"
                style={{ backgroundColor: colors.accent + '20' }}
              >
                <benefit.icon size={24} style={{ color: colors.accent }} />
              </div>
              <div>
                <h3 className="font-semibold" style={{ color: colors.text }}>{benefit.title}</h3>
                <p className="text-sm" style={{ color: colors.textSecondary }}>{benefit.description}</p>
              </div>
            </div>
          ))}
        </div>

        {isInstalled ? (
          <div className="text-center p-6 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <IoCheckmarkCircle size={48} className="mx-auto mb-3 text-green-500" />
            <h3 className="text-lg font-bold mb-1" style={{ color: colors.text }}>Already Installed!</h3>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              You're all set. Enjoy the app!
            </p>
          </div>
        ) : isInstallable ? (
          <button
            onClick={promptInstall}
            className="w-full py-4 rounded-2xl font-bold text-lg"
            style={{ backgroundColor: colors.accent, color: '#0F172A' }}
          >
            Install Now
          </button>
        ) : (
          <div className="text-center p-6 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <h3 className="text-lg font-bold mb-2" style={{ color: colors.text }}>How to Install</h3>
            <p className="text-sm mb-4" style={{ color: colors.textSecondary }}>
              On iOS: Tap the share button and select "Add to Home Screen"
            </p>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              On Android: Tap the menu and select "Install app" or "Add to Home screen"
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PWABenefits;
