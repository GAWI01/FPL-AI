# Data use and commercial release gate

Updated: 2026-09-02

This engineering review is not legal advice. It records the current product behavior and the permissions that must be resolved before charging users or publicly marketing the service.

## Current implementation

- Reads unauthenticated JSON responses from `fantasy.premierleague.com/api` for bootstrap metadata, fixtures, live event points, public manager picks/history, and public transfers.
- Stores only the user's numeric public Team ID and plan history in that user's browser.
- Does not request FPL credentials, write to an FPL account, reproduce player photos, reproduce club badges/crests or copy official shirt artwork; the UI uses original geometric shirt shapes with simple club-colour abstractions.
- Uses club and player names, fixtures, prices, statuses, points, rankings, and other FPL game data in the decision product.

## Official terms reviewed

Re-reviewed on 2026-09-02. No official public-API licence granting public or commercial reuse was identified in the published materials reviewed.

The current [Premier League Terms of Use](https://www.premierleague.com/en/terms-and-conditions) reserve copyright and database rights and state that website/app materials may not be used commercially or reproduced into another database without prior written approval. They also reserve trademarks, logos, and brand names.

The Premier League's official [business, trademark and data contact guidance](https://www.premierleague.com/en/news/102426) directs business proposals to `partnerships@premierleague.com`, says logos/trademarks require express permission, and directs match-data permission requests to Football DataCo.

The separate official [Fantasy Premier League Challenge terms](https://fplchallenge.premierleague.com/help/terms) are not assumed to govern the main FPL game, but reinforce the need for a written scope: they expressly restrict commercial exploitation, automated extraction and use of game data without consent. This is supporting risk evidence, not a substitute for confirmation covering the exact endpoints used by FPL AI.

The [Premier League Privacy Policy](https://www.premierleague.com/en/privacy-policy) describes Fantasy gameplay statistics, rankings and profile details as user data. Even though this beta only reads public manager identifiers, a privacy review is required before server-side accounts, analytics, or persistent manager profiles are introduced.

## Release decision

**Personal/local beta:** technically enabled, with the independent-product disclaimer visible in Settings.

**Public free beta:** do not launch until counsel or the rights holder confirms the intended read/display pattern, naming, disclaimers, caching, retention, and rate limits.

**Paid/commercial SaaS:** blocked pending written approval or an appropriately licensed data source. Public endpoint accessibility is not treated as a commercial licence.

## Required evidence before commercial launch

1. Written response or agreement covering FPL game data used by the product.
2. Match/fixture data licence confirmation where required.
3. Trademark/naming review for “FPL AI”, product metadata, marketing copy, and any club identifiers.
4. Approved retention and cache policy, attribution language, rate limits, and takedown process.
5. Privacy notice and data-processing inventory before adding accounts, telemetry tied to a manager, payments, email, or cloud-synced history.
6. A dated re-review of the official terms immediately before launch.

## Permission request scope

The written request should explicitly disclose and ask approval for:

- a decision-support SaaS using public Team IDs and read-only FPL JSON endpoints;
- the exact official fields displayed or transformed: player/team names, fixtures, prices, status/news, ownership, points, rankings, manager picks/history and live event aggregates;
- derived model projections, recommendations and historical evaluations built from those inputs;
- server-side cache durations, request volume, attribution, retention, territories and free/paid tiers;
- the proposed “FPL AI” product name and the absence of official affiliation;
- use of original geometric club-colour abstractions without crests, logos, photos or replica shirts;
- confirmation of whether Football DataCo or another licensee must separately approve fixture or match data.

The response must identify the rights holder, approved scope, effective date, restrictions and renewal/termination terms. Silence, endpoint accessibility or an informal assumption does not clear this gate.

Until those items exist, deployment artifacts are for private evaluation and technical staging only.
