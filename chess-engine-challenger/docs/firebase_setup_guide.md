# Chess Engine Challenger - Firebase Setup Guide

## Project Overview
Standalone web application for testing chess engines with public access
**Budget Target**: $20-$100/month maximum
**Architecture**: Cost-optimized Firebase deployment

## Firebase Project Setup

### 1. Create Firebase Project
```bash
# Navigate to project directory
cd "s:\Maker Stuff\Programming\Chess Engines\Chess Engine Playground\engine-tester\chess-engine-challenger"

# Login to Firebase (already completed)
firebase login

# Initialize new Firebase project
firebase init

# Select the following options:
# ✓ Hosting: Configure files for Firebase Hosting
# ✓ Functions: Configure Cloud Functions (Python runtime)
# ✓ Storage: Configure Cloud Storage security rules
# ✓ Firestore: Configure security rules and indexes
```

### 2. Firebase Configuration Files
Create the following configuration structure:

```
chess-engine-challenger/
├── firebase.json              # Main Firebase configuration
├── .firebaserc               # Project settings
├── firestore.rules           # Database security rules
├── storage.rules             # Storage security rules
├── functions/                # Backend Cloud Functions
│   ├── main.py              # Python entry point
│   ├── requirements.txt     # Python dependencies
│   └── uci_engine_handler.py
└── public/                   # Frontend static files
    ├── index.html
    ├── css/
    ├── js/
    └── assets/
```

## Cost Analysis & Optimization Strategy

### Firebase Pricing Breakdown (Spark vs Blaze Plans)

#### Spark Plan (Free Tier) - **RECOMMENDED START**
- **Hosting**: 10GB storage, 10GB/month bandwidth
- **Cloud Functions**: 125,000 invocations/month, 40,000 GB-seconds
- **Firestore**: 50,000 reads, 20,000 writes, 1GB storage
- **Storage**: 5GB total storage
- **Authentication**: Unlimited users

**Estimated Usage for Chess Challenger**:
- **Storage**: ~3GB engines + 100MB frontend = ~3.1GB ✓
- **Functions**: ~10,000 games/month = ~50,000 invocations ✓  
- **Database**: ~20,000 game records = within limits ✓
- **Bandwidth**: 2-3GB/month for moderate traffic ✓

**Result**: Can operate entirely on FREE TIER for first few months!

#### Blaze Plan (Pay-as-you-go) - **WHEN NEEDED**
Only upgrade when exceeding free tier limits.

**Monthly Cost Estimates**:
- **Functions**: $0.40/million invocations (after free tier)
- **Storage**: $0.026/GB/month for files
- **Firestore**: $0.18/100K reads, $0.18/100K writes
- **Hosting**: $0.026/GB for bandwidth (after free tier)

**100 games/day scenario (~3000/month)**:
- Functions: ~150K invocations = $0.10/month
- Storage: 3GB engines = $0.08/month  
- Database: ~60K operations = $0.11/month
- Bandwidth: ~8GB = $0.05/month
- **Total**: ~$0.34/month (within your budget!)

**1000 games/day scenario (~30,000/month)**:
- Functions: ~1.5M invocations = $0.55/month
- Storage: 3GB engines = $0.08/month
- Database: ~600K operations = $1.08/month  
- Bandwidth: ~80GB = $2.08/month
- **Total**: ~$3.79/month (still very affordable!)

### Cost Optimization Strategies

1. **Engine Storage Optimization**:
   - Compress engines with UPX (50-70% size reduction)
   - Use Firebase Storage caching headers
   - Only download engines when needed

2. **Function Efficiency**:
   - Keep engine processes alive between games (connection pooling)
   - Implement engine warm-up to reduce cold starts
   - Use lightweight UCI parsing

3. **Database Optimization**:
   - Only store completed games (not abandoned)
   - Use batch writes for multiple operations
   - Implement client-side caching for engine list

4. **Traffic Management**:
   - Enable Firebase hosting compression
   - Use CDN for static assets
   - Implement reasonable rate limiting

## Security & Performance Configuration

### Firestore Security Rules
```javascript
// Cost-optimized rules - prevent abuse while allowing functionality
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Game records - allow read/write for completed games only
    match /games/{gameId} {
      allow read: if true;
      allow create: if request.resource.data.result != null 
                   && request.resource.data.moves != null
                   && request.resource.data.pgn != null;
      allow update: if false; // No updates to prevent data corruption
      allow delete: if false; // No deletions to preserve history
    }
    
    // Engine stats - read-only for users
    match /engine_stats/{engineName} {
      allow read: if true;
      allow write: if false; // Only functions can update stats
    }
    
    // Rate limiting collection (internal use)
    match /rate_limits/{clientId} {
      allow read, write: if false; // Functions only
    }
  }
}
```

### Cloud Storage Rules
```javascript
// Secure engine storage - read-only for users
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Engine executables - download only
    match /engines/{engineName} {
      allow read: if true;
      allow write: if false; // Admin uploads only
    }
    
    // Game PGN files - read-only archive
    match /games/{gameId}.pgn {
      allow read: if true;
      allow write: if false; // Functions write only
    }
  }
}
```

## Performance Targets & Monitoring

### Performance Goals
- **Page Load**: < 2 seconds first visit, < 1 second cached
- **Move Response**: < 3 seconds for 1000ms engine time
- **Game Start**: < 5 seconds including engine initialization
- **Concurrent Games**: Support 10+ simultaneous games

### Cost Monitoring Setup
```javascript
// Add to Firebase Functions
exports.costMonitor = functions.pubsub
  .schedule('every 24 hours')
  .onRun(async (context) => {
    // Check usage metrics
    const usage = await admin.app().options.credential.getAccessToken();
    
    // Alert if approaching budget limits
    if (dailyCost > budgetAlert) {
      await sendAlert('Approaching daily cost limit');
    }
    
    return null;
  });
```

### Scaling Strategy

#### Phase 1: Launch (Free Tier)
- Target: 10-50 games/day
- Cost: $0/month
- Features: Basic engine battles, PGN recording

#### Phase 2: Growth (Low Blaze)  
- Target: 100-500 games/day
- Cost: $1-5/month
- Features: ELO tracking, game analysis

#### Phase 3: Popular (Medium Blaze)
- Target: 1000+ games/day
- Cost: $10-20/month  
- Features: Tournaments, advanced analytics

#### Emergency Brake (Cost Protection)
```python
# Add to Cloud Functions - automatic shutdown if costs exceed budget
def check_monthly_budget():
    if estimated_monthly_cost > MAX_BUDGET:
        # Temporarily disable expensive features
        disable_new_games()
        send_admin_alert(f"Monthly budget exceeded: ${estimated_monthly_cost}")
```

## Deployment Commands

### Initial Setup
```bash
# Install Firebase CLI (if needed)
npm install -g firebase-tools

# Initialize project
firebase init

# Deploy security rules
firebase deploy --only firestore:rules,storage:rules

# Deploy functions (backend)
firebase deploy --only functions

# Deploy frontend
firebase deploy --only hosting
```

### Development Workflow
```bash
# Local development with emulators
firebase emulators:start

# Deploy to staging (if configured)
firebase use staging
firebase deploy

# Deploy to production
firebase use production  
firebase deploy

# Monitor costs
firebase projects:list
```

## Cost Tracking & Alerts

### Daily Monitoring
1. Check Firebase Console usage dashboard
2. Monitor function invocation counts
3. Track storage bandwidth usage
4. Review Firestore read/write operations

### Weekly Analysis
1. Calculate actual vs projected costs
2. Identify optimization opportunities
3. Adjust rate limits if needed
4. Plan for traffic growth

### Monthly Budget Review
1. Compare actual costs to $20-100 budget
2. Optimize heavy usage patterns
3. Consider architecture improvements
4. Plan scaling strategies

This setup should keep you well within budget while providing a robust, scalable chess engine challenger platform!
```
