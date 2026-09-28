# Project brief coverage review

This review compares the supplied “Online Hobby & Skills Tracker with Community Sharing on Cloud” brief with the current implementation. The brief is broad and includes both an achievable student MVP and advanced/optional items. This status describes what the repository implements, not what is merely proposed in the brief.

## Core user experience

| Brief area | Status | Current project |
|---|---|---|
| Accounts and profiles | Partial | Firebase email/password registration and sign-in; users can edit name, bio, and interests. Public profiles and profile pictures are not implemented. |
| Hobby and skill tracking | Covered for MVP | Users can create, edit, list, and delete skills; skills have category, level, target level, description, and status. There is no separate skill-detail screen. |
| Goals and milestones | Partial | Users create, edit, and remove hour-based goals. Each goal saves 1–8 configurable percentage checkpoints; progress derives from practice logs. The dates on which checkpoints were achieved are not stored as separate records. |
| Practice logging | Covered for MVP | Users record skill, minutes, activity, notes, and date. Dashboard derives lifetime, weekly, six-month, and current-month totals, recent activity, and current and longest streaks. |
| Community sharing | Covered for MVP | Signed-in users can post text, optionally tag one of their skills, search loaded posts, filter categories, sort by recency or appreciations, like, comment, and delete their own posts. Photos are intentionally omitted in both modes. |
| Dashboard and analytics | Partial | The dashboard shows total time, active skills, current and longest streaks, completed goals, weekly and six-month charts, monthly total, top practiced skill, configurable goal checkpoints, goals, and recent sessions. Skill distribution, milestone achievement history, and community-engagement totals are not implemented. |

## Cloud and engineering requirements

| Brief area | Status | Current project |
|---|---|---|
| Cloud hosting | Configured | Firebase Hosting serves the static frontend. A deployment must be run by the project owner after changes. |
| Cloud authentication and database | Implemented | Firebase Authentication and Firestore; rules keep profile and personal learning records scoped to the signed-in user. Community posts are available to signed-in users. |
| Cloud object storage and uploads | Intentionally omitted | Firebase Storage requires the Blaze pay-as-you-go plan. To keep the project on a no-billing setup and avoid a quota-limited photo experience, there is no photo picker or upload API in either mode. This means the brief’s object-storage and file-upload requirements are not met. |
| REST APIs | Partial | The local Python/SQLite demo exposes REST-style endpoints. Cloud mode uses the Firebase browser SDK directly rather than a deployed REST backend. |
| Local simulation | Implemented | `py backend/server.py` runs a Python standard-library API backed by SQLite. The repository does not include a separate React/Vite frontend or npm build. |
| Security | Partial | Firebase rules restrict personal records; the local demo hashes passwords and checks ownership. Rate limiting, moderation/reporting, account deletion, and production hardening are not implemented. |
| Testing | Partial | Standard-library unit and local API-flow tests are included. Firebase emulator, browser end-to-end, deployment smoke, and the brief’s full 27-case test matrix are not included. |
| Scale, AI, and serverless processing | Future work | The documentation explains possible scale paths, but there are no deployed Functions, Cloud Run API, AI recommendation service, queues, or scheduled jobs. |

## Separate proof deliverables

The brief also asks for a formal project report, screenshots, a day-by-day development record, resume/LinkedIn material, and a set of interview questions and answers. Those are separate coursework/proof artifacts and are not part of this web application repository yet.

## Overall assessment

The repository covers the central student MVP: accounts, personal skills, goals, practice, progress, and a small authenticated community. It is not a 100% match for the supplied brief. The largest deliberate gap is cloud object storage and image uploads; other notable gaps are public profiles, follows, moderation, separate milestone achievement history, full REST APIs in cloud mode, advanced analytics, serverless jobs, and the separate report/proof deliverables. The no-photo decision is consistent with the project’s no-billing constraint, but it should be disclosed in any course submission because the brief names cloud storage as a required concept.
