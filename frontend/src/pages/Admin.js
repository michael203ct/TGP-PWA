import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { 
  IoArrowBack, IoLockClosed, IoLogOut, IoApps, IoBagHandle, IoLogoYoutube, 
  IoNewspaper, IoMail, IoRefresh, IoCheckmarkCircle, IoClose
} from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';
const ADMIN_CODE = 'mrn320';

const Admin = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('apps');
  const [suggestions, setSuggestions] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [accessCode, setAccessCode] = useState('');
  const [isAuthed, setIsAuthed] = useState(false);

  const fetchSuggestions = useCallback(async () => {
    if (!isAuthed) return;
    
    setLoading(true);
    try {
      if (activeTab === 'emails') {
        const response = await fetch(`${API_URL}/api/subscribers`);
        if (response.ok) {
          const data = await response.json();
          setSubscribers(data.subscribers || []);
        }
      } else {
        const endpoint = activeTab === 'apps' ? 'app' : 
                         activeTab === 'gear' ? 'gear' :
                         activeTab === 'channels' ? 'channel' : 'news';
        
        const response = await fetch(`${API_URL}/api/suggestions/${endpoint}`);
        if (response.ok) {
          const data = await response.json();
          setSuggestions(data);
        }
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, isAuthed]);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleApprove = async (suggestion) => {
    if (!window.confirm(`Add "${suggestion.name}" to the main content?`)) return;
    
    try {
      const endpoint = activeTab === 'apps' ? 'app' : 
                       activeTab === 'gear' ? 'gear' :
                       activeTab === 'channels' ? 'channel' : 'news';
      
      const response = await fetch(`${API_URL}/api/suggestions/${endpoint}/${suggestion.id}/approve`, {
        method: 'POST',
      });
      
      if (response.ok) {
        alert('Suggestion approved and added to content!');
        fetchSuggestions();
      } else {
        alert('Failed to approve. Please try again.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  };

  const handleReject = async (suggestion) => {
    if (!window.confirm(`Remove "${suggestion.name}" from the queue?`)) return;
    
    try {
      const endpoint = activeTab === 'apps' ? 'app' : 
                       activeTab === 'gear' ? 'gear' :
                       activeTab === 'channels' ? 'channel' : 'news';
      
      const response = await fetch(`${API_URL}/api/suggestions/${endpoint}/${suggestion.id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        alert('Suggestion removed.');
        fetchSuggestions();
      } else {
        alert('Failed to remove. Please try again.');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    }
  };

  const handleLogin = () => {
    if (accessCode === ADMIN_CODE) {
      setIsAuthed(true);
    } else {
      alert('Invalid Code. Please enter the correct admin access code.');
    }
  };

  const tabs = [
    { key: 'apps', label: 'Apps', icon: IoApps },
    { key: 'gear', label: 'Gear', icon: IoBagHandle },
    { key: 'channels', label: 'Channels', icon: IoLogoYoutube },
    { key: 'news', label: 'News', icon: IoNewspaper },
    { key: 'emails', label: 'Emails', icon: IoMail },
  ];

  const pendingSuggestions = suggestions.filter(s => s.status === 'pending');

  if (!isAuthed) {
    return (
      <div style={{ backgroundColor: colors.background }} className="min-h-screen">
        <header 
          className="flex items-center justify-between px-4 py-3 border-b"
          style={{ borderColor: colors.border }}
        >
          <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center">
            <IoArrowBack size={24} style={{ color: colors.text }} />
          </button>
          <h1 className="text-lg font-bold" style={{ color: colors.text }}>Admin Access</h1>
          <div className="w-10"></div>
        </header>
        
        <div className="flex items-center justify-center min-h-[60vh] px-6">
          <div 
            className="w-full max-w-[320px] p-8 rounded-2xl text-center"
            style={{ backgroundColor: colors.surface }}
          >
            <IoLockClosed size={48} style={{ color: colors.accent }} className="mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2" style={{ color: colors.text }}>Admin Panel</h2>
            <p className="text-sm mb-6" style={{ color: colors.textSecondary }}>
              Enter access code to continue
            </p>
            
            <input
              type="password"
              placeholder="Access code"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
              className="w-full h-12 px-4 rounded-xl border text-base outline-none mb-4"
              style={{ 
                backgroundColor: colors.background, 
                color: colors.text, 
                borderColor: colors.border 
              }}
            />
            
            <button
              onClick={handleLogin}
              className="w-full h-12 rounded-full font-semibold"
              style={{ backgroundColor: colors.accent, color: '#0F172A' }}
            >
              Enter
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: colors.background }} className="min-h-screen">
      {/* Header */}
      <header 
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: colors.border }}
      >
        <button onClick={() => navigate(-1)} className="w-10 h-10 flex items-center justify-center">
          <IoArrowBack size={24} style={{ color: colors.text }} />
        </button>
        <h1 className="text-lg font-bold" style={{ color: colors.text }}>Admin Panel</h1>
        <button onClick={() => setIsAuthed(false)} className="w-10 h-10 flex items-center justify-center">
          <IoLogOut size={24} style={{ color: colors.textSecondary }} />
        </button>
      </header>

      {/* Tabs */}
      <div 
        className="flex border-b"
        style={{ backgroundColor: colors.surface, borderColor: colors.border }}
      >
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-3 border-b-2 ${
              activeTab === tab.key ? '' : 'border-transparent'
            }`}
            style={{ 
              borderColor: activeTab === tab.key ? colors.accent : 'transparent',
              color: activeTab === tab.key ? colors.accent : colors.textSecondary 
            }}
          >
            <tab.icon size={20} />
            <span className="text-sm font-semibold">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'emails' ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                {subscribers.length} subscriber{subscribers.length !== 1 ? 's' : ''}
              </span>
              <button onClick={fetchSuggestions}>
                <IoRefresh size={20} style={{ color: colors.accent }} />
              </button>
            </div>

            {loading ? (
              <div className="py-10 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-t-transparent" style={{ borderColor: colors.accent, borderTopColor: 'transparent' }}></div>
              </div>
            ) : subscribers.length === 0 ? (
              <div className="py-12 text-center">
                <IoMail size={48} style={{ color: colors.textSecondary }} className="mx-auto mb-3" />
                <p className="text-base" style={{ color: colors.textSecondary }}>No subscribers yet</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {subscribers.map((sub, idx) => (
                  <div 
                    key={idx}
                    className="p-3.5 rounded-xl border"
                    style={{ backgroundColor: colors.surface, borderColor: colors.border }}
                  >
                    <div className="flex items-center gap-2.5 mb-2">
                      <IoMail size={18} style={{ color: colors.accent }} />
                      <span className="text-sm font-medium" style={{ color: colors.text }}>{sub.email}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span 
                        className="px-2 py-0.5 rounded-lg text-[11px] font-semibold uppercase"
                        style={{ backgroundColor: colors.accent + '20', color: colors.accent }}
                      >
                        {sub.list_type}
                      </span>
                      <span className="text-xs" style={{ color: colors.textSecondary }}>
                        {new Date(sub.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                {pendingSuggestions.length} pending suggestion{pendingSuggestions.length !== 1 ? 's' : ''}
              </span>
              <button onClick={fetchSuggestions}>
                <IoRefresh size={20} style={{ color: colors.accent }} />
              </button>
            </div>

            {loading ? (
              <div className="py-10 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-t-transparent" style={{ borderColor: colors.accent, borderTopColor: 'transparent' }}></div>
              </div>
            ) : pendingSuggestions.length === 0 ? (
              <div className="py-12 text-center">
                <IoCheckmarkCircle size={48} style={{ color: colors.textSecondary }} className="mx-auto mb-3" />
                <p className="text-base" style={{ color: colors.textSecondary }}>No pending suggestions</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingSuggestions.map(suggestion => (
                  <div 
                    key={suggestion.id}
                    className="p-4 rounded-xl border"
                    style={{ backgroundColor: colors.surface, borderColor: colors.border }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold flex-1" style={{ color: colors.text }}>
                        {suggestion.name}
                      </h3>
                      {suggestion.category && (
                        <span 
                          className="px-2.5 py-1 rounded-xl text-xs font-semibold"
                          style={{ backgroundColor: colors.accent + '20', color: colors.accent }}
                        >
                          {suggestion.category}
                        </span>
                      )}
                    </div>
                    
                    {suggestion.description && (
                      <p className="text-sm line-clamp-3 mb-2 leading-relaxed" style={{ color: colors.textSecondary }}>
                        {suggestion.description}
                      </p>
                    )}
                    
                    {(suggestion.url || suggestion.link) && (
                      <p className="text-sm line-clamp-1 mb-2" style={{ color: colors.accent }}>
                        {suggestion.url || suggestion.link}
                      </p>
                    )}
                    
                    <p className="text-xs mb-3" style={{ color: colors.textSecondary }}>
                      {new Date(suggestion.created_at).toLocaleDateString()}
                    </p>
                    
                    <div className="flex gap-2.5">
                      <button
                        onClick={() => handleReject(suggestion)}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl border border-red-500"
                      >
                        <IoClose size={18} color="#EF4444" />
                        <span className="text-sm font-semibold text-red-500">Reject</span>
                      </button>
                      
                      <button
                        onClick={() => handleApprove(suggestion)}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-green-500"
                      >
                        <IoCheckmarkCircle size={18} color="#fff" />
                        <span className="text-sm font-semibold text-white">Approve</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Admin;
