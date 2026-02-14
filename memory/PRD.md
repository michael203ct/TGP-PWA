# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment. Clone GitHub repository https://github.com/michael203ct/thegigpulse.git, keep FastAPI backend as-is, deploy for custom domain thegigpulse.com.

## Latest Update (Dec 2025)
- ✅ **YouTube Shorts Filter** - All videos < 3 minutes filtered out
- ✅ **Arena Page Fixed** - "Choose Your Arena" header no longer hidden
- ✅ **Base + Tip = Total** - Backend auto-recalculates total when tip updated
- ✅ **Admin Delete Posts** - Red trash icon allows admin to delete any post (password: mrn320)
- ✅ **Fixed Trip Data** - Corrected existing trip where $19+$44.25 showed $62.25 → now $63.25
- ✅ **Date/Time Stamp** - Shows "Sat, Feb 14 • 4:25 AM" on trip cards
- ✅ **Referral Text** - Split into 2 lines with down arrow (↓)

## Previous Updates (Feb 14, 2026)
- ✅ **The Arena** - New centerpiece feature with Live Pulse and Driver Wins
- ✅ **Driver Wins** - Real-time trip sharing with fire 🔥 voting system
- ✅ **Live Pulse** - Live streaming earnings tally with host mode for streamers
- ✅ **5-Tab Navigation** - Content, News Feed, Arena (center), Essentials, Apps
- ✅ **Referral Note** - Added to Apps page: "Use my referral link..."
- ✅ **Support the Pulse** - Renamed from "Support" in burger menu
- ✅ **Buy Me a Coffee** - Support page integration

## Previous Updates
- ✅ Admin Reject Button - Cross-platform alert helper
- ✅ Data Ordering - Featured items display in correct order
- ✅ Price Persistence - Manual price changes preserved
- ✅ Video Hide Persistence - Hidden videos stay hidden
- ✅ PWA & SEO Meta Tags - Proper manifest, icons, OG tags
- ✅ Colored Logo/Favicon - Cyan logo on dark background

## Project Overview
The Gig Pulse is a Progressive Web App (PWA) designed for gig economy workers - rideshare drivers, delivery workers, and shoppers. The platform curates educational content, industry news, essential gear, and helpful tools.

## User Personas
1. **Rideshare Drivers** - Uber, Lyft drivers seeking tips, gear, and earnings strategies
2. **Delivery Workers** - DoorDash, Grubhub, Amazon Flex drivers needing tools and advice  
3. **Shopping Gig Workers** - Instacart, Shipt shoppers looking for community recommendations
4. **Streamers/Content Creators** - Live streaming gig workers using Live Pulse for real-time earnings tally
5. **App Administrators** - Content managers reviewing user suggestions and moderating content

## Core Requirements

### The Arena
1. **Driver Wins** - Real-time trip sharing feed
   - Share trips with platform, amount, miles, minutes, note
   - Fire 🔥 voting system (tiered: 1 fire → 4+ fires)
   - Edit own trips via localStorage session
   - "Tip Updated" badge when tips are edited
   - Guest-friendly (no account required)

2. **Live Pulse** - Live streaming earnings tally
   - Live Now and Upcoming sections
   - Real-time earnings total and platform breakdown
   - Host Mode via secret URL: `/host-mode?id={id}&key={key}`
   - Streamers can add trips in real-time
   - Competition creation (pending approval)

### Navigation
- 5-tab bottom navigation: Content, News Feed, Arena (center), Essentials, Apps
- Arena tab is centerpiece with larger icon, cyan-400 highlight, subtle glow
- Merch removed from tab bar (still accessible via menu)

## Architecture
- **Frontend**: Expo (React Native for Web), built as static site
- **Backend**: FastAPI with Motor (async MongoDB driver)
- **Database**: MongoDB
- **Collections**: driver_wins, live_pulse_sessions, live_pulse_trips, competitions
- **External Integrations**: YouTube Data API, RSS feeds

## What's Been Implemented

### Arena Features (Feb 14, 2026)
- [x] Driver Wins API (CRUD, fire voting)
- [x] Live Pulse Sessions API
- [x] Host Mode for streamers
- [x] Competition creation (pending approval)
- [x] Real-time polling (10-15 seconds)
- [x] localStorage session for editing own trips
- [x] Fire emoji tiered badge system

### Previous Features
- [x] YouTube video feed with admin hide
- [x] News RSS aggregation
- [x] Essentials with price editing
- [x] Apps page with referral links
- [x] Admin panel (password: mrn320)
- [x] Buy Me a Coffee integration

## Technical Notes
- Admin password: `mrn320`
- Backend runs on port 8001
- Frontend runs on port 3000
- All API endpoints prefixed with /api
- Host Mode URL: `/host-mode?id={session_id}&key={host_key}`
- Cross-platform alerts using `showAlert()` helper
- Deployment uses `build-setup.js` script

## API Endpoints (Arena)
- `GET /api/arena/driver-wins` - Get all trips
- `POST /api/arena/driver-wins` - Create trip
- `PUT /api/arena/driver-wins/{id}` - Update trip
- `POST /api/arena/driver-wins/{id}/fire` - Fire/unfire trip
- `GET /api/arena/live-pulse/sessions` - Get live/upcoming sessions
- `POST /api/arena/live-pulse/sessions` - Create session
- `GET /api/arena/live-pulse/host/{id}?key={key}` - Verify host
- `POST /api/arena/live-pulse/sessions/{id}/add-trip` - Add trip (host only)

## Prioritized Backlog

### P0 (Critical)
- None - all core functionality complete ✅

### P1 (High)
- Deploy with Arena features
- Test Host Mode end-to-end

### P2 (Medium)  
- Push notifications
- Analytics integration
- Competition management admin panel

### P3 (Low)
- Social sharing features
- User accounts
- Merch store integration

