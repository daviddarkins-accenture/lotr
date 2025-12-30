# Medium Article 2 — The Two Towers: Forging Profiles and Engagements in Data Cloud

*Part 2 of 3: Why the distinction between identity and activity data is everything*

---

## Recap: We Got the Data In

In the previous article, we ingested a fan-made Lord of the Rings API into Salesforce Data Cloud using the Ingestion API.

**933 characters. 2,383 quotes. No connector. No middleware.**

The Ingestion API accepted our data in batches of 200 records, returned `202 Accepted` immediately, and processed everything asynchronously. Within a short amount of data, the data appeared in Data 360's Data Streams.

But getting data into Data 360 isn't the goal. **Structure** is the goal.

Most Data 360 failures happen after ingestion, when teams model everything as Profile data or flatten identity and activity into a single object.

And in Data 360, structure isn't discovered — it's forged.

---

## Two Towers, Two Kinds of Data

The Lord of the Rings API gives us two fundamentally different things:

**Characters** — Named individuals with relatively stable attributes.

```json
{
  "_id": "5cd9d533844dc4c55e47afed",
  "name": "Treebeard",
  "race": "Ent",
  "birth": "YT",
  "height": "15'4",
  "hair": "Leaf, twig and moss like",
  "spouse": "Fimbrethil"
}
```

**Quotes** — Things those characters said. Moments. Context.

```json
{
  "dialog": "Side? I am on nobody's side because nobody's on my side little Orc.",
  "movie": "The Two Towers",
  "character": "5cd9d533844dc4c55e47afed"
}
```

At first glance, it's all just lore.

But these are two fundamentally different categories of data. Treating them the same would collapse the entire model.

Teams commonly get this wrong by treating events as Profiles, flattening everything into one object "for speed," or using Engagements as mini-profiles with identity fields. These patterns work until they don't — unification degrades silently, automation breaks on identity resolution drift, and AI Agents amplify the mistakes with false confidence.

![Treebeard](assets/treebeard.png)
*For these examples we are going to use my favourite Lord of the Rings character — Treebeard*

---

## The First Tower: Profiles

Characters map to **Profile** data in Data 360.

![Treebeard's Profile in Salesforce CRM](assets/tb_profile.png)
*Treebeards Profile Data eg attributes on a Person Account*

*NOTE: We used a Flow to create a Person Account Salesforce CRM record when the Data Stream populated via the Ingestion API*

Profile data represents identity:

- Relatively stable over time
- Descriptive rather than transactional
- Something other data can safely attach to

This is the foundation everything else depends on.

```yaml
LotrCharacter:
  type: object
  properties:
    characterId:
      type: string
      description: Unique identifier (primary key)
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

Data 360 is strict about Profile data. Schemas are enforced. Fields are required. Identifiers must be consistent.

It can feel unforgiving.

That's because it is.

For this pattern, all schema fields must be present in every record — even if the source data has nulls, you send empty strings. The Data Stream configuration uses:

- Category: **Profile**
- Primary Key: `characterId`
- Record Modified Field: `ingestedAt`
- Refresh Mode: **Upsert** (for idempotent updates)

Profile mistakes are expensive and sticky. Fixing a bad Profile model later is reconstruction, not refactoring — you're rebuilding identity from scratch while downstream systems depend on the broken foundation. Identity resolution rules drift, automation triggers on wrong records, and the unified profile becomes unreliable.

If identity is loose:

- Unification fails
- Automation misfires
- AI loses grounding

The first tower has to stand, or everything behind it falls.

![Treebeard's Profile in Salesforce CRM](assets/tb_profile.png)
*Treebeard's Person Account showing Profile data (Character Information) and Engagement data (Quotes) in a unified view.*

---

## The Second Tower: Engagements

Quotes map to **Engagement** data.

![Treebeard's Engagement Data - Quotes Related List](assets/tb_engage.png)
*Treebeards Engagement Data eg associated / related lists on a Person Account*

*NOTE: The Quotes Related List (highlighted) shows Engagement data linked to Treebeard's Salesforce CRM Person Account Record — all 45 quotes visible on the Person Account page [limited to the last 7 days by default]. This uses the Data 360 related list functionality*

Engagement data represents activity:

- High-volume
- Timestamped
- Only meaningful when tied back to a profile

There are 45 quotes from Treebeard alone. They change nothing about *who* Treebeard is — but they reveal *what he does*.

```yaml
LotrQuote:
  type: object
  properties:
    quoteId:
      type: string
      description: Unique identifier for each quote
    characterId:
      type: string
      description: Foreign key linking to the character
    dialog:
      type: string
      description: The quote text
    movie:
      type: string
      description: Which film the quote is from
    characterName:
      type: string
      description: Denormalized for display
    ingestedAt:
      type: string
      format: date-time
```

The Data Stream configuration uses:

- Category: **Engagement** (required for Related Lists in Salesforce)
- Primary Key: `quoteId`
- Event Time Field: `ingestedAt`
- Refresh Mode: **Upsert**

Modeling quotes as engagements keeps them lightweight and scalable. Get the foreign key wrong, and engagements orphan — they exist but can't be linked to identity, making them invisible to automation and agents.

---

## Forging the Link

The real work isn't defining the towers separately.

It's forging the relationship between them.

The API gives us a character ID. That becomes the shared identifier:

![Identity Resolution Diagram](assets/dcstream_newlotrchardlomap.png)

Data 360 does not infer intent — inconsistent identifiers silently degrade unification without error messages. Identity resolution matches fail, but the system doesn't tell you. Automation runs on partial data. Agents answer questions using mislinked context.

The relationship extends into Salesforce CRM through Identity Resolution, which links `LotrCharacter.characterId` to `Account.characterId__c`. The implementation details — field mapping, Data Stream configuration, Related List setup — are covered in the GitHub repository.

This is where the pattern generalizes to real-world systems.

---

## Why This Matters for Agentforce

Here's where the modeling decision pays off.

When you ask an AI Agent in Agentforce a question like:

> "Did Treebeard ever talk about Gandalf?"

The Agent needs two things:

1. **Identity** — who are we talking about? eg Treebeard and his characherid
2. **Context** — what activity is associated with that identity? eg the Quotes/LotrQuote associated to Treebeard/LotrCharacter

If identity is unreliable, the agent can't ground its answer. It might conflate customers, miss signals, or hallucinate context.

If activity isn't properly linked, the agent has no history to draw from.

Agents fail confidently when Profile and Engagement are poorly separated — they'll answer with authority while hallucinating context from mislinked data. The agent won't error. It will synthesize plausible-sounding answers from broken relationships, and users won't know until the answers are wrong.

This is why unified profiles matter. Not as a buzzword — as the literal foundation for trustworthy AI.

![Agentforce Query](assets/af.png)
*Using Agentforce to find out what Treebeard said in his Quotes.*

---

## How to Set This Up Yourself

If you want to replicate this setup, the complete code and configuration is available on GitHub: **[daviddarkins-accenture/lotr](https://github.com/daviddarkins-accenture/lotr)**

The repository includes:

- Python ingestion scripts with the Ingestion API implementation
- OpenAPI 3.0 schemas for both Profile and Engagement data
- Salesforce metadata (Flows, Custom Fields, Related Lists)
- Step-by-step setup instructions in the README

---

## The Lesson

Data modeling in Data 360 isn't optional complexity. It's the contract that makes everything downstream work.

Get it wrong, and you have a data lake. Get it right, and you have unified profiles that power automation, personalization, and AI.

The distinction between Profile and Engagement isn't academic. It's architectural:

- **Profile data** (Characters) = stable identity, foundation for everything
- **Engagement data** (Quotes) = high-volume activity, only meaningful when linked
- **Identity Resolution** = the bridge that connects external data to CRM
- **Related Lists** = the UI that makes engagement data visible in Salesforce

When you model correctly:

- Data 360 can unify profiles across systems
- Salesforce Flows can trigger on external data
- Related Lists can display engagement data on Account pages
- AI agents can reason over both identity and activity

In the final article, we'll look at what happens when this data leaves Data Cloud and enters CRM — and why that's where the real value appears.

---

*Next: From Middle-earth to CRM — When External Data Becomes First-Class*
