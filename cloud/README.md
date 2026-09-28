# Firebase cloud configuration

Cloud mode connects the browser to Firebase Authentication and Cloud Firestore. Firebase Hosting deploys only the static frontend. See docs/FIREBASE_SETUP.md for the setup and deployment flow.

The Python REST API and SQLite database remain the local/offline demo adapter. No server-side Functions or Python API is deployed. Firebase Storage and photo uploads are omitted because Firebase Storage requires the Blaze pay-as-you-go plan. Community posts are text-only in both modes.

Never commit frontend/firebase-config.js, service-account keys, local databases, or user data. The checked-in Firebase rules restrict access by authenticated UID and should be reviewed before production use.
