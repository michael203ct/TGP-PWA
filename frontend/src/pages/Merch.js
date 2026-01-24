import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { IoShirt, IoCar, IoHeart, IoGift, IoArrowForward } from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const Merch = () => {
  const { colors } = useTheme();
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [error, setError] = useState('');

  const handleSubscribe = async () => {
    if (!email.trim()) {
      setError('Please enter your email address.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    setSubmitting(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), list_type: 'merch' }),
      });
      
      if (response.ok) {
        setSubscribed(true);
        setEmail('');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Something went wrong. Try again.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-140px)] p-6" style={{ backgroundColor: colors.background }}>
      <div 
        className="w-[120px] h-[120px] rounded-full flex items-center justify-center mb-6"
        style={{ backgroundColor: colors.surface }}
      >
        <IoShirt size={64} style={{ color: colors.accent }} />
      </div>
      
      <h1 className="text-3xl font-bold mb-1" style={{ color: colors.text }}>Merch Store</h1>
      <p className="text-lg font-semibold mb-4" style={{ color: colors.accent }}>Coming Soon</p>
      
      <p className="text-sm text-center leading-relaxed mb-6 max-w-[300px]" style={{ color: colors.textSecondary }}>
        Rep the gig pulse with exclusive gear designed for drivers, by drivers.
      </p>
      
      <div className="space-y-3.5 mb-7">
        <div className="flex items-center gap-3">
          <IoCar size={24} style={{ color: colors.accent }} />
          <span className="text-sm font-medium" style={{ color: colors.text }}>Driver-Focused Designs</span>
        </div>
        <div className="flex items-center gap-3">
          <IoHeart size={24} style={{ color: colors.accent }} />
          <span className="text-sm font-medium" style={{ color: colors.text }}>Community Voted Styles</span>
        </div>
        <div className="flex items-center gap-3">
          <IoGift size={24} style={{ color: colors.accent }} />
          <span className="text-sm font-medium" style={{ color: colors.text }}>Exclusive Drops</span>
        </div>
      </div>
      
      {/* Email Signup Section */}
      <div 
        className="w-full max-w-[340px] p-5 rounded-2xl border"
        style={{ backgroundColor: colors.surface, borderColor: colors.border }}
      >
        {subscribed ? (
          <div className="text-center py-2">
            <div className="text-green-500 text-3xl mb-2.5">✓</div>
            <p className="text-lg font-semibold mt-2.5" style={{ color: colors.text }}>You're on the list!</p>
            <p className="text-sm mt-1" style={{ color: colors.textSecondary }}>
              We'll notify you when merch drops.
            </p>
          </div>
        ) : (
          <>
            <h3 className="text-lg font-bold text-center mb-1.5" style={{ color: colors.text }}>
              Get Notified First
            </h3>
            <p className="text-sm text-center mb-4" style={{ color: colors.textSecondary }}>
              Be the first to know when we drop new merch.
            </p>
            
            <div className="flex gap-2.5 mb-2.5">
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 h-12 px-3.5 rounded-xl border text-sm outline-none"
                style={{ 
                  backgroundColor: colors.background, 
                  color: colors.text,
                  borderColor: colors.border 
                }}
              />
              <button
                onClick={handleSubscribe}
                disabled={submitting}
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: colors.accent }}
              >
                {submitting ? (
                  <div className="animate-spin w-5 h-5 border-2 rounded-full border-t-transparent" style={{ borderColor: '#0F172A', borderTopColor: 'transparent' }}></div>
                ) : (
                  <IoArrowForward size={20} color="#0F172A" />
                )}
              </button>
            </div>
            
            {error && (
              <p className="text-xs text-red-500 text-center mb-2">{error}</p>
            )}
            
            <p className="text-[11px] text-center" style={{ color: colors.textSecondary }}>
              No spam. Unsubscribe anytime.
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default Merch;
