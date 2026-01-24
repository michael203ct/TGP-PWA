import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { IoAdd, IoAlertCircle, IoVideocam, IoRefresh } from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const Content = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const [featuredChannels, setFeaturedChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFeaturedChannels = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/static-content/featured-channels`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setFeaturedChannels(data.data);
        }
      }
    } catch (err) {
      console.error('Error fetching featured channels:', err);
    }
  }, []);

  const filterVideos = (videoList) => {
    return videoList.filter(video => {
      const title = video.title.toLowerCase();
      if (title.includes('#shorts') || title.includes('#short')) return false;
      if (video.title.length < 10 && !video.description) return false;
      const channelName = video.channel_title;
      if (['Rideshare Rodeo', 'The Rideshare Guy', 'Rideshare Professor'].includes(channelName)) {
        return false;
      }
      return true;
    });
  };

  const fetchFeed = useCallback(async (forceRefresh = false) => {
    try {
      setError(null);
      const url = `${API_URL}/api/youtube/feed?max_per_channel=5${forceRefresh ? '&force_refresh=true' : ''}`;
      const response = await fetch(url);
      
      if (!response.ok) throw new Error('Failed to fetch videos');
      
      const data = await response.json();
      if (data.success) {
        const filteredVideos = filterVideos(data.data || []);
        setVideos(filteredVideos);
      } else {
        throw new Error(data.detail || 'Failed to load feed');
      }
    } catch (err) {
      console.error('Feed fetch error:', err);
      setError(err.message || 'Failed to load videos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
    fetchFeaturedChannels();
  }, [fetchFeed, fetchFeaturedChannels]);

  const formatViewCount = (count) => {
    const num = parseInt(count, 10);
    if (isNaN(num)) return count;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M views`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K views`;
    return `${num} views`;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]" style={{ backgroundColor: colors.background }}>
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-t-transparent" style={{ borderColor: colors.accent, borderTopColor: 'transparent' }}></div>
        <p className="mt-3 text-sm" style={{ color: colors.textSecondary }}>Loading gig content...</p>
      </div>
    );
  }

  return (
    <div className="p-4" style={{ backgroundColor: colors.background }}>
      {/* Featured Channels Section */}
      <div className="mb-5">
        <h2 className="text-lg font-bold mb-3" style={{ color: colors.text }}>Featured Channels</h2>
        <div className="grid grid-cols-3 gap-2.5">
          {featuredChannels.slice(0, 3).map((channel) => (
            <a
              key={channel.id}
              href={channel.channelUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl pt-4 pb-3 flex flex-col items-center hover:opacity-90 transition-opacity"
              style={{ backgroundColor: colors.surface }}
              data-testid={`featured-channel-${channel.id}`}
            >
              <img 
                src={channel.thumbnail} 
                alt={channel.name}
                className="w-16 h-16 rounded-full mb-2.5 object-cover"
              />
              <p className="text-xs font-semibold text-center px-2 truncate w-full" style={{ color: colors.text }}>
                {channel.name}
              </p>
              <p className="text-[11px] font-medium" style={{ color: colors.accent }}>
                {channel.tag || 'Gig tips & tricks'}
              </p>
              <p className="text-[10px]" style={{ color: colors.textSecondary }}>
                {channel.handle}
              </p>
            </a>
          ))}
        </div>
      </div>

      {/* Latest Videos Section */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-bold" style={{ color: colors.text }}>Latest Videos</h2>
          <button
            onClick={() => navigate('/suggest-channel')}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border text-xs font-semibold"
            style={{ borderColor: colors.border, color: colors.accent }}
            data-testid="suggest-channel-btn"
          >
            <IoAdd size={14} />
            Suggest a Channel
          </button>
        </div>

        {error ? (
          <div className="p-8 rounded-xl flex flex-col items-center" style={{ backgroundColor: colors.surface }}>
            <IoAlertCircle size={48} style={{ color: colors.textSecondary }} />
            <p className="mt-3 text-sm text-center" style={{ color: colors.textSecondary }}>{error}</p>
            <button 
              onClick={() => fetchFeed(true)}
              className="mt-4 px-6 py-2.5 rounded-full text-sm font-semibold"
              style={{ backgroundColor: colors.accent, color: '#0F172A' }}
            >
              Try Again
            </button>
          </div>
        ) : videos.length === 0 ? (
          <div className="p-8 rounded-xl flex flex-col items-center" style={{ backgroundColor: colors.surface }}>
            <IoVideocam size={48} style={{ color: colors.textSecondary }} />
            <p className="mt-3 text-sm text-center" style={{ color: colors.textSecondary }}>
              No videos available. Pull to refresh.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {videos.map((video) => (
              <a
                key={video.video_id}
                href={`https://www.youtube.com/watch?v=${video.video_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-xl overflow-hidden hover:opacity-90 transition-opacity"
                style={{ backgroundColor: colors.surface }}
              >
                <img 
                  src={video.thumbnail_high || video.thumbnail_medium || video.thumbnail}
                  alt={video.title}
                  className="w-full aspect-video object-cover"
                />
                <div className="p-3">
                  <h3 className="text-sm font-semibold line-clamp-2 mb-1" style={{ color: colors.text }}>
                    {video.title}
                  </h3>
                  <p className="text-xs" style={{ color: colors.textSecondary }}>
                    {video.channel_title} • {formatViewCount(video.view_count)}
                  </p>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Content;
