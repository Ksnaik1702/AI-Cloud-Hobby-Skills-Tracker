# Architecture and build sequence

## Current cloud mode

Browser
  ├── Firebase Authentication (email/password)
  ├── Cloud Firestore (profiles, skills, goals, practice, posts, likes, comments)
Firebase Hosting serves the static frontend from frontend/

The no-billing Firebase configuration does not use Cloud Storage; community posts are text-only.

The browser's Firebase SDK talks directly to the services. Firestore security rules check the authenticated UID and restrict writes. Firebase Hosting serves the static app over HTTPS and its CDN. There is no deployed Python API, Cloud Function, moderator service, or server-side analytics job yet.

## Local demo mode

Browser (HTML / CSS / JavaScript)
        │ same-origin JSON REST calls
        ▼
Python ThreadingHTTPServer ── HMAC-signed bearer session
        ├── SQLite: users, skills, goals, practice, posts, likes, comments

The API validates inputs and checks user ownership. The local database is ignored by Git and remains on the developer's computer. Community posts are text-only.

## Feature coverage

- Implemented: account registration/sign-in, profile editing, skill create/edit/delete, goals with configurable saved milestone percentages and edit/delete, practice journal, total/weekly/six-month analytics, current and longest streak, text-only community feed with tags/search/category filters/popularity sorting, likes, and comments.
- Cloud implementation: Firebase Authentication and Firestore for the account and core records. Firebase Storage and photo uploads are omitted so both modes remain text-only and avoid requiring a billing account.
- Still to build: separate achievement-history records, follows, public profiles, moderation/report tools, AI hobby recommendations, server-side streak/badge aggregation, scheduled jobs, and Firebase emulator/browser test coverage.
- Deployment: Firebase Hosting configuration serves the static frontend. Deployment must be run by an authenticated project owner.

## Data relationships

User 1──* Skill 1──* Goal
  │         └──* PracticeSession
  └──* Post ──* Comment
         └──* Like (one per signed-in user)

Practice minutes are source events. Dashboard totals, weekly and six-month practice, goal progress, and current and longest streak are derived from these events. Each goal saves its chosen percentage checkpoints (default 25%, 50%, 75%, and 100%); achieved checkpoint history and trusted server-side badge aggregation remain future work.

## Scaling and production work

The cloud database is managed and the static frontend is served through Firebase Hosting's CDN. The current client calculates analytics by reading the signed-in user's records, which is suitable only for a small student project. Larger usage needs server-side aggregates, pagination and indexes, rate limits, structured logs, backups, monitoring, moderation, automated deployment, and load/security review.
