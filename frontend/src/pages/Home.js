import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoPlayCircle, IoNewspaper, IoBagCheck, IoGrid, IoChevronForward } from 'react-icons/io5';

const Home = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();

  const sections = [
    {
      title: 'Curated Videos',
      description: 'Tips from top creators',
      icon: IoPlayCircle,
      route: '/content',
      color: '#EF4444',
    },
    {
      title: 'News Feed',
      description: 'Stay in the know',
      icon: IoNewspaper,
      route: '/news',
      color: '#3B82F6',
    },
    {
      title: 'Driver Essentials',
      description: 'Gear that works',
      icon: IoBagCheck,
      route: '/essentials',
      color: '#22C55E',
    },
    {
      title: 'Apps & Tools',
      description: 'Maximize earnings',
      icon: IoGrid,
      route: '/apps',
      color: '#F59E0B',
    },
  ];

  return (
    <div className="p-4" style={{ backgroundColor: colors.background }}>
      {/* Hero Section */}
      <div className="text-center mt-4 mb-5">
        <h1 className="text-2xl font-bold tracking-wide" style={{ color: colors.accent }}>
          Educate. Elevate. Motivate.
        </h1>
        <p className="text-sm mt-2 font-medium" style={{ color: colors.textSecondary }}>
          for rideshare, delivery & shopping
        </p>
      </div>

      {/* Welcome Card */}
      <div 
        className="p-4 rounded-2xl mb-5"
        style={{ backgroundColor: colors.surface }}
      >
        <h2 className="text-lg font-bold mb-1" style={{ color: colors.text }}>
          Welcome to the gig pulse
        </h2>
        <p className="text-sm leading-relaxed" style={{ color: colors.textSecondary }}>
          Your daily boost for smarter shifts and bigger wins. Let's go!
        </p>
      </div>

      {/* Section Cards */}
      <div className="space-y-3">
        {sections.map((section, index) => (
          <button
            key={index}
            className="w-full flex items-center gap-4 p-4 rounded-2xl transition-opacity hover:opacity-90"
            style={{ backgroundColor: colors.surface }}
            onClick={() => navigate(section.route)}
            data-testid={`home-card-${section.title.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <div 
              className="w-14 h-14 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: section.color + '20' }}
            >
              <section.icon size={32} color={section.color} />
            </div>
            <div className="flex-1 text-left">
              <h3 className="text-base font-bold" style={{ color: colors.text }}>
                {section.title}
              </h3>
              <p className="text-sm" style={{ color: colors.textSecondary }}>
                {section.description}
              </p>
            </div>
            <IoChevronForward size={20} style={{ color: colors.textSecondary }} />
          </button>
        ))}
      </div>
    </div>
  );
};

export default Home;
