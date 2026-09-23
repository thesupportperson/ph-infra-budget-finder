# Performance checks

`pages_static_load.js` is independent of the parser and UI unit tests. It requests the production site's static HTML, CSS, JavaScript, project JSON, and factuality report concurrently.

Profiles:

- `smoke`: peaks at 5 virtual users (VU) for a quick deployment probe.
- `production`: peaks at 50 VUs, lasts 105 seconds, and stops if error rate reaches 1% or p95 request time reaches 2 seconds.

Run against production after a release:

```powershell
$env:BASE_URL = 'https://ph-infra-budget-finder.pages.dev'
$env:PROFILE = 'production'
k6 run tests/performance/pages_static_load.js
```

This validates a bounded traffic level from one load-generator machine. It does not prove a global maximum visitor capacity. Do not use a heavier production test without Cloudflare analytics/observability and explicit approval.
