# Firebase cloud configuration

Cloud mode connects the browser to Firebase Authentication and Cloud Firestore. Firebase Hosting deploys only the static frontend. See docs/FIREBASE_SETUP.md for the setup and deployment flow.

The Python REST API and SQLite database remain the local/offline demo adapter. No server-side Functions or Python API is deployed. Firebase Storage is not used by the free-tier configuration because current Firebase policy requires Blaze billing. Cloud posts are text-only; local demo mode supports image uploads.

Never commit frontend/firebase-config.js, service-account keys, local databases, or uploaded user files. The checked-in Firebase rules restrict access by authenticated UID and should be reviewed before production use.
