import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const VotingContext = createContext(undefined);

// Generate a unique device ID
const getDeviceId = () => {
  let deviceId = localStorage.getItem('device_id');
  if (!deviceId) {
    deviceId = 'web_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    localStorage.setItem('device_id', deviceId);
  }
  return deviceId;
};

export const VotingProvider = ({ children }) => {
  const [votedProducts, setVotedProducts] = useState(new Set());
  const [votesRemaining, setVotesRemaining] = useState(5);
  const deviceId = getDeviceId();

  useEffect(() => {
    // Load voted products from localStorage
    const saved = localStorage.getItem('voted_products');
    if (saved) {
      setVotedProducts(new Set(JSON.parse(saved)));
    }

    // Load votes remaining for today
    const today = new Date().toDateString();
    const savedDate = localStorage.getItem('vote_date');
    if (savedDate === today) {
      const remaining = localStorage.getItem('votes_remaining');
      if (remaining) setVotesRemaining(parseInt(remaining, 10));
    } else {
      // Reset for new day
      localStorage.setItem('vote_date', today);
      localStorage.setItem('votes_remaining', '5');
      setVotesRemaining(5);
    }
  }, []);

  const hasVoted = useCallback((productId) => {
    return votedProducts.has(productId);
  }, [votedProducts]);

  const canVote = useCallback(() => {
    return votesRemaining > 0;
  }, [votesRemaining]);

  const vote = useCallback(async (productId) => {
    if (hasVoted(productId) || !canVote()) {
      return false;
    }

    try {
      const response = await fetch(`${API_URL}/api/gear/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, device_id: deviceId }),
      });

      if (response.ok) {
        // Update local state
        const newVoted = new Set(votedProducts);
        newVoted.add(productId);
        setVotedProducts(newVoted);
        localStorage.setItem('voted_products', JSON.stringify([...newVoted]));

        const newRemaining = votesRemaining - 1;
        setVotesRemaining(newRemaining);
        localStorage.setItem('votes_remaining', newRemaining.toString());

        return true;
      }
      return false;
    } catch (error) {
      console.error('Vote error:', error);
      return false;
    }
  }, [deviceId, hasVoted, canVote, votedProducts, votesRemaining]);

  const trackClick = useCallback(async (productId) => {
    try {
      await fetch(`${API_URL}/api/gear/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId }),
      });
    } catch (error) {
      console.error('Click tracking error:', error);
    }
  }, []);

  return (
    <VotingContext.Provider value={{ hasVoted, canVote, vote, trackClick, votesRemaining }}>
      {children}
    </VotingContext.Provider>
  );
};

export const useVoting = () => {
  const context = useContext(VotingContext);
  if (!context) {
    throw new Error('useVoting must be used within a VotingProvider');
  }
  return context;
};
