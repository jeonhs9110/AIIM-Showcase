# AIIM — AI Influencer Match

> An end-to-end platform that helps marketing teams find the right creator for a campaign — across YouTube, Instagram, and TikTok, with an AI recommendation engine on top.

**Status:** Live demo deployed on Google Cloud.
**Source code:** Private (available on request for recruiters / hiring partners).

---

## What it does

Finding the right influencer for a brief is a research problem. Marketing teams spend days scrolling through platforms, cross-referencing follower counts, cross-checking demographics, and reading comments to guess whether a creator's audience matches a brand's target market. AIIM collapses that into a single search + ranking pipeline:

1. **Discovery** — continuously ingests creators from YouTube Data API, Instagram Graph API, and a dedicated Selenium scraper, normalising them into a unified schema.
2. **Enrichment** — an LLM reads each creator's bio, recent captions, and brand mentions, then structures them into searchable fields: primary language, audience country mix, vertical (beauty / fashion / food / lifestyle / tech), brand-deal history, and monetisation intent.
3. **Matching** — given a brief ("mid-tier K-beauty creator with engaged audience in Southeast Asia"), the recommendation engine returns a ranked shortlist with human-readable reasoning for every pick.

## Current data footprint

| Platform | Creators ingested |
|:---------|---:|
| Instagram | **3,512** |
| YouTube | **1,584** |
| TikTok | 16 (suspended, see note) |
| **Total** | **5,083 unique creators** |

Creators span 14 languages / scripts (Korean, Japanese, Chinese S/T, Thai, Vietnamese, Indonesian, Filipino, Arabic, Hindi, Turkish, Portuguese, Spanish, German, Italian, Russian) — the ingestion pipeline uses native-language monetisation hashtags (`광고`, `スポンサー`, `رعاية`, `publicidade`, ...) to surface channels that English-only searches never reach.

## Tech stack

**Backend**
- **Python 3.10** · FastAPI · SQLAlchemy · Alembic
- **PostgreSQL** (Cloud SQL `db-f1-micro`)
- **Anthropic Claude API** — `claude-haiku-4-5` for demographics enrichment, brand-collab extraction, and the recommendation engine (with prompt caching to keep unit economics sane)
- **Selenium** for Instagram hashtag / commenter graph scraping (resilient human-like pacing, break scheduler, profile-dedup, idempotent upserts to the live DB)

**Frontend**
- **Next.js 14** (App Router, standalone build for Cloud Run)
- **TypeScript** · Tailwind CSS · shadcn/ui
- Server components where they help, client components where they don't

**Data ingestion**
- **YouTube Data API v3** (quota-budgeted daily scraper on Cloud Run Jobs)
- **Meta Graph API / Instagram Business Discovery** (rate-limited at 200 calls/hr)
- **Selenium workers** for the public-IG signal the Graph API doesn't expose (hashtag corpora, commenter graph, bio mentions)

**Cloud / infra**
- **Google Cloud Platform** end-to-end
- **Cloud Run** for backend + frontend (autoscaling, pay-per-request)
- **Cloud SQL Postgres** as the single source of truth
- **Artifact Registry** for container images
- **Cloud Build** for CI
- **Secret Manager** for API keys (never baked into images)

## Architecture at a glance

```
 ┌──────────────────────────────────────────────────────────────┐
 │  Data sources                                                │
 │  ┌──────────┐  ┌──────────┐  ┌────────────────────────────┐  │
 │  │ YouTube  │  │ Meta IG  │  │ Selenium IG workers        │  │
 │  │  API v3  │  │  Graph   │  │  (hashtag + commenter      │  │
 │  │          │  │  API     │  │   graph, parallelised)     │  │
 │  └────┬─────┘  └────┬─────┘  └────────────┬───────────────┘  │
 └───────┼─────────────┼─────────────────────┼──────────────────┘
         ▼             ▼                     ▼
 ┌────────────────────────────────────────────────────────────┐
 │  Ingestion services (Python, idempotent upserts)           │
 │  influencer → platform_account → platform_metadata         │
 │                                                            │
 │  LLM enrichment passes (Claude Haiku, prompt-cached):      │
 │     demographics · brand collabs · vertical classification │
 └───────────────────────────┬────────────────────────────────┘
                             ▼
                     ┌────────────────┐
                     │  Cloud SQL     │
                     │  Postgres      │
                     └───────┬────────┘
                             ▼
             ┌───────────────────────────┐
             │  FastAPI (Cloud Run)      │
             │   /api/search             │
             │   /api/influencer/{id}    │
             │   /api/recommend  (LLM)   │
             │   /api/export/xlsx        │
             └──────────────┬────────────┘
                            ▼
             ┌───────────────────────────┐
             │  Next.js (Cloud Run)      │
             │  Browse · filter · detail │
             │  Excel export · AI match  │
             └───────────────────────────┘
```

## Engineering choices I'm proud of

- **Cost discipline as a first-class concern.** After burning a paid scraper budget in ~a day on a bad cost estimate, I switched to a *probe-one-before-bulk* rule for every paid API, and I track per-call spend in the operational notes so the next decision is informed by real numbers. My write-up in `feedback_cost_discipline.md` is the single most useful doc in the repo.

- **Graceful degradation.** If the Meta Graph API or YouTube quota hits the ceiling mid-run, the ingester commits per-row, logs clean summaries, and resumes on the next invocation. No multi-hour run ever loses work to a mid-run failure.

- **Human-shaped Selenium.** The IG scraper uses μs-precision randomised dwell times, mouse wander, break scheduling ("walked away from the desk" long breaks ~8% of the time), a resilient author-selector hierarchy that survives IG's frequent DOM changes, and persistent Chrome profiles so login state carries across runs. It has been running multi-hour sessions on my personal account for weeks without a single challenge wall.

- **Parallel workers with shared dedup.** A second Selenium worker runs a disjoint hashtag slice in a separate Chrome profile. Both commit to the same Cloud SQL; `platform_account` upserts are idempotent so collision is free.

- **Demo-mode gating.** The public demo keeps the browse / filter / Excel-export paths open, but disables the `/api/recommend` endpoint so visitors can't burn through the Anthropic credits that power it. Same codebase, one env var difference between prod and dev.

- **Multilingual discovery.** Instead of scraping English phrase queries that all return the same 10 top channels, I feed YouTube's `search.list` single-word monetisation hashtags in 14 scripts. First run added 400 channels in 30 minutes; the equivalent English-phrase run had plateaued at ~0 per day.

## Why the code is private

This is a personal portfolio project built on top of a handful of paid APIs (Anthropic, Meta, YouTube) and a scraping stack tuned for a specific account. Publishing the full source would:
- expose rate-limiting workarounds I'd rather not document publicly,
- let bots re-use my prompts and burn through credits,
- leak the DB seed data.

Recruiters / collaborators: happy to give repo access on request. Reach me at the address on my GitHub profile.

## License

All rights reserved. © 2026 jeonhs9110.
