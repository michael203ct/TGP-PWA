import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoAdd, IoPlayCircle, IoCloudOffline, IoNewspaper } from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const categories = ['All', 'Rideshare', 'Delivery', 'Shopping'];

const isShowLive = (schedule) => {
  const now = new Date();
  const currentDay = now.getDay();
  const currentHour = now.getHours();
  
  const scheduleLower = schedule.toLowerCase();
  let showDay = -1;
  let showHour = -1;
  
  if (scheduleLower.includes('monday')) showDay = 1;
  else if (scheduleLower.includes('tuesday')) showDay = 2;
  else if (scheduleLower.includes('wednesday')) showDay = 3;
  else if (scheduleLower.includes('thursday')) showDay = 4;
  else if (scheduleLower.includes('friday')) showDay = 5;
  else if (scheduleLower.includes('saturday')) showDay = 6;
  else if (scheduleLower.includes('sunday')) showDay = 0;
  
  const timeMatch = schedule.match(/(\d+)(am|pm)/i);
  if (timeMatch) {
    let hour = parseInt(timeMatch[1]);
    if (timeMatch[2].toLowerCase() === 'pm' && hour !== 12) hour += 12;
    if (timeMatch[2].toLowerCase() === 'am' && hour === 12) hour = 0;
    showHour = hour;
  }
  
  if (showDay === currentDay && showHour !== -1) {
    const estOffset = -5;
    const userOffset = -now.getTimezoneOffset() / 60;
    const adjustedShowHour = showHour + (userOffset - estOffset);
    if (currentHour >= adjustedShowHour && currentHour < adjustedShowHour + 2) {
      return true;
    }
  }
  return false;
};

const News = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(true);
  const [news, setNews] = useState([]);
  const [weeklyShows, setWeeklyShows] = useState([]);
  const [error, setError] = useState(null);

  const fetchWeeklyShows = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/static-content/weekly-shows`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setWeeklyShows(data.data);
        }
      }
    } catch (err) {
      console.error('Error fetching weekly shows:', err);
    }
  }, []);

  const fetchNews = useCallback(async (forceRefresh = false) => {
    try {
      setError(null);
      const categoryParam = selectedCategory === 'All' ? '' : `&category=${selectedCategory.toLowerCase()}`;
      const response = await fetch(
        `${API_URL}/api/news/feed?limit=30${categoryParam}${forceRefresh ? '&force_refresh=true' : ''}`
      );
      
      if (!response.ok) throw new Error('Failed to fetch news');
      
      const data = await response.json();
      if (data.success && data.data) {
        setNews(data.data);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Unable to load news. Pull to refresh.');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory]);

  useEffect(() => {
    setLoading(true);
    fetchNews();
    fetchWeeklyShows();
  }, [selectedCategory, fetchNews, fetchWeeklyShows]);

  const getDayBadge = (schedule) => {
    if (schedule.includes('Monday')) return 'MON';
    if (schedule.includes('Tuesday')) return 'TUE';
    if (schedule.includes('Wednesday')) return 'WED';
    return 'LIVE';
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    return 'Just now';
  };

  const getCategoryColor = (cat) => {
    switch (cat?.toLowerCase()) {
      case 'rideshare': return '#3B82F6';
      case 'delivery': return '#22C55E';
      case 'shopping': return '#F59E0B';
      default: return colors.accent;
    }
  };

  return (
    <div className="p-4" style={{ backgroundColor: colors.background }}>
      {/* Weekly Shows Section */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-0.5" style={{ color: colors.text }}>Weekly Shows</h2>
        <p className="text-xs mb-3" style={{ color: colors.textSecondary }}>
          Long-form lives & discussions every week
        </p>

        <div className="grid grid-cols-3 gap-2.5">
          {weeklyShows.slice(0, 3).map((show) => {
            const isLive = isShowLive(show.schedule);
            
            return (
              <a
                key={show.id}
                href={show.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl overflow-hidden hover:opacity-90 transition-opacity"
                style={{ backgroundColor: colors.surface }}
                data-testid={`weekly-show-${show.id}`}
              >
                <div className="relative h-[90px] bg-slate-800">
                  <img 
                    src={show.thumbnail} 
                    alt={show.name}
                    className="w-full h-full object-cover"
                  />
                  <div 
                    className="absolute top-1 left-1 px-2 py-0.5 rounded text-[10px] font-bold"
                    style={{ backgroundColor: colors.accent, color: '#0F172A' }}
                  >
                    {getDayBadge(show.schedule)}
                  </div>
                  {isLive && (
                    <div className="absolute top-1 right-1 px-1.5 py-0.5 rounded flex items-center gap-1 bg-red-500">
                      <div className="w-1.5 h-1.5 rounded-full bg-white"></div>
                      <span className="text-[9px] font-extrabold text-white tracking-wide">LIVE</span>
                    </div>
                  )}
                  <div className="absolute inset-0 flex items-center justify-center bg-black/25">
                    <IoPlayCircle size={24} color="#fff" />
                  </div>
                </div>
                <div className="p-2">
                  <p className="text-xs font-semibold line-clamp-2 leading-tight mb-0.5" style={{ color: colors.text }}>
                    {show.name}
                  </p>
                  <p className="text-[11px] font-medium mb-0.5" style={{ color: colors.accent }}>
                    {show.creator}
                  </p>
                  <p className="text-[10px]" style={{ color: colors.textSecondary }}>
                    {show.schedule}
                  </p>
                  <p className="text-[9px]" style={{ color: colors.textSecondary }}>
                    {show.duration} • 🎧 friendly
                  </p>
                </div>
              </a>
            );
          })}
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap transition-colors ${
              selectedCategory === cat ? '' : 'opacity-70 hover:opacity-100'
            }`}
            style={{ 
              backgroundColor: selectedCategory === cat ? colors.accent : colors.surface,
              color: selectedCategory === cat ? '#0F172A' : colors.text
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* News Feed Section */}
      <div className="mb-4">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
          <h2 className="text-xl font-bold" style={{ color: colors.text }}>Latest News</h2>
          <button
            onClick={() => navigate('/suggest-news')}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border text-xs font-semibold"
            style={{ borderColor: colors.border, color: colors.accent }}
            data-testid="suggest-news-btn"
          >
            <IoAdd size={14} />
            Suggest a Site
          </button>
        </div>

        {loading ? (
          <div className="py-10 flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-t-transparent" style={{ borderColor: colors.accent, borderTopColor: 'transparent' }}></div>
            <p className="mt-3 text-sm" style={{ color: colors.textSecondary }}>Loading news...</p>
          </div>
        ) : error ? (
          <div className="py-10 flex flex-col items-center">
            <IoCloudOffline size={48} style={{ color: colors.textSecondary }} />
            <p className="mt-3 text-sm text-center" style={{ color: colors.textSecondary }}>{error}</p>
          </div>
        ) : news.length === 0 ? (
          <div className="py-10 flex flex-col items-center">
            <IoNewspaper size={48} style={{ color: colors.textSecondary }} />
            <p className="mt-3 text-sm text-center" style={{ color: colors.textSecondary }}>
              No news found for this category
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {news.map((article) => (
              <a
                key={article.id}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-xl overflow-hidden p-3 hover:opacity-90 transition-opacity"
                style={{ backgroundColor: colors.card }}
                data-testid={`news-card-${article.id}`}
              >
                <div className="flex gap-3">
                  {article.thumbnail && (
                    <img 
                      src={article.thumbnail} 
                      alt=""
                      className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                    />
                  )}
                  <div className={`flex-1 ${!article.thumbnail ? '' : ''}`}>
                    {article.category && (
                      <span 
                        className="inline-block px-1.5 py-0.5 rounded text-[9px] font-bold text-white mb-1.5"
                        style={{ backgroundColor: getCategoryColor(article.category) }}
                      >
                        {article.category.toUpperCase()}
                      </span>
                    )}
                    <h3 className="text-sm font-semibold line-clamp-2 leading-tight mb-1.5" style={{ color: colors.text }}>
                      {article.title}
                    </h3>
                    <p className="text-xs line-clamp-2 leading-relaxed mb-2" style={{ color: colors.textSecondary }}>
                      {article.snippet}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-medium" style={{ color: colors.accent }}>
                        {article.source}
                      </span>
                      <span className="text-[10px]" style={{ color: colors.textSecondary }}>
                        {formatTimeAgo(article.published_at)}
                      </span>
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default News;
