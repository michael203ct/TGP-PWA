import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoArrowBack, IoCar, IoStar, IoArrowForward } from 'react-icons/io5';

const topGearPicks = [
  {
    id: 1,
    name: 'REDTIGER F17 4K Dash Cam',
    description: '3 Channel, 5GHz WiFi, GPS, 64GB Card Included',
    price: '$179.99',
    rating: '4.5',
    image: 'https://customer-assets.emergentagent.com/job_gig-essentials-hub/artifacts/bvstr1hk_f1.jpg',
    url: 'https://www.amazon.com/dp/B0CSPBJ2HM?tag=thegigpulse-20'
  },
  {
    id: 2,
    name: 'Fanttik Slim V8 APEX Car Vacuum',
    description: '19000Pa Cordless, 4-in-1, Type-C Charging',
    price: '$65.99',
    rating: '4.7',
    image: 'https://customer-assets.emergentagent.com/job_gig-essentials-hub/artifacts/5vi8o56r_f2.jpg',
    url: 'https://www.amazon.com/dp/B0CQYTNNW7?tag=thegigpulse-20'
  },
  {
    id: 3,
    name: 'iOttie Easy One Touch Signature',
    description: 'Dashboard & Windshield Phone Mount',
    price: '$24.95',
    rating: '4.6',
    image: 'https://customer-assets.emergentagent.com/job_gig-essentials-hub/artifacts/7ric738l_f3.jpg',
    url: 'https://www.amazon.com/dp/B0875RKTQF?tag=thegigpulse-20'
  }
];

const DriverEssentials = () => {
  const { colors } = useTheme();
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
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Top Gear Picks</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <div className="text-center mb-6">
          <IoCar size={48} style={{ color: colors.accent }} className="mx-auto mb-3" />
          <h2 className="text-xl font-bold mb-2" style={{ color: colors.text }}>
            Driver-Tested Essentials
          </h2>
          <p className="text-sm" style={{ color: colors.textSecondary }}>
            Gear that makes every shift better
          </p>
        </div>

        <div className="space-y-4">
          {topGearPicks.map((item) => (
            <div 
              key={item.id}
              className="p-4 rounded-xl border"
              style={{ backgroundColor: colors.surface, borderColor: colors.cardBorder }}
            >
              <div className="flex gap-4">
                <div className="w-24 h-24 bg-white rounded-lg p-2 flex-shrink-0">
                  <img 
                    src={item.image} 
                    alt={item.name}
                    className="w-full h-full object-contain"
                  />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1" style={{ color: colors.text }}>{item.name}</h3>
                  <p className="text-xs mb-2" style={{ color: colors.textSecondary }}>{item.description}</p>
                  <div className="flex items-center gap-1 mb-2">
                    <IoStar size={14} color="#FFB800" />
                    <span className="text-sm" style={{ color: colors.text }}>{item.rating}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold" style={{ color: colors.accent }}>{item.price}</span>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ backgroundColor: colors.accent, color: '#0F172A' }}
                    >
                      Shop <IoArrowForward size={14} />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-center mt-6 italic" style={{ color: colors.textSecondary }}>
          Affiliate links may earn us a commission at no extra cost to you.
        </p>
      </div>
    </div>
  );
};

export default DriverEssentials;
