# Data-source register

## Official Fantasy Premier League API

FPL AI currently uses public Fantasy Premier League endpoints for bootstrap/player metadata, fixtures, event live data and public manager/team history. Data is cached behind the backend gateway with request timeouts and stale fallback, so each browser does not independently hammer the upstream service.

Before commercial/public launch, the project owner must re-review the Premier League/FPL website terms, branding rules, acceptable request volume, attribution expectations and any restrictions on commercial reuse. The current implementation should not be interpreted as legal approval.

## Prediction artifacts

Model output is generated inside this project from approved inputs and published with a versioned manifest. The UI labels these values `Model`, never `Live` or `Official`.

## Product boundary

The MVP does not collect FPL passwords, write to official FPL accounts or automate transfers/chips. Any future source must be added to this register with ownership, license/terms, attribution, refresh interval, failure mode and retention policy before it is enabled in production.
