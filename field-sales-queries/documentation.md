# Field Sales Queries — workflows

Langdock workflow exports (`schema: ldwf`) for turning Slack field-sales list submissions into Jira tickets, tracking them in Google Sheets, and closing the loop in Slack when issues are done.

**Related links** (also in `links.md`):

- Workflow 1 (editor): https://app.langdock.com/workflows/aab23b86-4776-48b4-80fd-83a487baf3f5  
- Workflow 2 (editor): https://app.langdock.com/workflows/5d189d89-f130-46e5-8cf9-c7563e21086a  
- Jira Automation (WOR project): https://people-team.atlassian.net/jira/servicedesk/projects/WOR/settings/automate#/rule/019dd89a-e393-7de4-9c24-2cf9c7780548  

Exports in this folder were last saved on **2026-04-29** (see `meta.exportedAt` in each JSON file).

---

## How the two JSON files work together

| File | Role |
|------|------|
| `Field Sales Queries 1.json` | **Ingestion** — Slack list submission → Jira ticket + **Sheet1** row (`Open`) + confirmation reply. |
| `Field Sales Queries 2.json` | **Reconciliation** — On a schedule, reads **Sheet1**, checks Jira for each **Open** row; when status is **Done** or **Closed**, notifies the Slack thread, archives a row on **Sheet2**, and removes the row from **Sheet1**. |

The workflows do not invoke each other in Langdock. They share the same **spreadsheet** (`1jnhL-Ck1jgSaBKn13k7D_dw2yDnfIvBZBnmLb2Uz9xA`) and the same **Sheet1** column layout so Workflow 2 can consume what Workflow 1 writes.

```mermaid
flowchart TB
  subgraph WF1["Workflow 1 — event-driven"]
    S[Slack list message] --> J1[Jira create WOR-*]
    J1 --> D1[Delay 15s]
    D1 --> SH1[Append Sheet1 row: Open]
    D1 --> R1[Slack reply with ticket link]
  end
  subgraph WF2["Workflow 2 — scheduled"]
    CRON[Every minute] --> RD[Read Sheet1]
    RD --> LOOP[For each Open row]
    LOOP --> J2[Jira get issue]
    J2 --> Q{Done / Closed?}
    Q -->|No| NEXT[Next row]
    Q -->|Yes| R2[Slack thread: completed]
    R2 --> SH2[Append Sheet2: Closed]
    SH2 --> RM[Delete Sheet1 row]
  end
  SH1 -.->|same Sheet1| RD
```

---

## Workflow 1 — end-to-end flow

```mermaid
flowchart LR
  T["Trigger: new message in Slack channel"] --> C{"Condition: Only bot messages"}
  C -->|"subtype = bot_message AND text contains 'filed'"| X["Code: parse list attachment + submitter"]
  C -->|"otherwise"| STOP["Stop — no downstream"]
  X --> J["Action: Find Jira users"]
  J --> A["Agent: Match Jira user → accountId"]
  A --> CR["Action: Create Jira task"]
  CR --> DL["Delay: 15 seconds"]
  DL --> R["Action: Reply to message"]
  DL --> S["Action: Log row to Google Sheets"]
```

**Order of execution**

1. **Trigger** — Listens to Slack channel `C0AEAG522T0`.
2. **Condition (`Only bot messages`)** — Continues only if the message is a bot message whose text includes `filed`.
3. **Code** — Parses the List attachment into fields (`request`, `details`, …) and `submitted_by_name` from the `@Name (` mention pattern in the message text.
4. **Find Jira user** — Searches Jira with the submitter name.
5. **Match Jira user (agent)** — Returns `accountId` (prefers `@sumup.com`).
6. **Create task** — Project **WOR**, issue type from config, summary `{{request}} - #field-sales-queries`, description + Slack `ts` embedded as `_slack_thread_ts:<ts>_`, reporter = matched user.
7. **Delay** — Waits **15 seconds** (allows Jira indexing before downstream steps).
8. **Parallel** — **Reply** with Service Desk portal link and mention; **Sheet1** append (see expected outputs).

**Error handling** — `strategy: stop` on most nodes; failures abort the run.

---

## Workflow 2 — end-to-end flow

```mermaid
flowchart LR
  T["Trigger: scheduled cron"] --> G["Get Sheet1 values"]
  G --> L["Loop: Open rows only + sheet row #"]
  L --> J["Get Jira issue by key"]
  J --> D{"AI: Done or Closed?"}
  D -->|"Not done"| E["Loop end — next item"]
  D -->|"Done"| SL["Reply in Slack thread"]
  SL --> A["Append row to Sheet2"]
  A --> RM["Delete row from Sheet1"]
  RM --> E
```

**Order of execution**

1. **Schedule** — Trigger name in the export is **Every Five Minutes**, but the configured cron expression is **`* * * * *`**, which runs **every minute**. If you intended a slower cadence, adjust the cron in Langdock to match (for example `*/5 * * * *` for every five minutes).
2. **Get open Jira tickets from sheet** — Reads **Sheet1** of the shared spreadsheet.
3. **Loop over tickets** — Builds items from all data rows after the header: keeps rows where status column (index `3`) is **`Open`**, and appends the **Google Sheet row number** as the last element (`i + 2`) for delete-range operations (`currentItem[5]`).
4. **Get Jira issue status** — Uses the ticket key from `currentItem[0]`.
5. **Is ticket Done?** — Prompt-based branch on `getJiraIssue` output: **Done** or **Closed** vs still in progress.
6. **If not done** — Goes to **Loop end** (next iteration).
7. **If done** — **Reply in Slack thread** (`threadTs` and `channelId` from the row) → **Append to Sheet2** (archived “Closed” row) → **Delete** that row from **Sheet1** using the stored row index → **Loop end**.

**Error handling** — Loop end uses `continue` on errors so one bad row may not stop the whole loop; other nodes use `stop` where configured.

---

## Expected outputs — Workflow 1

| Destination | Expected result |
|-------------|-----------------|
| **Jira** | New issue **WOR-*** with summary from the list request + `#field-sales-queries`, description with details and `_slack_thread_ts:<ts>_`, reporter = matched user. |
| **Slack** | Thread reply tagging the submitter (`submitted_by`) with a link to the **Service Desk customer portal** for the ticket: `people-team.atlassian.net/servicedesk/customer/portal/18/<KEY>` (not the generic `/browse/` URL). |
| **Google Sheets — Sheet1** | One new row: **key**, **message `ts`**, channel `C0AEAG522T0`, status **`Open`**, **submitter Slack user id** (`submitted_by`). |

If the bot/`filed` condition fails, nothing is written to Jira, Sheet1, or Slack.

---

## Expected outputs — Workflow 2

| Destination | Expected result |
|-------------|-----------------|
| **Jira** | Read-only: status check only; no issue updates from this workflow. |
| **Slack** | For each row that was **Open** in Sheet1 and is now **Done/Closed** in Jira: a **thread reply** on the original channel/thread with the ticket key and a short completion message. |
| **Google Sheets — Sheet2** | One appended row per closed ticket: **key**, **thread `ts`**, **channel id**, status **`Closed`**, fifth column from `currentItem[4]` (same Sheet1 column as Workflow 1’s fifth field — the append prompt labels it “summary”; the sheet column is whatever Workflow 1 wrote in position 5, typically submitter id). |
| **Google Sheets — Sheet1** | The corresponding **Open** row is **removed** after a successful close path (reply → append Sheet2 → delete). |

Rows that are still not **Done**/**Closed** in Jira stay on Sheet1 and are re-checked on the next run.

---

## Sheet1 row shape (shared contract)

For Workflow 2’s loop and delete logic to work, Sheet1 rows written by Workflow 1 should keep this column order:

| Index | Meaning |
|-------|---------|
| 0 | Jira issue key |
| 1 | Slack thread `ts` |
| 2 | Slack channel id |
| 3 | Status text (`Open` while tracked) |
| 4 | Submitter / fifth metadata column |

Workflow 2 appends a **row index** internally for deletion (`currentItem[5]`; not an extra Sheet1 column).
