# Data 360 Ingestion API Part 1 — From the Shire to the Misty Mountains

---

Salesforce Data 360 / Data 360 is vast.

On the surface, it feels welcoming. There are clear paths, familiar features, and plenty of well-documented entry points: connectors, starter use cases, clean demos where everything behaves exactly as you expect.

This is the Shire.

And to be clear, the Shire exists for a reason. It's comfortable. It gets you moving quickly. Most journeys should probably start there.

But if you've spent enough time solving problems beyond the demos, you know what happens next.

Eventually, the road becomes less well-travelled. And then… obscure.

## The Question That Keeps Coming Up

One question comes up again and again:

> "Can Data 360 / Data 360 consume this API? I don't see a connector for it."

These APIs are often a cornerstone of an organisation's data strategy. They've been around for years. They speak HTTPS, return JSON and when they were built, Salesforce connectors weren't exactly top of mind.

Salesforce gives us connectors, and they're genuinely useful. They're the well-worn roads out of Hobbiton: familiar, reliable, predictable.

But the real world doesn't live entirely on paved roads.

At some point, you reach the foothills. And beyond them… the Misty Mountains.

This is where things get interesting.

There are a lot of APIs people want to consume:

- some elegant
- some awkward
- some that feel like they were built by a council of wizards who never met again

Standing at the base of the mountains waiting for "one connector to rule them all" starts to feel less like a strategy and more like wishful thinking.

So I stopped asking which connector exists and started exploring what Data 360 offers natively.

**What does Data 360 give us when there isn't a connector?**

## Choosing an Awkward Dataset on Purpose

To answer that question, I deliberately chose a fun but awkward dataset: [The One API](https://the-one-api.dev/) — a fan-made Lord of the Rings API.

- No enterprise backing
- No Salesforce connector
- No concern for CRM use cases
- Just raw JSON over HTTPS

If this works, anything works.

### Credit Where It's Due

The One API is a non-commercial, open-source project maintained by [Rike](https://x.com/rikecodes) and Mateusz since 2019. It's become a beloved resource for developers learning API integration, and for good reason — it's well-documented, freely accessible, and genuinely fun to work with.

If you use it, consider supporting the project via their [GitHub](https://github.com) or [Buy Me A Coffee](https://www.buymeacoffee.com).

## What The One API Provides

The One API gives us two kinds of data we are going to use on this project:

**Characters** — ~933 named individuals from Tolkien's world:

```json
{
  "_id": "5cd9d533844dc4c55e47afed",
  "name": "Treebeard",
  "race": "Ent",
  "gender": "Male",
  "birth": "YT",
  "height": "15'4",
  "hair": "Leaf, twig and moss like",
  "spouse": "Fimbrethil",
  "wikiUrl": "http://lotr.wikia.com//wiki/Treebeard"
}
```

**Quotes** — ~2,383 lines of dialogue from the films:

```json
{
  "dialog": "Treebeard, some call me.",
  "movie": "The Two Towers",
  "character": "5cd9d533844dc4c55e47afed"
}
```

This is messy, real-world data. Nulls everywhere. Inconsistent formatting. No pagination standards. Perfect for testing what Data 360 can actually handle.

## What Data 360 Gives You

When there's no connector, Data 360 gives you the **Ingestion API** — a contract that says:

> "If you can speak this language, you shall pass."

The gates of Moria, if you will. Speak friend, and enter.

The contract has three parts:

### 1. A Schema (OpenAPI 3.0)

You define what your data looks like. Data 360 is strict about this — flat structures only, specific field types, required naming conventions. See the Data 360 Developer Guide for the full spec.

```yaml
openapi: 3.0.3
info:
  title: LOTR Character Data
  version: 1.0.0

components:
  schemas:
    LotrCharacter:
      type: object
      properties:
        characterId:
          type: string
        name:
          type: string
        race:
          type: string
        gender:
          type: string
        birth:
          type: string
        death:
          type: string
        realm:
          type: string
        height:
          type: string
        hair:
          type: string
        spouse:
          type: string
        wikiUrl:
          type: string
          format: url
        ingestedAt:
          type: string
          format: date-time
```

Key constraints I learned the hard way:

- **No nested objects** — flatten everything
- **All fields must be present** in every record (use empty strings for nulls)
- **DateTime fields are required** for engagement-category data
- **Field names can't use reserved words** or double underscores

### 2. Authentication (Two-Step Token Exchange)

You need a two-step exchange:

```
Step 1: Get Salesforce token
POST {auth_url}/services/oauth2/token
→ Returns: access_token, instance_url

Step 2: Exchange for Data 360 token
POST {instance_url}/services/a360/token
grant_type=urn:salesforce:grant-type:external:cdp
subject_token={salesforce_token}
→ Returns: JWT access_token, Data 360 instance URL (*.c360a.salesforce.com)
```

The second token is what you use for all Ingestion API calls. This isn't obvious from the documentation, and it's the first place most implementations fail.

### 3. The Streaming Endpoint

```
POST https://{dc_instance}/api/v1/ingest/sources/{source}/{object}
Authorization: Bearer {dc_jwt_token}
Content-Type: application/json

{
  "data": [
    { ...record 1... },
    { ...record 2... },
    ...
  ]
}
```

I batch records (200 per request) and the API returns `202 Accepted` immediately. The data appears in Data 360 after the Data Stream refreshes — typically 2-3 minutes.

## And It Worked

After running the ingestion:

- **933 characters** landed in Data 360 as Profile data
- **2,383 quotes** landed as Engagement data
- Records are deduplicated via primary key (idempotent upserts)
- The data is now available for segmentation, automation, and unification

No connector. No middleware. Just a schema, some Python, and the Ingestion API.

In the next article, Part 2 dives deep into the implementation details — how Profile and Engagement data are modeled in Data 360, why the distinction is enforced at the schema level, and how primary keys, foreign keys, and timestamps determine whether your data unifies cleanly or collapses into a lake. We will also share a repo so you can try this yourself

## Not the only road out of the Shire

There are many ways to solve this problem, and people have been doing it for years with tools like:

- MuleSoft
- Informatica
- custom middleware
- iPaaS platforms
- queues, schedulers, pipelines
- Custom LWC's

Those tools all have their place, and in real architectures they're often the right answer.

This series isn't about replacing them. It's about understanding what Data 360 itself gives you with the Ingestion API when you leave the road and step into the mountains:

- an ingestion endpoint
- a schema
- and a clear contract

## What This Means

The Ingestion API isn't a workaround. It's the foundation that connectors are built on.

When you understand it, you stop asking "is there a connector?" and start asking "can I transform this data?"

The answer is usually yes.

In the next article, we'll look at how to model this data — and why the distinction between Profile and Engagement data is the difference between a data lake and a unified customer view.

*Consider this the moment the party leaves the Shire.*

---

**Further Reading:**

- [Data 360 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_quick_start.htm)
- [Data 360 Connectors and Integrations (Trailhead)](https://trailhead.salesforce.com/content/learn/modules/data-cloud-connectors-and-integrations)
- [Data 360 Quick Look (Trailhead)](https://trailhead.salesforce.com/content/learn/modules/data-cloud-quick-look)

---

*Next: The Two Towers — Forging Profiles and Engagements in Data 360*
