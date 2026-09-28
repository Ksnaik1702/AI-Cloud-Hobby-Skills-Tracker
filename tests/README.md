# Automated checks

The standard-library suite covers password hashing, signed session tokens, bounded goal-progress calculation, and the local REST workflow from account creation through skill, goal, practice, analytics, post, like, and comment.

From the project root, run:

    py -m unittest discover -s tests -v

These are local unit and API checks, including the no-photo-upload route behavior, skill and goal editing, configurable goal checkpoints, skill-tagged posts, six-month analytics, and longest-streak output. They are not a full browser or Firebase emulator suite. Firebase Auth, Firestore rules, and Hosting still need an integration smoke check in the Firebase project.
