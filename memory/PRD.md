# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment. Clone GitHub repository https://github.com/michael203ct/thegigpulse.git, keep FastAPI backend as-is, deploy for custom domain thegigpulse.com.

## Latest Update (Jan 28, 2026)
- ✅ **Admin Reject Button FIXED** - The Reject button now works on web platform using cross-platform alert helper
- ✅ **Data Ordering Fixed** - Featured Gear, Channels, and Tools now display in correct order
- ✅ **Price Persistence Fixed** - Manual price changes are no longer reset on server restart
- ✅ **Video Hide Persistence** - Hidden videos remain hidden after cache refresh
- ✅ **PWA & SEO Meta Tags** - Proper manifest.json, icons, and OG tags for link previews
- ✅ **Ionicons Font Fixed** - Icons now load correctly on deployed site

## Previous Updates (Jan 24-26, 2026)
- ✅ **Admin Hide Video Feature** - Tap "Latest Videos" title 5 times to enable admin mode
- ✅ All backend syntax errors fixed
- ✅ Frontend rebuilt and deployed
- ✅ All 18 backend tests passing (100%)
- ✅ All frontend tests passing (100%)
- ✅ Apps page scrolling confirmed working

## Project Overview
The Gig Pulse is a Progressive Web App (PWA) designed for gig economy workers - rideshare drivers, delivery workers, and shoppers. The platform curates educational content, industry news, essential gear, and helpful tools.

## User Personas
1. **Rideshare Drivers** - Uber, Lyft drivers seeking tips, gear, and earnings strategies
2. **Delivery Workers** - DoorDash, Grubhub, Amazon Flex drivers needing tools and advice  
3. **Shopping Gig Workers** - Instacart, Shipt shoppers looking for community recommendations
4. **App Administrators** - Content managers reviewing user suggestions and moderating video feed

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
- **Admin Hide Video** - Moderators can hide inappropriate videos from the feed

## Architecture
- **Frontend**: Expo (React Native for Web), built as static site with `npx expo export --platform web`
- **Backend**: FastAPI with Motor (async MongoDB driver)
- **Database**: MongoDB
- **External Integrations**: YouTube Data API, RSS feeds

## What's Been Implemented (Jan 24-26, 2026)
- [x] Cloned repository from GitHub
- [x] Built web version using Expo export
- [x] Set up static server with API proxy
- [x] All navigation pages: Home, Content, News, Essentials, Apps, Merch
- [x] Bottom tab navigation and header with menu
- [x] Admin panel with password authentication (mrn320)
- [x] Suggestion forms: Channel, News, Gear, App
- [x] Theme toggle (dark/light mode)
- [x] YouTube API configured and working
- [x] All static content seeded:
  - 3 Weekly Shows
  - 3 Featured Channels
  - 10 Gig Apps with referral links
  - 6 Helpful Tools
  - 3 Featured Gear
  - 19 Community Favorites
- [x] **Admin Hide Video Feature** - 5-tap toggle, red X button on video cards

## Prioritized Backlog

### P0 (Critical)
- None - all core functionality complete ✅

### P1 (High)
- Full end-to-end verification of admin functionality on deployed site

### P2 (Medium)  
- PWA manifest and service worker configuration
- Push notification support
- Analytics integration

### P3 (Low)
- Social sharing features
- User accounts and personalization
- Merch store integration when ready

## Next Tasks
1. **Deploy the application** to production environment
2. Configure custom domain thegigpulse.com
3. Set up SSL certificate for custom domain

## Technical Notes
- Admin password: `mrn320`
- Backend runs on port 8001
- Frontend runs on port 3000
- All API endpoints prefixed with /api
- Admin Hide Video: 5-tap on "Latest Videos" title, 2-second window

## Test Results (Jan 26, 2026)
- Backend: 100% (18/18 tests passed)
- Frontend: 100% (all features verified)
- Test report: /app/test_reports/iteration_6.json
