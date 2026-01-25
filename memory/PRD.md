# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment. Clone GitHub repository https://github.com/michael203ct/thegigpulse.git, keep FastAPI backend as-is, deploy for custom domain thegigpulse.com.

## Latest Update (Jan 25, 2026)
- Pulled latest Expo code from GitHub with correct logo (car + pulse + road)
- Built web version using `npx expo export --platform web`
- Set up static server with API proxy to backend
- YouTube API configured and working
- All data seeded correctly:
  - 3 Weekly Shows with thumbnails (Drivers Coast 2 Coast, Show Me The Money Club, Off The Clock)
  - 3 Featured Channels (Rideshare Rodeo, The Rideshare Guy, Rideshare Professor)
  - 10 Gig Apps with referral links
  - 6 Helpful Tools (Gridwise, Everlance, WorkSolo, GigU, Mystro, Maxymo)
  - 3 Featured Gear with Amazon affiliate links
  - 19 Community Favorites with Amazon affiliate links
- Testing: 93% overall success rate

## Project Overview
The Gig Pulse is a Progressive Web App (PWA) designed for gig economy workers - rideshare drivers, delivery workers, and shoppers. The platform curates educational content, industry news, essential gear, and helpful tools.

## User Personas
1. **Rideshare Drivers** - Uber, Lyft drivers seeking tips, gear, and earnings strategies
2. **Delivery Workers** - DoorDash, Grubhub, Amazon Flex drivers needing tools and advice  
3. **Shopping Gig Workers** - Instacart, Shipt shoppers looking for community recommendations
4. **App Administrators** - Content managers reviewing user suggestions

## Core Requirements (Static)
- Home page with navigation to main sections
- Content page with YouTube video feed (requires YouTube API key)
- News Feed with RSS aggregation
- Essentials page with featured gear and community favorites
- Apps page listing gig platforms and helpful tools
- Merch page (coming soon) with email subscription
- Admin panel with password protection (mrn320)
- Dark/Light theme toggle
- PWA installation capability

## Architecture
- **Frontend**: React 18 with React Router, Tailwind CSS, react-icons
- **Backend**: FastAPI with Motor (async MongoDB driver)
- **Database**: MongoDB
- **External Integrations**: YouTube Data API, RSS feeds

## What's Been Implemented (Jan 24-25, 2026)
- [x] Cloned repository from GitHub
- [x] Converted Expo React Native to standard React
- [x] All navigation pages: Home, Content, News, Essentials, Apps, Merch
- [x] Bottom tab navigation and header with menu
- [x] Admin panel with password authentication (mrn320)
- [x] Suggestion forms: Channel, News, Gear, App
- [x] Theme toggle (dark/light mode)
- [x] Backend FastAPI server preserved with all features
- [x] All static content APIs working
- [x] Email subscription for merch notifications
- [x] Updated assets and product images from GitHub
- [x] Deployment check passed - ready for production

## Prioritized Backlog

### P0 (Critical)
- None - core functionality complete

### P1 (High)
- Configure YouTube API key for video content
- Set up RSS feed sources for news

### P2 (Medium)  
- PWA manifest and service worker configuration
- Push notification support
- Analytics integration

### P3 (Low)
- Social sharing features
- User accounts and personalization
- Merch store integration when ready

## Next Tasks
1. Add YouTube API key to enable video content
2. Configure custom domain thegigpulse.com
3. Set up production deployment

## Technical Notes
- Admin password: mrn320
- Backend runs on port 8001
- Frontend runs on port 3000
- All API endpoints prefixed with /api
