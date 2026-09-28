# Firebase setup and deployment

## Services used by the cloud mode

- Authentication: Email/Password provider.
- Cloud Firestore: profiles, handles, skills, goals, practice sessions, posts, likes, and comments.
- Firebase Hosting: serves the static files in frontend/.

Cloud mode uses the Firebase browser SDK directly. The Python REST API is for the local SQLite demo; it is not deployed as a cloud API.

## Configure the web app

1. In Firebase Console, open Project settings → General → Your apps and register a Web app if needed.
2. Copy frontend/firebase-config.example.js to frontend/firebase-config.js.
3. Replace the placeholder values with the web app config. Keep the assignment to window.HOBBYLOOP_FIREBASE_CONFIG.
4. Keep firebase-config.js out of Git. Firebase web config identifies the browser app; never put a service-account private key in it.
5. In Authentication → Sign-in method, enable Email/Password.
6. Add localhost and 127.0.0.1 to Authentication → Settings → Authorized domains if you use them for local testing.
7. Create a Cloud Firestore database and publish the project's firestore.rules.

## Keep the Firebase setup on the no-billing plan

Do not enable Cloud Storage for this project while staying on Firebase's Spark plan. Firebase requires Blaze billing to provision/use Cloud Storage for Firebase as of February 3, 2026. Blaze is usage-based and requires a linked billing account; usage can incur charges. Cloud Storage Always Free quotas apply only in the US-CENTRAL1, US-EAST1, and US-WEST1 regions. A Firestore database set to Mumbai does not by itself tell us the region a future Storage bucket would use. See the official [Firebase Storage FAQ](https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024) and [Cloud Storage pricing](https://cloud.google.com/storage/pricing).

The app has no photo upload option in either cloud or local demo mode. It does not deploy Storage rules or make Storage requests.

## Deploy the website

The root firebase.json serves only frontend/, and .firebaserc selects this Firebase project.

1. Install the Firebase CLI and sign in with the Google account that owns the project.
2. Open a terminal in the project root.
3. Deploy Hosting and Firestore rules: firebase deploy --only hosting,firestore:rules

The CLI prints your Hosting URL after deployment. The app requires frontend/firebase-config.js to exist before deployment. That config file remains ignored by Git, so create it again when cloning the repository.

Firebase Hosting deploys only static assets. Cloud mode currently calls Auth and Firestore directly from the browser. No Storage, Functions, Cloud Run API, analytics backend, or server-side scheduled jobs are deployed.

## Verify the live app

Open the Hosting URL and create a test account. Add a skill, create a goal, log a practice session, and publish a text post. Confirm the records in Firestore. Community posts are text-only in both modes.

## Local mode

For the local Python/SQLite demo, run py backend/server.py and visit http://127.0.0.1:8000. Use “Use local demo on this device” on the sign-in page to switch modes.
