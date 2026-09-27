# Hobbyloop

Hobbyloop is a cloud-connected hobby and skills tracker for practicing consistently and sharing progress. It includes a responsive browser app, Firebase Authentication and Cloud Firestore, with a Python/SQLite local demo. Firebase cloud mode is text-only so the free-tier setup does not require Storage billing.

## Current implementation

- Email/password registration and sign-in with Firebase Authentication in cloud mode
- User profiles and private skills, goals, and practice sessions in Cloud Firestore
- Dashboard analytics for practice time, weekly activity, streaks, goal progress, and 25%, 50%, 75%, and 100% goal markers
- Community posts, likes, comments, and a signed-in feed
- Image uploads in local demo mode (JPG, PNG, and WebP under 4.5 MB); cloud posts are text-only on the no-billing setup
- Local Python REST API, SQLite persistence, password hashing, and local image uploads
- Firestore rules that restrict access to the authenticated owner

The app is a student MVP. Persistent milestone records, profile image uploads, follows, moderation/reporting, AI recommendations, scheduled cloud functions, and full Firebase emulator/browser coverage are still future work.

## Run locally

Requirements: Python 3.10+ and a modern browser.

1. Open a terminal in the project folder.
2. Run: py backend/server.py
3. Open http://127.0.0.1:8000.
4. The supplied project config connects to Firebase by default. To use only the local demo, select “Use local demo on this device” on the sign-in screen.

The local database and uploaded images are stored in ignored folders under backend/. They are not included in Git.

## Firebase setup and deployment

1. Copy frontend/firebase-config.example.js to frontend/firebase-config.js and fill in the Firebase web-app settings. This file is ignored by Git.
2. Enable Email/Password in Firebase Authentication and create a Firestore database.
3. Publish firestore.rules in the Firebase Console. The Firebase CLI can also deploy the rules.
4. Firebase Storage is intentionally not enabled because current Firebase requirements place it behind the Blaze pay-as-you-go billing plan. Cloud community posts work without images; local demo mode retains image uploads.
5. Install the Firebase CLI, sign in, and from this folder run: firebase deploy --only hosting,firestore:rules.

The Hosting configuration serves only frontend/; the local Python backend and SQLite files are not deployed. In cloud mode, the browser talks to Firebase Auth and Firestore directly under their security rules. Firebase Hosting provides the static website. No Cloud Functions or Python cloud API are deployed yet.

See docs/FIREBASE_SETUP.md and docs/ARCHITECTURE.md for details. See tests/README.md for the current automated checks.

## Project map

- frontend/ — browser application and Firebase adapter
- backend/ — local REST API and SQLite demo
- cloud/ — Firebase migration notes
- docs/ — setup and architecture
- tests/ — Python standard-library tests
- sample_data/ — synthetic data guidance

## Local REST API

The local backend serves endpoints under /api, including /api/auth/register, /api/auth/login, /api/profile, /api/skills, /api/goals, /api/practice, /api/feed, /api/posts, and /api/analytics/dashboard. Protected requests require a bearer token.

## Security notes

Never commit frontend/firebase-config.js, .env, service-account keys, or user data. Firebase web configuration is intended for browser clients; Firestore and Storage security rules enforce access. Review the rules before production use. This project is an educational MVP and needs further hardening before use with sensitive or large-scale data.
