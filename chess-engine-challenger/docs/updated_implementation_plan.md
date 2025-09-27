# Chess Engine Challenger - Updated Implementation Plan

## Project Requirements Analysis
1. **UCI Compatibility**: Simple UCI controller for any engine executable
2. **Cloud Deployment Ready**: Firebase hosting with portable architecture
3. **Lightweight Logging**: Client-side updates, server logs complete games only
4. **Security Audit**: Locked-down frontend/backend with input validation
5. **Portable Design**: Can be integrated into company website portfolio

## Security Audit & Hardening Plan

### Backend Security Measures
- **Input Validation**: All moves validated against chess rules before engine communication
- **Engine Process Isolation**: Subprocess sandboxing with timeout limits
- **Rate Limiting**: Per-IP request limiting to prevent DOS attacks  
- **Path Traversal Prevention**: Whitelist engine executables, no dynamic path construction
- **Command Injection Prevention**: No shell=True, validated UCI command structure only
- **Resource Limits**: Engine process memory/CPU limits, automatic termination
- **Error Handling**: No sensitive information leaked in error responses

### Frontend Security Measures  
- **Input Sanitization**: Move notation validation before API calls
- **XSS Prevention**: No innerHTML usage, DOM manipulation only
- **CSRF Protection**: API tokens for state-changing operations
- **Content Security Policy**: Strict CSP headers to prevent script injection
- **HTTPS Only**: All communication over secure connections
- **Client-Side Validation**: Move legality checked before server submission

## Portable Architecture Design

### File Structure (Cloud-Ready)
```
chess-engine-challenger/
├── backend/
│   ├── app.py                     # Flask application (can run on any cloud)
│   ├── uci_controller.py          # Universal UCI engine communication
│   ├── security_middleware.py     # Security validation layer
│   ├── config.py                  # Environment-based configuration
│   ├── game_logger.py             # PGN logging with move times/evals
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── index.html                 # Standalone web interface
│   ├── js/
│   │   ├── chess-engine-ui.js     # Main UI controller
│   │   ├── board-renderer.js      # Chess board display
│   │   └── api-client.js          # Secure API communication
│   ├── css/
│   │   └── chess-challenger.css   # Responsive styling
│   └── assets/
│       └── pieces/                # Chess piece images
├── engines/
│   ├── v7p3r_engine.exe          # Your engines
│   ├── cobra_engine.exe
│   └── slowmate_engine.exe
├── firebase/
│   ├── firebase.json              # Firebase hosting config
│   ├── .firebaserc               # Firebase project config
│   └── functions/                 # Cloud functions (future)
└── docs/
    └── deployment_guide.md        # Step-by-step deployment
```

## UCI Controller Specifications

### Universal Engine Communication
- **Standard UCI Protocol**: Works with any UCI-compliant engine
- **Process Management**: Automatic start/stop, timeout handling
- **Error Recovery**: Engine crashes handled gracefully
- **Move Time Tracking**: Precise timing for PGN records
- **Evaluation Capture**: Extract engine analysis when available

### Engine Configuration
```python
{
    "V7P3R": {
        "executable": "engines/v7p3r_engine.exe",
        "startup_time": 5000,  # ms
        "move_time_default": 1000,  # ms
        "supports_eval": True
    },
    "C0BR4": {
        "executable": "engines/cobra_engine.exe", 
        "startup_time": 3000,
        "move_time_default": 1000,
        "supports_eval": True
    }
}
```

## Lightweight Game Logging

### Complete Games Only
- **Result Required**: Only log games with definitive outcomes
- **Rich PGN Format**: Include move times, evaluations, time stamps
- **Event Logging**: Separate log for crashes/abandons (no ELO impact)
- **Client Updates**: Real-time UI updates without server logging

### PGN Enhancement Example
```
[Event "Engine Challenge"]
[Site "Chess Engine Challenger"]
[Date "2024.01.15"]
[White "Human (1500)"]
[Black "V7P3R (1800)"] 
[Result "0-1"]
[WhiteTime "600+5"]
[BlackTime "600+5"]

1. e4 {[%clk 9:58] [%eval +0.25]} e5 {[%clk 9:57] [%eval -0.20] [%mt 1.2s]}
```

## Firebase Integration Plan

### Hosting Structure
- **Static Frontend**: Served directly from Firebase hosting
- **Cloud Functions**: Handle UCI engine communication (Python runtime)
- **Firestore Database**: Game records, ELO tracking, usage analytics
- **Cloud Storage**: Engine executables, game PGN files
- **Authentication**: Optional user accounts for ELO tracking

### Environment Configuration
```javascript
// firebase-config.js
const firebaseConfig = {
    apiKey: process.env.FIREBASE_API_KEY,
    authDomain: "chess-challenger.firebaseapp.com",
    projectId: "chess-challenger",
    storageBucket: "chess-challenger.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc123def456"
};
```

## Implementation Phases

### Phase 1: Secure UCI Backend (Current)
- UCI controller with security hardening
- Input validation and rate limiting
- Basic Flask API with CORS protection
- Engine process management

### Phase 2: Frontend Security & UX
- Secure chess board interface
- Move validation and API integration
- Responsive design for mobile/desktop
- Error handling and user feedback

### Phase 3: Firebase Migration
- Cloud Functions deployment
- Firestore integration for game logging
- Static hosting configuration
- Environment variable management

### Phase 4: Portfolio Integration
- Standalone deployment capability
- Custom domain configuration
- Company website integration
- Performance optimization

## Security Testing Checklist
- [ ] Input validation (malformed moves, injection attempts)
- [ ] Rate limiting effectiveness
- [ ] Engine process isolation
- [ ] File system access restrictions
- [ ] API endpoint security
- [ ] Frontend XSS protection
- [ ] CSRF token validation
- [ ] Error message sanitization
```
