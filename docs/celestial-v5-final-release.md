# SUZUKA CELESTIAL GATE V5 — final release preflight

Approved visual baseline: `43435dc93361d0e722541db3d3122211d34e3dcb` on `feature/celestial-gate-redesign`. The user explicitly authorized final verification, branch push, PR, CI, main merge and GitHub Pages publication on 2026-10-10. This document records preflight evidence; production confirmation is recorded separately after deployment.

## Official profiles

The user supplied `TETSUHIGE_公式画像.jpg.png` and `LEON_VAIL_公式画像.jpg.png` on Desktop. Both are PNG files, despite the `.jpg` portion of their names. The iron duo image is 1374×1145; LEON VAIL is 1278×1230. Exact original bytes are retained in `images/official-originals/`. The complete composition is encoded proportionally as quality-90 WebP for the canonical profile and quality-81 WebP at 480/960 pixels for the existing directory and home gates. No face, clothing, identity, cropping or other ten official images were changed.

Canonical fields: `artists[].image`, `imageAlt`, `imageWidth`, `imageHeight`. Original and optimized SHA-256, actual supplied filename and registration evidence: `assets/data/official-image-registrations.json`. Existing thumbnail manifests are extended only for these two artists. The 12 official profiles are present on their artist pages, directory and home gate insets; metadata and image sitemap are regenerated.

## Corrections

- Generate the error document canonical, Open Graph URL and JSON-LD identity from the actual `/404.html` route, retaining `noindex, follow` and excluding it from the public sitemap.
- Use root-relative 404 resource URLs, because GitHub Pages serves this document at arbitrary missing URL depths. Chrome and WebKit tested a nested missing URL at 390/768/1440 pixels, including the photographic background and usable settings.
- Replace the pre-delivery TETSUHIGE blank-image constraint with validation of its user-provided official registration and both original/optimized hashes. Member names remain strictly 源治・虎徹. A mismatched original hash fails.
- Validate exact canonical/thumbnail coverage and retained original hashes for both delivered profiles. A bad 404 canonical/JSON-LD identity fails the SEO audit.
- Add PR validation to the existing Pages workflow. PR builds execute the existing checks plus reproducibility and SEO; Pages configuration, artifact upload and deployment run only outside PR events. PR concurrency cannot displace production runs.
- The first PR CI run exposed an implicit local-only Pillow dependency in the regeneration audit. The workflow now explicitly uses Python 3.12 and installs pinned `requirements-build.txt` (Pillow 12.2.0). The audit remains enabled; no content or audit condition is weakened.

## Local verification

- 307 content pages: 303 indexed routes and 4 noindex routes; The existing Google ownership verification file and tracked legacy `index 3.html` are outside these generated routes and remain unchanged.
- 12 artists, 82 works, 31 public lyrics. Canonical records are unchanged except the four official image fields for the two supplied artists. The public sitemap is unchanged.
- Chrome/WebKit × 390/768/1440 pixels: 1,842 page views; no broken local images, overflow, page JavaScript errors or console warnings/errors detected.
- All 12 normal portals in both engines pass, including world/destination picture continuity. Candidate sound opt-in, timing, volume, mute and NOX low-pass filtering pass. Skip, Escape, keyboard focus, back, BFCache, short motion, reduced-motion, data saver, storage denial, navigation failure and audio failure fallbacks pass. Formal-audio failure cases use inert mocks, not a real formal Ver.2 asset.
- Automated WCAG 2 A/AA checks: 307 pages, zero detected violations; dialog checks also pass in both engines at all three widths. This is not a claim of complete manual accessibility certification.
- Internal HTML references: no missing resource or anchor. 175 external anchor URLs returned HTTP 2xx; this tests reachability, not every external page's content.
- 32 JavaScript and 23 CSS files parse. Second-generation changed/deleted counts are zero.
- Three fresh home measurements: local PC LCP median 140 ms; simulated mobile (390px/DPR2, 1.6 Mbps down, 150 ms latency, CPU ×4) median 2,764 ms, CLS 0. These are laboratory measurements, not field Core Web Vitals.
- 61 audit/test commands: 59 pass; the two historical failures below remain unchanged from the approved baseline. All 44 Pages validation commands pass locally.
- Existing 226 image/environment/audio files and other ten profile manifest entries retain their hashes. All 788 pre-existing untracked names and 496 locally readable protected file hashes are preserved; none is staged for release.

## Residual risks

| Item | Cause / impact | Required follow-up |
|---|---|---|
| `audit_20260924_sync.py` | Demands 9/24 counts (10 artists, 64 works, 4 upcoming, 19 lyrics) from today's 12/82/0/31 canonical data. Reproduces on the approved baseline. No identified present-site regression. | Separate immutable historical fixtures from current-source invariants. Do not rewrite current data or historical expectations merely to pass. |
| `audit_linkcore_releases.py` | Compares current publication state to the immutable 9/24 snapshot; verified 10/2 publication of 世代を越えて、ママへ conflicts with its old upcoming state. Same baseline failure. | Maintain the original snapshot; build a separate current-state audit using formal distribution evidence. |
| Formal heavy Ver.2 | `assets/audio/door-heavy-v2.wav` remains absent and unregistered. Candidate is explicitly `new-candidate-not-adopted`; navigation works silently when unavailable. | Supply and formally adopt the actual Ver.2 file if required. |
| Physical iPhone/Android | No connected physical devices available. Chrome and WebKit emulation pass. | Check physical Safari/Chrome and audible comfort on devices; do not claim completed real-device QA. |

The user permits publication with accurately reported known audit/device risks. None of these findings is hidden by altering canonical works, lyrics, distribution status or the historical audit expectations. Publication requires a successful PR build, a fresh main ancestry check, and a successful Pages deployment followed by live verification. No destructive or force push is needed.
