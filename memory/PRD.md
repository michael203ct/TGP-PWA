# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment. Clone GitHub repository https://github.com/michael203ct/thegigpulse.git, keep FastAPI backend as-is, deploy for custom domain thegigpulse.com.

## Latest Update (Feb 15, 2026)
- ✅ **Earnings Tracker Redesign:**
  - Total $ is now first field and only required (*)
  - Total $ field is larger with cyan accent border
  - Rideshare box (Uber/Lyft) with info icon explaining tip behavior
  - All fields visible without scrolling
  - Sticky Add Trip & End Shift buttons (always visible)
  - Trip cards show tip amount with "Edit Tip" button
  - Tip edit modal: for non-rideshare, asks if total should adjust or stay same
  - Cancel shift confirmation popup
  - "End Shift Without Posting" option in End Shift modal
- ✅ **Driver Wins Tabs:**
  - Two tabs at top: "Trips" (default) and "Shifts"
  - Trips tab shows regular trip posts
  - Shifts tab shows shift summaries with "Shift Complete" badge
  - "tap 🔥 if win!" changed to "show love" - moved to lower right
- ✅ **Arena Page Fix:**
  - "Choose Your Arena" header no longer cropped

## Previous Updates (Feb 14, 2026)
- ✅ **Arena Icon Update** - Changed from fire/fitness icon to ribbon icon
- ✅ **Earnings Tracker** - Real-time shift tracking with localStorage
- ✅ **Fire System Update** - All new posts start with 0 fires
- ✅ **Driver Wins Layout** - Username below date stamp, fire badge on right

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
   - **Trips/Shifts tabs** - Filter between regular trips and shift summaries
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

3. **Earnings Tracker** - Real-time shift tracking
   - **Start Shift** button begins tracking session
   - **Add Trip** modal:
     - Total $ first and required (larger, cyan border)
     - Rideshare box (Uber/Lyft) with info icon explaining tip behavior
     - All fields visible without scrolling (compact layout)
   - **Trip cards** show tip with "Edit Tip" button
   - **Tip Edit** for non-rideshare asks: adjust total or keep same?
   - **Sticky buttons** - Add Trip & End Shift always visible
   - **Cancel confirmation** - X button asks for confirmation
   - **End Shift** options:
     - Post to Driver Wins (requires username)
     - End without posting (just clear data)
   - Data persists in localStorage
   - Guest-friendly (username required only at end)

### Navigation
- 5-tab bottom navigation: Content, News Feed, Arena (center), Essentials, Apps
- Arena tab is centerpiece with ribbon icon, cyan-400 highlight, circular border

## Architecture
- **Frontend**: Expo (React Native for Web), built as static site
- **Backend**: FastAPI with Motor (async MongoDB driver)
- **Database**: MongoDB
- **Collections**: driver_wins, live_pulse_sessions, live_pulse_trips, competitions

## Future: User Account Integration (Planned)
- Currently guest-friendly with localStorage session IDs
- Future: User login/account creation
- Migration path: Link localStorage session to user account on registration
- Fields prepared for user_id association

## What's Been Implemented

### Earnings Tracker (Feb 15, 2026)
- [x] Redesigned Add Trip modal (Total $ first, rideshare box)
- [x] Sticky action buttons at bottom
- [x] Trip cards with Edit Tip button
- [x] Tip edit modal with adjust/keep options
- [x] Cancel confirmation popup
- [x] End without posting option

### Driver Wins (Feb 15, 2026)
- [x] Trips/Shifts tabs at top
- [x] Tab filtering works correctly
- [x] "show love" text moved to lower right

### Arena Page (Feb 15, 2026)
- [x] Header padding fixed (no longer cropped)

## Technical Notes
- Admin password: `mrn320`
- Backend runs on port 8001
- Frontend runs on port 3000
- All API endpoints prefixed with /api
- localStorage keys:
  - `gig_pulse_current_shift` - active shift data
  - `gig_pulse_session` - session ID for editing
  - `gig_pulse_username` - saved username

## API Endpoints (Arena)
- `GET /api/arena/driver-wins` - Get all trips
- `POST /api/arena/driver-wins` - Create trip (supports `shift_complete` field)
- `PUT /api/arena/driver-wins/{id}` - Update trip
- `POST /api/arena/driver-wins/{id}/fire` - Fire/unfire trip
- `DELETE /api/arena/driver-wins/{id}/admin?password=xxx` - Admin delete

## Prioritized Backlog

### P0 (Critical)
- None - all core functionality complete ✅

### P1 (High)
- Test emails cleanup in merch admin (production database)
- PWA prompt session-based dismissal (appears too frequently)
- Deploy with all Arena features

### P2 (Medium)  
- User accounts/login system
- Push notifications
- Analytics integration
- Competition management admin panel

### P3 (Low)
- Social sharing features
- "Most Fires" / "Top Earners" leaderboard
- Merch store integration
- Auto-price sync for essentials
