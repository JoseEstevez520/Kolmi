# Security

Kolmi is self-hosted: each class runs its own instance, so a fix reaches you when you update
yours.

## Reporting a problem

Please don't open a public issue. Use **Report a vulnerability** in this repository's Security
tab, which sends it to the maintainer privately. Say what you found, how to reproduce it and the
version or commit.

## What counts

Anything that exposes notes, accounts or keys: reading another student's raw notes, doing an
admin action as a student, or a secret reaching the repository or the logs.

## If you host an instance

Keep the Supabase keys and `CLASS_CODE` in `.env`, never in git. What the app stores and where
it goes is in [docs/privacy.md](docs/privacy.md).
