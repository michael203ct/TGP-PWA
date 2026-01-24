import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useVoting } from '../contexts/VotingContext';
import { IoAdd, IoHeart, IoHeartOutline, IoStar, IoClose, IoArrowForward } from 'react-icons/io5';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';
const categories = ['All', 'Rideshare', 'Delivery', 'Shopping'];

const Essentials = () => {
  const { colors } = useTheme();
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [featuredGear, setFeaturedGear] = useState([]);
  const [communityGear, setCommunityGear] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedFeaturedItem, setSelectedFeaturedItem] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [featuredRes, communityRes] = await Promise.all([
        fetch(`${API_URL}/api/static-content/featured-gear`),
        fetch(`${API_URL}/api/static-content/community-favorites`)
      ]);
      
      if (featuredRes.ok) {
        const data = await featuredRes.json();
        if (data.success && data.data) setFeaturedGear(data.data);
      }
      
      if (communityRes.ok) {
        const data = await communityRes.json();
        if (data.success && data.data) setCommunityGear(data.data);
      }
    } catch (err) {
      console.error('Error fetching essentials data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredGear = communityGear.filter((item) => {
    if (item.category?.toLowerCase() === 'other') return false;
    if (selectedCategory === 'All') return true;
    if (item.categories && item.categories.length > 0) {
      return item.categories.some(c => c.toLowerCase() === selectedCategory.toLowerCase());
    }
    return item.category?.toLowerCase() === selectedCategory.toLowerCase();
  });

  return (
    <div className="p-4" style={{ backgroundColor: colors.background }}>
      {/* Featured Section */}
      <div className="mb-4">
        <h2 className="text-lg font-bold mb-3" style={{ color: colors.text }}>Featured</h2>
        <div className="grid grid-cols-3 gap-2.5">
          {featuredGear.slice(0, 3).map((item) => (
            <div
              key={item.id}
              className="rounded-xl overflow-hidden border"
              style={{ backgroundColor: colors.surface, borderColor: colors.cardBorder }}
              data-testid={`featured-gear-${item.id}`}
            >
              <button 
                onClick={() => setSelectedFeaturedItem(item)}
                className="w-full bg-white p-1.5 rounded-t-xl"
              >
                <img 
                  src={item.image} 
                  alt={item.name}
                  className="w-full h-[100px] object-contain rounded"
                />
              </button>
              <div className="p-2">
                <button onClick={() => setSelectedFeaturedItem(item)} className="text-left w-full">
                  <p className="text-[11px] font-semibold line-clamp-1 mb-0.5" style={{ color: colors.text }}>
                    {item.name}
                  </p>
                </button>
                <p className="text-[9px] line-clamp-1 mb-1.5" style={{ color: colors.textSecondary }}>
                  {item.blurb}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold" style={{ color: colors.accent }}>{item.price}</span>
                  <a
                    href={item.affiliateUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-2 py-1 rounded-lg text-[9px] font-semibold"
                    style={{ backgroundColor: colors.accent, color: '#0F172A' }}
                  >
                    Shop Now
                  </a>
                </div>
              </div>
            </div>
          ))}
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

      {/* Community Favorites */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2.5">
          <h2 className="text-lg font-bold" style={{ color: colors.text }}>Community Favorites</h2>
          <button
            onClick={() => navigate('/suggest-gear')}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border text-xs font-semibold"
            style={{ borderColor: colors.border, color: colors.accent }}
            data-testid="suggest-gear-btn"
          >
            <IoAdd size={14} />
            Suggest an Item
          </button>
        </div>

        <div 
          className="flex items-center gap-2 p-2.5 rounded-lg mb-3"
          style={{ backgroundColor: colors.surface }}
        >
          <IoHeartOutline size={16} style={{ color: colors.accent }} />
          <span className="text-xs" style={{ color: colors.textSecondary }}>
            Tap hearts to vote for your favorites!
          </span>
        </div>

        <div className="space-y-3">
          {filteredGear.map((gear) => (
            <CompactGearCard 
              key={gear.id} 
              gear={gear} 
              colors={colors} 
              onLiked={fetchData}
              onImagePress={() => setSelectedItem(gear)}
            />
          ))}
        </div>
      </div>

      <p className="text-[10px] text-center italic" style={{ color: colors.textSecondary }}>
        Affiliate Disclosure: Some links may earn us a commission at no extra cost to you.
      </p>

      {/* Product Detail Modal */}
      {selectedItem && (
        <div 
          className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-5"
          onClick={() => setSelectedItem(null)}
        >
          <div 
            className="w-full max-w-md rounded-2xl overflow-hidden max-h-[90vh] overflow-y-auto"
            style={{ backgroundColor: colors.card }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-3 right-3 p-1"
              onClick={() => setSelectedItem(null)}
            >
              <IoClose size={24} style={{ color: colors.textSecondary }} />
            </button>
            
            <div className="bg-white p-5 flex justify-center">
              <img 
                src={selectedItem.image} 
                alt={selectedItem.name}
                className="h-[220px] object-contain"
              />
            </div>
            
            <div className="p-5">
              <h3 className="text-lg font-bold mb-2" style={{ color: colors.text }}>
                {selectedItem.name}
              </h3>
              
              {selectedItem.rating && (
                <div className="flex items-center gap-1 mb-3">
                  <IoStar size={16} color="#FFB800" />
                  <span className="text-sm font-semibold" style={{ color: colors.text }}>
                    {selectedItem.rating}
                  </span>
                  <span className="text-sm" style={{ color: colors.textSecondary }}>
                    ({selectedItem.reviews} reviews)
                  </span>
                </div>
              )}
              
              <p className="text-sm leading-relaxed mb-3" style={{ color: colors.textSecondary }}>
                {selectedItem.description}
              </p>
              
              {selectedItem.category && (
                <span 
                  className="inline-block px-2.5 py-1 rounded-xl text-xs font-semibold mb-4"
                  style={{ backgroundColor: colors.accent + '20', color: colors.accent }}
                >
                  {selectedItem.category.charAt(0).toUpperCase() + selectedItem.category.slice(1)}
                </span>
              )}
              
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold" style={{ color: colors.accent }}>
                  {selectedItem.price}
                </span>
                <a
                  href={selectedItem.affiliateUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setSelectedItem(null)}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-full font-semibold text-sm"
                  style={{ backgroundColor: colors.accent, color: '#0F172A' }}
                >
                  Shop on Amazon
                  <IoArrowForward size={18} />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Featured Product Detail Modal */}
      {selectedFeaturedItem && (
        <div 
          className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-5"
          onClick={() => setSelectedFeaturedItem(null)}
        >
          <div 
            className="w-full max-w-md rounded-2xl overflow-hidden"
            style={{ backgroundColor: colors.card }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-3 right-3 p-1"
              onClick={() => setSelectedFeaturedItem(null)}
            >
              <IoClose size={24} style={{ color: colors.textSecondary }} />
            </button>
            
            <div className="bg-white p-5 flex justify-center">
              <img 
                src={selectedFeaturedItem.image} 
                alt={selectedFeaturedItem.name}
                className="h-[220px] object-contain"
              />
            </div>
            
            <div className="p-5">
              <h3 className="text-lg font-bold mb-2" style={{ color: colors.text }}>
                {selectedFeaturedItem.name}
              </h3>
              
              <p className="text-sm leading-relaxed mb-3" style={{ color: colors.textSecondary }}>
                {selectedFeaturedItem.blurb}
              </p>
              
              <span 
                className="inline-block px-2.5 py-1 rounded-xl text-xs font-semibold mb-4"
                style={{ backgroundColor: colors.accent + '20', color: colors.accent }}
              >
                Featured Pick
              </span>
              
              <div className="flex items-center justify-between">
                <span className="text-xl font-bold" style={{ color: colors.accent }}>
                  {selectedFeaturedItem.price}
                </span>
                <a
                  href={selectedFeaturedItem.affiliateUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setSelectedFeaturedItem(null)}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-full font-semibold text-sm"
                  style={{ backgroundColor: colors.accent, color: '#0F172A' }}
                >
                  Shop on Amazon
                  <IoArrowForward size={18} />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Compact Gear Card Component
const CompactGearCard = ({ gear, colors, onLiked, onImagePress }) => {
  const { hasVoted, vote, trackClick } = useVoting();
  const [voted, setVoted] = useState(hasVoted(gear.id));
  const [likes, setLikes] = useState(gear.likes || 0);

  const handleVote = async () => {
    if (voted) return;
    const success = await vote(gear.id);
    if (success) {
      setVoted(true);
      setLikes(prev => prev + 1);
      onLiked();
    }
  };

  const handleShop = async () => {
    await trackClick(gear.id);
    window.open(gear.affiliateUrl, '_blank');
  };

  const displayCategories = gear.categories && gear.categories.length > 0 
    ? gear.categories 
    : (gear.category ? [gear.category] : []);

  return (
    <div 
      className="flex gap-3 p-2.5 rounded-xl border"
      style={{ backgroundColor: colors.card, borderColor: colors.cardBorder }}
    >
      <button 
        onClick={onImagePress}
        className="w-[90px] h-[90px] flex-shrink-0 bg-white rounded-lg p-1.5 flex items-center justify-center"
      >
        <img 
          src={gear.image} 
          alt={gear.name}
          className="max-w-full max-h-full object-contain rounded"
        />
      </button>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between mb-0.5">
          <button onClick={onImagePress} className="text-left flex-1 mr-2">
            <p className="text-sm font-semibold line-clamp-1" style={{ color: colors.text }}>
              {gear.name}
            </p>
          </button>
          <button onClick={handleVote} className="flex items-center gap-1 p-1">
            {likes > 0 && (
              <span className="text-xs font-semibold" style={{ color: colors.accent }}>{likes}</span>
            )}
            {voted ? (
              <IoHeart size={18} style={{ color: colors.accent }} />
            ) : (
              <IoHeartOutline size={18} style={{ color: colors.accent }} />
            )}
          </button>
        </div>
        
        {gear.rating && (
          <div className="flex items-center gap-1 mb-0.5">
            <IoStar size={12} color="#FFB800" />
            <span className="text-[11px]" style={{ color: colors.textSecondary }}>
              {gear.rating} ({gear.reviews} reviews)
            </span>
          </div>
        )}

        {displayCategories.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-1">
            {displayCategories.slice(0, 3).map((cat, idx) => (
              <span 
                key={idx}
                className="px-1.5 py-0.5 rounded text-[9px] font-semibold"
                style={{ backgroundColor: colors.accent + '20', color: colors.accent }}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </span>
            ))}
          </div>
        )}
        
        <p className="text-xs line-clamp-2 leading-relaxed mb-1.5" style={{ color: colors.textSecondary }}>
          {gear.description}
        </p>
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold" style={{ color: colors.accent }}>{gear.price}</span>
          <button
            onClick={handleShop}
            className="px-3.5 py-1.5 rounded-xl text-xs font-semibold"
            style={{ backgroundColor: colors.accent, color: '#0F172A' }}
            data-testid={`shop-btn-${gear.id}`}
          >
            Shop
          </button>
        </div>
      </div>
    </div>
  );
};

export default Essentials;
