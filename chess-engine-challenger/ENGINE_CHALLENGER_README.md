# Chess Engine Challenger
This project is a way to create an interface for all the various engine versions that have been compiled throughout development. Its an opportunity for me as a developer to challenge the engines, to set them up to play against eachother, to open up a web interface to allow others to play against the engine of their choosing. 

## Current Engines
- V7P3R (Starting ELO: 1300)
- C0BR4 (Starting ELO: 1300)
- SlowMate (Starting ELO: 1300)

## Current Features
- Simple web interface with engine selection dropdowns
    - Two dropdowns for player selection for white/black (human or one of the engines in the list)
- Time Controls: 30|0, 10|5, 5|5, 3|2, 1|1
- Board display using dark theme board and pieces from images directory
- Move list displayed next to board
- Game PGN saved to game_records\ directory
- Basic ELO calculation per engine (starting from 1300)

## Architecture Strategy
### Firebase Project Structure (Separate Project Approach)
- **Main Project**: `chess-engine-challenger-firebase`
- **Custom Domain**: `chess.labs.rapidtechconsultants.com`
- **Engine Storage**: Firebase Cloud Storage bucket for engine executables (3GB+)
- **Backend**: Python Flask app deployed via Cloud Functions
- **Frontend**: Static hosting on Firebase Hosting
- **Database**: Firestore for game records, ELO tracking, and metrics

### Integration with RTS Learning Labs
- **Parent Site**: `labs.rapidtechconsultants.com` (main labs portal)
- **Chess Challenger**: Embedded or linked from labs portal
- **Benefits**: Isolated costs, independent scaling, security separation

### Security & Performance
- UCI engine communication via secure Cloud Functions
- Engine executables stored in authenticated Cloud Storage
- Rate limiting and input validation for public access
- Bitboard evaluation system for high-performance analysis

## TODO: Future Features (Post-MVP)

### Phase 2: Enhanced Player Tracking
- [ ] **Lichess Integration**: Import player ELO via Lichess API for verification
- [ ] **Chess.com Integration**: Import player ratings for accurate matchmaking
- [ ] **Verified ELO System**: More confident ELO calculations with known player ratings
- [ ] **Player Profiles**: Optional accounts with game history and statistics

### Phase 3: Advanced Anti-Cheat
- [ ] **Stockfish Monitoring**: Detect engine assistance during human games
- [ ] **AI Pattern Detection**: Identify suspicious move patterns
- [ ] **Move Time Analysis**: Flag unrealistic calculation speeds
- [ ] **Position Analysis**: Cross-reference with known engine evaluations

### Phase 4: Tournament System
- [ ] **Engine vs Engine Tournaments**: Automated round-robin competitions
- [ ] **Swiss System Tournaments**: Human and engine mixed events
- [ ] **Time Control Variants**: Bullet, blitz, rapid, classical divisions
- [ ] **Opening Book Restrictions**: Test engines in specific openings

### Phase 5: Advanced Analytics
- [ ] **Real-time Metrics Dashboard**: Live game statistics and ELO changes
- [ ] **Opening Performance Analysis**: Track engine success by opening
- [ ] **Endgame Statistics**: Evaluate engine endgame playing strength
- [ ] **Positional Analysis**: Deep dive into tactical vs positional play

### Phase 6: Learning Integration
- [ ] **Interactive Lessons**: Analyze games with educational commentary
- [ ] **Position Trainer**: Practice specific positions against engines
- [ ] **Opening Explorer**: Study openings through engine games
- [ ] **Puzzle Generation**: Create puzzles from engine games

## Development Phases

### Phase 1: MVP (Current)
- [x] Basic web interface with engine selection
- [x] UCI communication system
- [x] Time controls and basic game flow
- [x] PGN recording with move times and evaluations
- [x] Simple ELO calculation (starting at 1300)
- [ ] Firebase deployment with Cloud Storage engines
- [ ] Security hardening and rate limiting

### Phase 2: Cloud Production
- [ ] Firebase project setup with custom domain
- [ ] Engine storage in Cloud Storage buckets
- [ ] Firestore integration for persistent data
- [ ] Performance optimization and caching
- [ ] Comprehensive error handling and logging

### Phase 3: Public Launch
- [ ] Integration with labs.rapidtechconsultants.com
- [ ] User feedback system and bug reporting
- [ ] Mobile responsiveness and PWA features
- [ ] Basic analytics and usage tracking

## Technical Specifications
- **Frontend**: Vanilla HTML/CSS/JS with responsive design
- **Backend**: Flask + Cloud Functions for UCI communication
- **Database**: Firestore for games, ELO, and user data
- **Storage**: Cloud Storage for engine executables and game records
- **Security**: Input validation, rate limiting, CORS protection
- **Performance**: Bitboard evaluation for 15,000+ NPS analysis speed

## Engine Integration Notes
- All engines must be UCI-compatible
- Engine executables stored securely in Cloud Storage
- Process isolation and resource limits for security
- Automatic cleanup of idle engine processes
- Support for engine-specific time management and options

## Cost Considerations
- **Storage**: ~3GB for all engine versions ($0.026/GB/month)
- **Compute**: Cloud Functions for UCI communication (pay-per-use)
- **Database**: Firestore reads/writes for game logging
- **Bandwidth**: Minimal for web interface, higher for engine downloads
- **Estimated Monthly Cost**: $10-30 for moderate usage (100+ games/day)

## Getting Started
1. Clone repository to local development environment
2. Set up Firebase project with Authentication and Cloud Storage
3. Deploy engines to Cloud Storage bucket
4. Configure Flask backend for Cloud Functions deployment
5. Test locally with Firebase emulators
6. Deploy to production with custom domain configuration

## Links
- **Production Site**: `chess.labs.rapidtechconsultants.com` (planned)
- **Parent Labs Portal**: `labs.rapidtechconsultants.com` (planned)
- **Main RTS Site**: `rapidtechconsultants.com`