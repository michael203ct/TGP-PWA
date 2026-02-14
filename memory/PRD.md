# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment. Clone GitHub repository https://github.com/michael203ct/thegigpulse.git, keep FastAPI backend as-is, deploy for custom domain thegigpulse.com.

## Latest Update (Feb 14, 2026)
- ✅ **Arena Icon Update** - Changed from fire/fitness icon to ribbon icon for "The Arena" title and bottom tab
- ✅ **Earnings Tracker** - New feature added to Arena section:
  - Real-time shift tracking with Start Shift button
  - Add multiple trips during shift (stored in localStorage)
  - Live running total updates as trips are added
  - End Shift saves to MongoDB and posts to Driver Wins with "Shift Complete" badge
  - Guest-friendly (no login required)
- ✅ **Fire System Update** - All new posts start with 0 fires (changed from 1)
- ✅ **Driver Wins Layout** - Username below date stamp, fire badge on right
- ✅ **Live Pulse** - Added "Upcoming Competitions" section

## Previous Updates (Dec 2025)
- ✅ **Arena Page Compact** - Smaller cards/icons, fits on one screen without scroll
- ✅ **Driver Wins Layout Redesign**:
  - Date/time moved to top right
  - Username moved to bottom right
  - Stats (mi, hr) aligned on right
  - Less crowded left side
- ✅ **Hidden Admin Mode** - 5 taps on "Driver Wins" header reveals trash icons
- ✅ **Base + Tip = Total** - Backend auto-recalculates on update

## Previous Updates (Feb 14, 2026)
- ✅ **The Arena** - New centerpiece feature with Live Pulse, Driver Wins, and Earnings Tracker
- ✅ **Driver Wins** - Real-time trip sharing with fire 🔥 voting system
- ✅ **Live Pulse** - Live streaming earnings tally with host mode for streamers
- ✅ **5-Tab Navigation** - Content, News Feed, Arena (center), Essentials, Apps
- ✅ **Referral Note** - Added to Apps page: "Use my referral link..."
- ✅ **Support the Pulse** - Renamed from "Support" in burger menu
- ✅ **Buy Me a Coffee** - Support page integration

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
   - Fire 🔥 voting system (tiered: 0-1=🔥, 2-4=🔥🔥, 5-9=🔥🔥🔥, 10+=🔥🔥🔥🔥)
   - All new posts start with 0 fires
   - Edit own trips via localStorage session
   - "Tip Updated" badge when tips are edited
   - "Shift Complete" badge for shift summaries
   - Guest-friendly (no account required)

2. **Live Pulse** - Live streaming earnings tally
   - Live Now and Upcoming Competitions sections
   - Real-time earnings total and platform breakdown
   - Host Mode via secret URL: `/host-mode?id={id}&key={key}`
   - Streamers can add trips in real-time
   - Competition creation (pending approval)

3. **Earnings Tracker** - Real-time shift tracking
   - Start Shift button begins tracking session
   - Add Trip during shift (platform, total, base, tip, miles, minutes, note)
   - Data persists in localStorage across app sessions
   - Live running total updates immediately
   - Editable trip list during shift
   - End Shift posts summary to Driver Wins with "Shift Complete" badge
   - Guest-friendly (username required only at end)

### Navigation
- 5-tab bottom navigation: Content, News Feed, Arena (center), Essentials, Apps
- Arena tab is centerpiece with ribbon icon, cyan-400 highlight, circular border
- Merch removed from tab bar (still accessible via menu)

## Architecture
- **Frontend**: Expo (React Native for Web), built as static site
- **Backend**: FastAPI with Motor (async MongoDB driver)
- **Database**: MongoDB
- **Collections**: driver_wins, live_pulse_sessions, live_pulse_trips, competitions
- **External Integrations**: YouTube Data API, RSS feeds

## What's Been Implemented

### Arena Features (Feb 14, 2026)
- [x] Driver Wins API (CRUD, fire voting, shift_complete support)
- [x] Live Pulse Sessions API
- [x] Host Mode for streamers
- [x] Competition creation (pending approval)
- [x] Real-time polling (10-15 seconds)
- [x] localStorage session for editing own trips
- [x] Fire emoji tiered badge system (starts at 0)
- [x] Earnings Tracker with localStorage persistence
- [x] Shift Complete badge for shift summaries

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
- Earnings Tracker uses `localStorage` keys:
  - `gig_pulse_current_shift` - active shift data
  - `gig_pulse_session` - session ID for editing
  - `gig_pulse_username` - saved username

## API Endpoints (Arena)
- `GET /api/arena/driver-wins` - Get all trips
- `POST /api/arena/driver-wins` - Create trip (supports `shift_complete` field)
- `PUT /api/arena/driver-wins/{id}` - Update trip
- `POST /api/arena/driver-wins/{id}/fire` - Fire/unfire trip
- `DELETE /api/arena/driver-wins/{id}/admin?password=xxx` - Admin delete
- `GET /api/arena/live-pulse/sessions` - Get live/upcoming sessions
- `POST /api/arena/live-pulse/sessions` - Create session
- `GET /api/arena/live-pulse/host/{id}?key={key}` - Verify host
- `POST /api/arena/live-pulse/sessions/{id}/add-trip` - Add trip (host only)

## Prioritized Backlog

### P0 (Critical)
- None - all core functionality complete ✅

### P1 (High)
- Test emails cleanup in merch admin (production database)
- Deploy with Arena features
- Test Host Mode end-to-end

### P2 (Medium)  
- Push notifications
- Analytics integration
- Competition management admin panel
- Auto-price sync for essentials

### P3 (Low)
- Social sharing features
- User accounts
- Merch store integration
- "Most Fires" / "Top Earners" leaderboard
