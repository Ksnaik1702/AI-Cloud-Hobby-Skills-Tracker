# Architecture and build sequence

## Current cloud mode

Browser
  ├── Firebase Authentication (email/password)
  ├── Cloud Firestore (profiles, skills, goals, practice, posts, likes, comments)
Firebase Hosting serves the static frontend from frontend/

The no-billing Firebase configuration does not use Cloud Storage; community posts are text-only.

The browser's Firebase SDK talks directly to the services. Firestore and Storage security rules check the authenticated UID and restrict writes. Firebase Hosting serves the static app over HTTPS and its CDN. There is no deployed Python API, Cloud Function, moderator service, or server-side analytics job yet.

## Local demo mode

Browser (HTML / CSS / JavaScript)
        │ same-origin JSON REST calls
        ▼
Python ThreadingHTTPServer ── HMAC-signed bearer session
        ├── SQLite: users, skills, goals, practice, posts, likes, comments
        └── Local upload directory (image files)

The API validates inputs and checks user ownership. The local database and uploads are ignored by Git and remain on the developer's computer.

## Feature coverage

- Implemented: account registration/sign-in, profile editing, skills, goals, practice journal, computed dashboard analytics, goal milestone markers, feed, likes, comments, and local-mode image uploads.
- Cloud implementation: Firebase Authentication and Firestore for the account and core records. Firebase Storage is intentionally disabled in the no-billing configuration; cloud posts are text-only, while local mode supports image uploads.
- Still to build: profile-picture uploads, a dedicated milestone editor, follows, moderation/report tools, AI hobby recommendations, server-side streak/badge aggregation, scheduled jobs, and production-grade integration/end-to-end test coverage.
- Deployment: Firebase Hosting configuration serves the static frontend. Deployment must be run by an authenticated project owner.

## Data relationships

User 1──* Skill 1──* Goal
  │         └──* PracticeSession
  └──* Post ──* Comment
         └──* Like (one per signed-in user)

Practice minutes are source events. Dashboard totals, weekly practice, goal progress, and current streak are derived from these events. Goal milestones (25%, 50%, 75%, and 100%) are currently derived from goal progress in the dashboard; persistent milestone records and trusted server-side badge aggregation remain future work.

## Scaling and production work

The cloud database is managed and the static frontend is served through Firebase Hosting's CDN. The current client calculates analytics by reading the signed-in user's records, which is suitable only for a small student project. Larger usage needs server-side aggregates, pagination and indexes, rate limits, structured logs, backups, monitoring, moderation, automated deployment, and load/security review.
