import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoArrowBack, IoPerson, IoMail, IoLocation, IoCar } from 'react-icons/io5';

const Profile = () => {
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
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Profile</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <div className="flex flex-col items-center mb-8">
          <div 
            className="w-24 h-24 rounded-full flex items-center justify-center mb-4"
            style={{ backgroundColor: colors.surface }}
          >
            <IoPerson size={48} style={{ color: colors.accent }} />
          </div>
          <h2 className="text-xl font-bold" style={{ color: colors.text }}>Gig Worker</h2>
          <p className="text-sm" style={{ color: colors.textSecondary }}>Member since 2024</p>
        </div>

        <div className="space-y-3">
          <div className="p-4 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <div className="flex items-center gap-4">
              <IoMail size={24} style={{ color: colors.accent }} />
              <div className="flex-1">
                <p className="font-semibold" style={{ color: colors.text }}>Email</p>
                <p className="text-sm" style={{ color: colors.textSecondary }}>Not set</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <div className="flex items-center gap-4">
              <IoLocation size={24} style={{ color: colors.accent }} />
              <div className="flex-1">
                <p className="font-semibold" style={{ color: colors.text }}>Location</p>
                <p className="text-sm" style={{ color: colors.textSecondary }}>United States</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl" style={{ backgroundColor: colors.surface }}>
            <div className="flex items-center gap-4">
              <IoCar size={24} style={{ color: colors.accent }} />
              <div className="flex-1">
                <p className="font-semibold" style={{ color: colors.text }}>Gig Types</p>
                <p className="text-sm" style={{ color: colors.textSecondary }}>Rideshare, Delivery</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm" style={{ color: colors.textSecondary }}>
            Profile features coming soon!
          </p>
        </div>
      </div>
    </div>
  );
};

export default Profile;
