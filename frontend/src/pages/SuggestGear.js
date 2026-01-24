import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoArrowBack, IoCheckmarkCircle } from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';
const categories = ['Rideshare', 'Delivery', 'Shopping'];

const SuggestGear = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Rideshare');
  const [description, setDescription] = useState('');
  const [link, setLink] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !description.trim()) {
      setError('Please fill in required fields');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/suggestions/gear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: name.trim(), 
          category: category.toLowerCase(), 
          description: description.trim(),
          link: link.trim() || null
        }),
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
          <h1 className="text-lg font-bold" style={{ color: colors.text }}>Suggest Gear</h1>
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
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Suggest Gear</h1>
        <div className="w-10"></div>
      </header>

      <div className="p-4">
        <p className="text-sm mb-6" style={{ color: colors.textSecondary }}>
          Found gear that makes gig work easier? Share it with the community!
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>Product Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Phone Mount Pro"
              className="w-full h-12 px-4 rounded-xl border outline-none"
              style={{ backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>Category</label>
            <div className="flex gap-2">
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  className={`flex-1 py-2 rounded-xl font-semibold text-sm ${category === cat ? '' : 'opacity-60'}`}
                  style={{ backgroundColor: category === cat ? colors.accent : colors.surface, color: category === cat ? '#0F172A' : colors.text }}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>Why You Recommend It *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What makes this product great for gig workers?"
              rows={4}
              className="w-full px-4 py-3 rounded-xl border outline-none resize-none"
              style={{ backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: colors.text }}>Product Link (optional)</label>
            <input
              type="url"
              value={link}
              onChange={(e) => setLink(e.target.value)}
              placeholder="https://amazon.com/..."
              className="w-full h-12 px-4 rounded-xl border outline-none"
              style={{ backgroundColor: colors.surface, color: colors.text, borderColor: colors.border }}
            />
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

export default SuggestGear;
