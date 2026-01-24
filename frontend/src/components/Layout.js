import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { 
  IoHome, IoPlayCircle, IoNewspaper, IoBagCheck, IoGrid, IoShirt,
  IoSunny, IoMoon, IoMenu, IoClose, IoSettings, IoPerson, IoCar,
  IoApps, IoDownload 
} from 'react-icons/io5';

const Layout = () => {
  const { colors, mode, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const tabs = [
    { path: '/content', label: 'Content', icon: IoPlayCircle },
    { path: '/news', label: 'News Feed', icon: IoNewspaper },
    { path: '/essentials', label: 'Essentials', icon: IoBagCheck },
    { path: '/apps', label: 'Apps', icon: IoGrid },
    { path: '/merch', label: 'Merch', icon: IoShirt, dimmed: true },
  ];

  const menuItems = [
    { icon: IoSettings, label: 'Settings', path: '/settings' },
    { icon: IoPerson, label: 'Profile', path: '/profile-page' },
    { icon: IoCar, label: 'Top Gear Picks', path: '/driver-essentials' },
    { icon: IoApps, label: 'Helpful Tools Guide', path: '/helpful-tools-guide' },
    { icon: IoShirt, label: 'Merch', path: '/merch', suffix: 'soon' },
    { icon: IoDownload, label: 'Install App', path: '/pwa-benefits' },
  ];

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: colors.background }}>
      {/* Header */}
      <header 
        className="sticky top-0 z-50 px-4 py-3 flex items-center justify-between border-b"
        style={{ backgroundColor: colors.background, borderColor: colors.border }}
      >
        <button 
          onClick={() => navigate('/')} 
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          data-testid="home-button"
        >
          <IoHome size={22} style={{ color: colors.accent }} />
          <span className="font-bold text-lg" style={{ color: colors.text }}>
            the gig pulse
          </span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg"
            style={{ backgroundColor: colors.surface }}
            data-testid="theme-toggle"
          >
            {mode === 'dark' ? (
              <IoSunny size={20} style={{ color: colors.accent }} />
            ) : (
              <IoMoon size={20} style={{ color: colors.accent }} />
            )}
          </button>

          <button
            onClick={() => setMenuOpen(true)}
            className="p-2 rounded-lg"
            style={{ backgroundColor: colors.surface }}
            data-testid="menu-button"
          >
            <IoMenu size={22} style={{ color: colors.text }} />
          </button>
        </div>
      </header>

      {/* Menu Modal */}
      {menuOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/50"
          onClick={() => setMenuOpen(false)}
        >
          <div 
            className="absolute right-4 top-16 rounded-xl shadow-2xl min-w-[180px]"
            style={{ backgroundColor: colors.surface }}
            onClick={(e) => e.stopPropagation()}
          >
            {menuItems.map((item, idx) => (
              <button
                key={idx}
                className="w-full flex items-center gap-3 px-4 py-3 hover:opacity-80 transition-opacity border-b last:border-b-0"
                style={{ borderColor: colors.border }}
                onClick={() => {
                  setMenuOpen(false);
                  navigate(item.path);
                }}
                data-testid={`menu-item-${item.label.toLowerCase().replace(' ', '-')}`}
              >
                <item.icon 
                  size={20} 
                  style={{ color: item.suffix === 'soon' ? colors.textSecondary : colors.accent }} 
                />
                <span 
                  className="flex-1 text-left font-medium"
                  style={{ color: item.suffix === 'soon' ? colors.textSecondary : colors.text }}
                >
                  {item.label}
                </span>
                {item.suffix === 'soon' && (
                  <span 
                    className="text-xs px-2 py-0.5 rounded-md"
                    style={{ backgroundColor: colors.border, color: colors.textSecondary }}
                  >
                    soon
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 pb-20">
        <Outlet />
      </main>

      {/* Bottom Tab Bar */}
      <nav 
        className="fixed bottom-0 left-0 right-0 border-t flex justify-around py-2 pb-safe"
        style={{ backgroundColor: colors.surface, borderColor: colors.border }}
      >
        {tabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) => 
              `flex flex-col items-center gap-1 px-3 py-1 ${tab.dimmed ? 'opacity-50' : ''}`
            }
          >
            {({ isActive }) => (
              <>
                <tab.icon 
                  size={24} 
                  style={{ color: isActive ? colors.accent : colors.textSecondary }} 
                />
                <span 
                  className="text-xs font-semibold"
                  style={{ color: isActive ? colors.accent : colors.textSecondary }}
                >
                  {tab.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
};

export default Layout;
