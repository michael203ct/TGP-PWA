import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { 
  IoAdd, IoChevronForward, IoClose, IoCheckmarkCircle, IoArrowForward,
  IoCar, IoCarSport, IoFastFood, IoRestaurant, IoCart, IoFlash, IoCube, 
  IoBagHandle, IoNavigate, IoBicycle, IoAnalytics, IoSpeedometer, IoSwapHorizontal, IoApps
} from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const iconMap = {
  'car': IoCar,
  'car-sport': IoCarSport,
  'fast-food': IoFastFood,
  'restaurant': IoRestaurant,
  'cart': IoCart,
  'cube': IoCube,
  'flash': IoFlash,
  'bag-handle': IoBagHandle,
  'bicycle': IoBicycle,
  'navigate': IoNavigate,
  'analytics': IoAnalytics,
  'speedometer': IoSpeedometer,
  'swap-horizontal': IoSwapHorizontal,
};

const Apps = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const [selectedApp, setSelectedApp] = useState(null);
  const [gigApps, setGigApps] = useState([]);
  const [helpfulTools, setHelpfulTools] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [appsRes, toolsRes] = await Promise.all([
        fetch(`${API_URL}/api/static-content/gig-apps`),
        fetch(`${API_URL}/api/static-content/helpful-tools`)
      ]);
      
      if (appsRes.ok) {
        const data = await appsRes.json();
        if (data.success && data.data) setGigApps(data.data);
      }
      
      if (toolsRes.ok) {
        const data = await toolsRes.json();
        if (data.success && data.data) setHelpfulTools(data.data);
      }
    } catch (err) {
      console.error('Error fetching apps data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getIcon = (iconName) => iconMap[iconName] || IoApps;

  // Reorder apps
  const orderedApps = [...gigApps].sort((a, b) => {
    const order = {
      'Uber': 1, 'Uber Eats': 2, 'Lyft': 3, 'DoorDash': 4, 'Grubhub': 5,
      'Instacart': 6, 'Spark': 7, 'Amazon Flex': 8, 'Shipt': 9, 'Roadie': 10
    };
    return (order[a.name] || 99) - (order[b.name] || 99);
  });

  return (
    <div className="p-4" style={{ backgroundColor: colors.background }}>
      {/* Gig Apps Section */}
      <div className="mb-6">
        <h2 className="text-lg font-bold mb-1" style={{ color: colors.text }}>Get Started – Gig Apps</h2>
        <p className="text-xs mb-3.5" style={{ color: colors.textSecondary }}>
          Tap any app to learn more and sign up
        </p>

        <div className="grid grid-cols-5 gap-2">
          {orderedApps.slice(0, 10).map((app) => {
            const IconComponent = getIcon(app.icon);
            return (
              <button
                key={app.id}
                onClick={() => setSelectedApp(app)}
                className="flex flex-col items-center p-1 rounded-xl border aspect-[0.85]"
                style={{ backgroundColor: colors.surface, borderColor: colors.cardBorder }}
                data-testid={`gig-app-${app.id}`}
              >
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-1"
                  style={{ backgroundColor: app.color + '20' }}
                >
                  <IconComponent size={24} color={app.color} />
                </div>
                <span className="text-[10px] font-semibold text-center line-clamp-1" style={{ color: colors.text }}>
                  {app.name}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Helpful Tools Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3.5">
          <h2 className="text-lg font-bold" style={{ color: colors.text }}>Other Helpful Tools</h2>
          <button
            onClick={() => navigate('/suggest-app')}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border text-xs font-semibold"
            style={{ borderColor: colors.border, color: colors.accent }}
            data-testid="suggest-app-btn"
          >
            <IoAdd size={14} />
            Suggest an App
          </button>
        </div>
        
        <div className="space-y-2.5">
          {helpfulTools.map((tool) => {
            const IconComponent = getIcon(tool.icon);
            return (
              <button
                key={tool.id}
                onClick={() => setSelectedApp(tool)}
                className="w-full flex items-center gap-3.5 p-4 rounded-xl border min-h-[100px]"
                style={{ backgroundColor: colors.surface, borderColor: colors.cardBorder }}
                data-testid={`tool-${tool.id}`}
              >
                <div 
                  className="w-[60px] h-[60px] rounded-2xl flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: tool.color + '20' }}
                >
                  <IconComponent size={32} color={tool.color} />
                </div>
                <div className="flex-1 text-left">
                  <p className="text-base font-semibold mb-1" style={{ color: colors.text }}>{tool.name}</p>
                  <p className="text-sm line-clamp-3 leading-relaxed" style={{ color: colors.textSecondary }}>
                    {tool.description}
                  </p>
                </div>
                <IoChevronForward size={20} style={{ color: colors.textSecondary }} />
              </button>
            );
          })}
        </div>
      </div>

      <p className="text-[10px] text-center italic mt-2" style={{ color: colors.textSecondary }}>
        Links may include referral codes – we may earn a small reward at no extra cost to you.
      </p>

      {/* App Detail Modal */}
      {selectedApp && (
        <div 
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-6"
          onClick={() => setSelectedApp(null)}
        >
          <div 
            className="w-full max-w-[360px] rounded-2xl p-6 text-center"
            style={{ backgroundColor: colors.surface }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-3.5 right-3.5 p-1"
              onClick={() => setSelectedApp(null)}
            >
              <IoClose size={24} style={{ color: colors.textSecondary }} />
            </button>

            <div 
              className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ backgroundColor: selectedApp.color + '20' }}
            >
              {React.createElement(getIcon(selectedApp.icon), { size: 48, color: selectedApp.color })}
            </div>

            <h3 className="text-xl font-bold mb-2" style={{ color: colors.text }}>{selectedApp.name}</h3>
            
            {selectedApp.description && (
              <p className="text-sm text-center leading-relaxed mb-4" style={{ color: colors.textSecondary }}>
                {selectedApp.description}
              </p>
            )}

            {selectedApp.features && selectedApp.features.length > 0 && (
              <div className="w-full mb-5 space-y-2">
                {selectedApp.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-left">
                    <IoCheckmarkCircle size={16} style={{ color: colors.accent }} />
                    <span className="text-sm flex-1" style={{ color: colors.text }}>{feature}</span>
                  </div>
                ))}
              </div>
            )}

            {selectedApp.url && (
              <a
                href={selectedApp.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setSelectedApp(null)}
                className="flex items-center justify-center gap-2 w-full py-3.5 px-7 rounded-full font-semibold"
                style={{ backgroundColor: colors.accent, color: '#0F172A' }}
              >
                Get Started
                <IoArrowForward size={18} />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Apps;
