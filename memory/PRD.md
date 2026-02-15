# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment. Clone GitHub repository https://github.com/michael203ct/thegigpulse.git, keep FastAPI backend as-is, deploy for custom domain thegigpulse.com.

## Latest Update (Feb 15, 2026 - Voice & UI Cleanup)
- ✅ **Speech Recognition** for Add Trip:
  - Voice button (🎤) in modal header
  - Say "$35, UberEats" or "$50 with $15 tip, DoorDash"
  - Auto-fills platform, total, tip, and calculates base
- ✅ **Tip Calculation Logic Fixed**:
  - For delivery apps: tip is PART of total
  - If total=$35, tip=$10 → base auto-calculates to $25 (35-10)
  - For rideshare: tip is additional to total
- ✅ **Add Trip Modal Cleanup**:
  - Total $ first and only required field (*)
  - Larger input with cyan border
  - Rideshare box (Uber/Lyft) with info icon explaining tip behavior
  - "Minutes" spelled out (not "Min")
  - Note field on its own line at bottom
  - No placeholder numbers in any field
  - Platform order: Grubhub moved after Shipt
- ✅ **Trip Card Redesign** (Earnings Tracker):
  - Edit Tip button moved inline with tip amount
  - Edit Trip button has border (distinct from Edit Tip)
  - Base pay shown on card
- ✅ **Driver Wins Cleanup**:
  - "show love" removed - just fire emoji with count
  - Shift cards clickable → opens detail popup
  - Shift Detail popup shows: total, platform, base, tips, miles, time, $/mi, $/hr

## Previous Updates (Feb 15, 2026)
- ✅ Trips/Shifts tabs at top of Driver Wins
- ✅ Sticky Add Trip & End Shift buttons
- ✅ "End Shift Without Posting" option
- ✅ Arena page header fixed (no longer cropped)

## Project Overview
The Gig Pulse is a Progressive Web App (PWA) for gig economy workers - rideshare drivers, delivery workers, and shoppers. Features educational content, industry news, essential gear, and the Arena (Driver Wins, Live Pulse, Earnings Tracker).

## Core Requirements

### The Arena
1. **Driver Wins** - Real-time trip sharing feed
   - **Trips/Shifts tabs** - Filter between regular trips and shift summaries
   - Shift cards clickable → detail popup
   - Fire 🔥 voting system (no "show love" text)
   - All new posts start with 0 fires
   - Guest-friendly (no account required)

2. **Live Pulse** - Live streaming earnings tally
   - Live Now and Upcoming Competitions sections
   - Host Mode for streamers

3. **Earnings Tracker** - Real-time shift tracking
   - **Voice input**: Say "$35, UberEats" to auto-fill
   - **Add Trip** modal:
     - Total $ first and required (larger, cyan border)
     - Tip calculation: for delivery, tip is part of total (base = total - tip)
     - Rideshare box with info icon
     - "Minutes" spelled out, Note on own line
     - No placeholder numbers
   - **Trip cards**: Edit Tip inline, Edit Trip with border
   - **Sticky buttons** - Add Trip & End Shift always visible
   - **End options**: Post to Driver Wins OR End without posting

## Technical Notes
- Admin password: `mrn320`
- Backend runs on port 8001
- Frontend runs on port 3000
- Speech Recognition: Uses Web Speech API (Chrome/Safari)
- localStorage keys:
  - `gig_pulse_current_shift` - active shift data
  - `gig_pulse_session` - session ID for editing
  - `gig_pulse_username` - saved username

## Tip Calculation Logic
```
For Rideshare (Uber, Lyft):
  - Tip is ADDITIONAL to total
  - If total=$50, tip=$10 → total stays $50, tip=$10
  
For Delivery (DoorDash, UberEats, etc.):
  - Tip is PART of total
  - If total=$35, tip=$10 → base = $35 - $10 = $25
```

## Speech Recognition Patterns
Supported phrases:
- "$35, DoorDash" → total=35, platform=DoorDash
- "$50 with $15 tip, UberEats" → total=50, tip=15, base=35, platform=UberEats
- "Uber, $25" → platform=Uber, total=25

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
- PWA prompt session-based dismissal (appears too frequently)
- Test emails cleanup in merch admin

### P2 (Medium)  
- User accounts/login system (localStorage → user account migration)
- Push notifications
- Analytics integration

### P3 (Low)
- "Top Earners" leaderboard
- Merch store integration
- Social sharing features
