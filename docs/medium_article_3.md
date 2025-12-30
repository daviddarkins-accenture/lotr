# Medium Article 3 — From Middle-earth to CRM: When External Data Becomes First-Class

*Part 3 of 3: The return of the data*

---

## Recap: The Journey So Far

In Part 1, we ingested a Lord of the Rings API into Salesforce Data 360 using the Ingestion API — no connector, no middleware. 933 characters and 2,383 quotes landed in Data 360.

In Part 2, we forged the two towers of data: **Profiles** (stable identity) and **Engagements** (high-volume activity). We saw why the distinction matters — not just for data modeling, but as the foundation for trustworthy AI.

But data in Data 360 alone isn't the destination.

The real value appears when external data becomes first-class in Salesforce CRM.

---

## The Bridge: Identity Resolution

Data 360 doesn't automatically know how to link external data to your CRM records. You have to build the bridge.

That bridge is **Identity Resolution**.

For our LOTR example, the bridge is simple:

- **Source:** `LotrCharacter.characterId` (from the external API)
- **Target:** `Account.characterId__c` (custom field on Salesforce Account)

When Identity Resolution runs, Data 360 creates a unified profile that links Treebeard's external profile data to his Salesforce Person Account.

![Identity Resolution Configuration](assets/dcstream_newlotrchardloaccountmapping.png)
*Configuring Identity Resolution: Linking LotrCharacter.characterId to Account.characterId__c*

This is where the pattern generalizes. Replace the fields:

| LOTR Example | Real-World Equivalent |
|--------------|----------------------|
| `characterId` | Customer ID, Patient ID, Device ID |
| `LotrCharacter` | External customer profile |
| `Account.characterId__c` | CRM record with matching identifier |

The architecture is the same. Identity Resolution is the bridge that connects external data to CRM.

---

## Automation: Salesforce Flows

Once Identity Resolution links profiles, you can automate CRM record creation.

For our LOTR example, we created a Salesforce Flow that triggers when a new `LotrCharacter` record appears in Data 360:

1. **Trigger:** Data 360 Data Change Event on `lotr_LotrCharacter__dlm`
2. **Action:** Create Person Account
3. **Mapping:** Map Data 360 fields to Account fields:
   - `name__c` → `LastName`
   - `race__c` → `Race__c`
   - `height__c` → `Height__c`
   - `characterId__c` → `characterId__c` (for Identity Resolution)

![Salesforce Flow Configuration](assets/dcstream_newlotrchardlodeploy.png)
*Salesforce Flow automatically creates Person Accounts when Data 360 profiles are created*

When Treebeard's character data lands in Data 360, the Flow creates his Person Account in CRM within minutes.

This is the power of Data 360 automation: external data triggers CRM actions without custom middleware or scheduled jobs.

---

## The UI: Related Lists

Data 360 Related Lists bring Engagement data directly into Salesforce CRM record pages.

For our LOTR example, we configured a Related List that displays Treebeard's quotes on his Account page:

- **Data Model Object:** `LotrQuote` (Engagement DMO)
- **Related To:** `Account`
- **Relationship:** `LotrQuote.characterId` → `Account.characterId__c`
- **Display Fields:** `dialog`, `movie`, `characterName`, `ingestedAt`

![Treebeard's Account Page with Quotes Related List](assets/tb_profile.png)
*Treebeard's Person Account showing Profile data (Character Information) and Engagement data (Quotes) in a unified view*

All 45 quotes from Treebeard appear directly on his Account page, powered by Data 360 Engagement data.

This is the UI that makes external data feel native to Salesforce. Users don't need to leave CRM to see external activity data.

---

## The AI: Agentforce

Here's where the modeling decision from Part 2 pays off.

When you ask Agentforce a question like:

> "Did Treebeard ever talk about Gandalf?"

The agent queries across both:

1. **Identity data** — Treebeard's Person Account (CRM)
2. **Activity data** — Treebeard's 45 quotes (Data 360 Engagement)

With properly modeled Profiles and Engagements, the agent responds with authority, grounded in properly linked data. It doesn't just search CRM fields; it queries the entire unified profile, including all quotes from Treebeard's Engagement DMO.

![Agentforce Query](assets/af.png)
*Using Agentforce to query Treebeard's quotes — the agent reasons over both CRM data and external Engagement data*

This is why unified profiles matter. Not as a buzzword — as the literal foundation for trustworthy AI.

Without the Profile/Engagement distinction, the agent has no reliable way to link quotes to characters. With it, the agent can answer questions that require understanding both *who* someone is and *what* they've done.

---

## The Complete Journey

Let's trace the complete journey from external API to first-class CRM data:

1. **External API** → The One API returns Treebeard's character data
2. **Ingestion API** → Python script sends data to Data 360
3. **Data 360** → Profile (LotrCharacter) and Engagement (LotrQuote) records are created
4. **Identity Resolution** → Data 360 links `LotrCharacter.characterId` to `Account.characterId__c`
5. **Salesforce Flow** → Flow creates Person Account when Data 360 profile is created
6. **Related List** → Quotes appear on Account page via Data 360 Related List
7. **Agentforce** → AI agent queries unified profile across CRM and external data

![Complete Architecture Diagram](assets/dcstream_newlotrchardloaccount.png)
*The complete journey: External API → Data 360 → CRM → Agentforce*

This isn't just integration. It's transformation.

External data becomes as native to Salesforce as any standard object. Users see it in the UI. Flows trigger on it. Agents reason over it.

---

## How to Set This Up Yourself

If you want to replicate this setup, the complete code and configuration is available on GitHub: **[daviddarkins-accenture/lotr](https://github.com/daviddarkins-accenture/lotr)**

The repository includes:

- Python ingestion scripts with the Ingestion API implementation
- OpenAPI 3.0 schemas for both Profile and Engagement data
- Salesforce metadata (Flows, Custom Fields, Related Lists, Flexipages)
- Step-by-step setup instructions in the README

Key setup steps:

1. **Deploy Data Streams** — Configure Profile and Engagement streams
2. **Configure Identity Resolution** — Link external profiles to CRM records
3. **Deploy Salesforce Flow** — Automate Account creation from Data 360
4. **Configure Related Lists** — Display Engagement data on Account pages
5. **Test with Agentforce** — Query unified profiles across CRM and external data

The repository is MIT licensed and designed as a learning POC. All the code is there — including the two-step token exchange, batch ingestion logic, schema definitions, and Salesforce automation.

---

## The Lesson

The Ingestion API isn't just about getting data into Data 360. It's about making external data first-class in Salesforce.

When you model correctly:

- **Identity Resolution** unifies external profiles with CRM records
- **Salesforce Flows** automate CRM actions from external data
- **Related Lists** surface external activity data in CRM UI
- **Agentforce** reasons over unified profiles across systems

This is the architecture that makes external data as native to Salesforce as any standard object.

The journey from random API to first-class CRM data is complete.

---

## What's Next?

This series covered the complete journey:

- **Part 1:** Ingesting external APIs into Data 360 using the Ingestion API
- **Part 2:** Modeling Profiles and Engagements correctly
- **Part 3:** Bridging Data 360 to CRM with Identity Resolution, Flows, Related Lists, and Agentforce

But this is just the beginning.

The same pattern applies to any external data source:
- Customer data from marketing platforms
- Device data from IoT systems
- Transaction data from payment processors
- Activity data from mobile apps

If you can speak the Ingestion API's language, you can make any external data first-class in Salesforce.

---

**Further Reading:**

- [Data 360 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_quick_start.htm)
- [Identity Resolution in Data 360](https://help.salesforce.com/s/articleView?id=sf.c360a_identity_resolution.htm)
- [Data 360 Related Lists](https://help.salesforce.com/s/articleView?id=sf.c360a_related_lists.htm)
- [Salesforce Flows](https://trailhead.salesforce.com/content/learn/modules/flow-basics)

---

*The journey is complete. The data has returned.*
