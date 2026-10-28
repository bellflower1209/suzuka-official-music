# Publication decision 2026-10-28: HOLD

The owner now explicitly permits publication when Chrome151 is included and the candidate is not worse
than production, in addition to the other modern-browser, audio-protection, package and GitHub gates.

## Chrome151 matched comparison: PASS

151.0.7922.34, same origin/track/network settings; fresh contexts; baseline/candidate/candidate/baseline;
135s each. The asagiri-shinobu document/configuration/audio runtime are byte-identical between packages.
Both verified documents were fulfilled identically at the formal origin; actual private delivery was used.
Clock median: baseline134.815s / candidate135.137s. Buffer median: baseline0.325s / candidate0s.
Range median: baseline1317ms / candidate1417ms, within preregistered measurement bounds.
All four pass stop/restart/OFF, stable stopped clock, one Audio, same virtual source, no errors,
64KiB206/no-store/formal-origin CORS, expired-ticket rejection and unsigned403.
No regression was detected under these conditions. The old browser was not excluded.

## Publication remains blocked by real delivery latency

The installed Chrome automatically updated from155 to156.0.8078.48. This run is not a new Chrome155 test.
Chrome156 real-origin playback advanced85.715s during135.126s. Two ranges took29.320s and36.377s.
Corresponding production Worker logs show29.130s and34.330s wall time with3ms CPU each and HTTP206.
The exact upstream/R2/downstream wait location is not proven. Do not assume test-environment causation.
WebKit26.5 passed135s continuous playback/OFF; SW Range observation is unavailable in Playwright WebKit.
The previous exact Chrome155 pass is retained, but the current long production-delivery wait is unresolved.

69 audits PASS. Current Chrome/WebKit display100 states per engine, GA4 transport/URL/title, CLS and portal PASS.
Package802 / old784 retained / protected157 byte-identical / static audio0 / internal references44126 and
fragments275 checked with zero missing. Catalog13 artists/104 works, Shorts98, canonical NEWS85,
27 verified video migrations and9 in progress; BABA NOVA remains catalog-only.

No stage/commit/push/PR/merge/Pages publication, backend change/redeployment, protection weakening or deletion.
Main remains934a63b79a7bdda85f4839aa77d3576a2987ee0a. Terminal36 dirty files remain byte-identical.
Storage17.293GB is retained; no safe deletion is inferred from publication success.

Candidate fixes: instrument auth/R2/first-byte/stream timing safely; evaluate bounded timeout/retry and small
bounded prefetch with authentication, expiry, sequence, origin binding,64KiB,no-store,OFF cancellation intact.
Diagnose and validate rather than guessing or exposing raw public audio. Resume the normal protected PR/CI/
merge/Pages/post-publication path only after the delivery gate is met.


> Historical snapshot. The operator subsequently approved publication with the existing playback delay unresolved. See [owner approval 2026-10-28](publication-owner-approval-20261028.md). This does not claim the delay was fixed.
