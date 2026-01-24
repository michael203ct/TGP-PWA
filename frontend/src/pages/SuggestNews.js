import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoArrowBack, IoCheckmarkCircle } from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const SuggestNews = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [type, setType] = useState('website');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !url.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/suggestions/news`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), url: url.trim(), type }),
      });

      if (response.ok) {
        setSubmitted(true);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to submit. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div style={{ backgroundColor: colors.background }} className="min-h-screen">
        <header className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: colors.border }}>
          <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center">
            <IoArrowBack size={24} style={{ color: colors.text }} />
          </button>
          <h1 className="text-lg font-bold" style={{ color: colors.text }}>Suggest a News Site</h1>
          <div className="w-10"></div>
        </header>
        <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
          <IoCheckmarkCircle size={64} className="text-green-500 mb-4" />
          <h2 className="text-xl font-bold mb-2" style={{ color: colors.text }}>Thanks for the suggestion!</h2>
          <p className="text-sm mb-6" style={{ color: colors.textSecondary }}>We'll review it and add it if it's a good fit.</p>
          <button onClick={() => navigate(-1)} className="px-6 py-3 rounded-full font-semibold" style={{ backgroundColor: colors.accent, color: '#0F172A' }}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.background }} className="min-h-screen">
      <header className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: colors.border }}>
        <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center">
          <IoArrowBack size={24} style={{ color: colors.text }} />
        </button>
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Suggest a News Site</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <p className="text-sm mb-6" style={{ color: colors.textSecondary }}>
          Know a great source for gig economy news? Let us know!
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>Site Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., The Rideshare Guy"
              className="w-full h-12 px-4 rounded-xl border outline-none"
              style={{ backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full h-12 px-4 rounded-xl border outline-none"
              style={{ backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>Type</label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setType('website')}
                className={`flex-1 py-3 rounded-xl font-semibold text-sm ${type === 'website' ? '' : 'opacity-60'}`}
                style={{ backgroundColor: type === 'website' ? colors.accent : colors.surface, color: type === 'website' ? '#0F172A' : colors.text }}
              >
                Website
              </button>
              <button
                type="button"
                onClick={() => setType('twitter')}
                className={`flex-1 py-3 rounded-xl font-semibold text-sm ${type === 'twitter' ? '' : 'opacity-60'}`}
                style={{ backgroundColor: type === 'twitter' ? colors.accent : colors.surface, color: type === 'twitter' ? '#0F172A' : colors.text }}
              >
                X / Twitter
              </button>
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 rounded-full font-semibold"
            style={{ backgroundColor: colors.accent, color: '#0F172A' }}
          >
            {submitting ? 'Submitting...' : 'Submit Suggestion'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SuggestNews;
