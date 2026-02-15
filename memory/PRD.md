# The Gig Pulse - PRD

## Original Problem Statement
Convert "The Gig Pulse" PWA from Expo React Native to standard React for web deployment.

## Latest Update (Feb 15, 2026 - Voice & UI Improvements)
- ✅ **Speech Recognition Improved**:
  - Better recognition of "Uber Eats" (also: "uber eats", "uber eat", "uber eight")
  - Better recognition of "Lyft" (also: "lift", "left")
  - Mic button moved between Add Trip and End Shift (with border)
  - Listening banner shows example phrases
- ✅ **"Uber Eats"** now has space (not "UberEats")
- ✅ **Add Trip Modal Reordered**:
  - Platform selection FIRST (no platform pre-selected)
  - Total $ below platforms (required *)
  - Divider line with "optional" text
  - Base $, Tip $, Miles, Minutes, Note all optional
  - Note on its own line
  - No placeholder numbers
- ✅ **Shift Detail Popup**:
  - Platform-by-platform breakdown (shows trips and $ per platform)
  - Summary section with trip count and duration
- ✅ **Tip Calculation Logic**:
  - For delivery: tip is PART of total (base = total - tip)

## Project Overview
The Gig Pulse is a Progressive Web App (PWA) for gig economy workers.

## Core Features

### Earnings Tracker
- **Start Shift** → Track earnings in real-time
- **Add Trip** - Platform first, then Total $, then optional fields
- **Voice Input** - Say "$35 Uber Eats" or "$50 with $15 tip DoorDash"
- **Mic Button** - Between Add Trip and End Shift, with border
- **Tip Calculation** - Delivery: tip is part of total
- **End Shift** - Post to Driver Wins or end without posting
- **Platform Breakdown** - Stored in shift note for detail popup

### Driver Wins
- **Trips/Shifts tabs** - Filter between regular trips and shift summaries
- **Shift cards clickable** - Opens detail popup with platform breakdown
- **Fire voting** - No "show love" text, just emoji with count
- **No placeholders** in form fields

## Speech Recognition Aliases
```
Uber: "uber", "hoover", "ooober", "uber ride"
Lyft: "lyft", "lift", "left", "lifted"
Uber Eats: "uber eats", "ubereats", "uber eat", "uber eight", "eats"
DoorDash: "doordash", "door dash"
Instacart: "instacart", "insta cart"
Spark: "spark", "walmart spark"
Amazon Flex: "amazon", "amazon flex", "flex"
Shipt: "shipt", "shipped", "ship"
Grubhub: "grubhub", "grub hub", "grub"
```

## Tip Calculation Logic
```
Rideshare (Uber, Lyft):
  - Tip is ADDITIONAL to total
  
Delivery (DoorDash, Uber Eats, etc.):
  - Tip is PART of total
  - base = total - tip
```

## Platform Breakdown Storage
When ending shift, breakdown stored in note:
`5 trips • 2h 30m shift • Uber:2x$45|DoorDash:3x$78`

## Technical Notes
- Admin password: `mrn320`
- Speech: Web Speech API (Chrome/Safari)
- localStorage keys: `gig_pulse_current_shift`, `gig_pulse_session`, `gig_pulse_username`

## Prioritized Backlog

### P1 (High)
- PWA prompt session-based dismissal

### P2 (Medium)  
- User accounts/login system
- Push notifications

### P3 (Low)
- "Top Earners" leaderboard
- Social sharing features
