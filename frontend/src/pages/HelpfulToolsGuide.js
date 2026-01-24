import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoArrowBack, IoAnalytics, IoSpeedometer, IoCalculator, IoSwapHorizontal, IoArrowForward } from 'react-icons/io5';

const tools = [
  {
    id: 'gridwise',
    name: 'Gridwise',
    icon: IoAnalytics,
    color: '#4A90D9',
    description: 'Track your earnings across all gig platforms. See detailed analytics, track mileage, and optimize your schedule.',
    url: 'https://gridwise.io/'
  },
  {
    id: 'everlance',
    name: 'Everlance',
    icon: IoSpeedometer,
    color: '#00C7B7',
    description: 'Automatic mileage tracking and expense management. Essential for tax deductions.',
    url: 'https://www.everlance.com/'
  },
  {
    id: 'stride',
    name: 'Stride',
    icon: IoCalculator,
    color: '#5271FF',
    description: 'Find tax deductions you might be missing. Health insurance marketplace for gig workers.',
    url: 'https://www.stridehealth.com/'
  },
  {
    id: 'para',
    name: 'Para',
    icon: IoSwapHorizontal,
    color: '#6366F1',
    description: 'Multi-app driver assistant that shows earnings before accepting. Compare offers across platforms.',
    url: 'https://www.joinpara.com/'
  }
];

const HelpfulToolsGuide = () => {
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
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Helpful Tools Guide</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold mb-2" style={{ color: colors.text }}>
            Tools Every Gig Worker Needs
          </h2>
          <p className="text-sm" style={{ color: colors.textSecondary }}>
            Maximize your earnings and simplify your taxes
          </p>
        </div>

        <div className="space-y-4">
          {tools.map((tool) => (
            <div 
              key={tool.id}
              className="p-4 rounded-xl"
              style={{ backgroundColor: colors.surface }}
            >
              <div className="flex items-start gap-4">
                <div 
                  className="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: tool.color + '20' }}
                >
                  <tool.icon size={28} color={tool.color} />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold mb-1" style={{ color: colors.text }}>{tool.name}</h3>
                  <p className="text-sm leading-relaxed mb-3" style={{ color: colors.textSecondary }}>
                    {tool.description}
                  </p>
                  <a
                    href={tool.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-semibold"
                    style={{ backgroundColor: colors.accent, color: '#0F172A' }}
                  >
                    Learn More <IoArrowForward size={16} />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-center mt-6 italic" style={{ color: colors.textSecondary }}>
          Links may include referral codes – we may earn a small reward at no extra cost to you.
        </p>
      </div>
    </div>
  );
};

export default HelpfulToolsGuide;
