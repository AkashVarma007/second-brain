# Second Brain — Platform Plan (users, apps, plugins, marketplace)

**Date:** 2026-10-15 · **Status:** draft for review · **Owner:** Akash

This is the master planning document for turning Second Brain from a single-purpose voice-note
gadget into a **small app platform**: a pocket device whose apps you install from a phone-app
marketplace, with NOG the pixel companion levelling up as you get real work done.

It is meant to be edited: change priorities, strike user types, add apps. Each build phase in
[Roadmap](#11-roadmap) gets its own spec and implementation plan in `docs/superpowers/` when it
starts.

Related: [design spec (v1)](../superpowers/specs/2026-07-21-second-brain-design.md) ·
[NOG-OS UI spec](../superpowers/specs/2026-10-14-nog-os-ui-design.md) ·
[hardware brief](../../HARDWARE_BRIEF.md) · UI mock (online, private):
https://claude.ai/artifact/N4j4FnrEww5LbYWzwsV5RV

---

## Contents

1. [Decisions so far](#1-decisions-so-far)
2. [Product vision](#2-product-vision)
3. [User types](#3-user-types)
4. [Same job, different tools: developer vs business analyst vs chairman](#4-same-job-different-tools)
5. [App catalogue](#5-app-catalogue)
6. [What to build first (data-driven)](#6-what-to-build-first)
7. [Platform architecture](#7-platform-architecture)
8. [The plugin model](#8-the-plugin-model)
9. [Phone app and marketplace](#9-phone-app-and-marketplace)
10. [NOG: levelling that fits every user](#10-nog-levelling-that-fits-every-user)
11. [Roadmap](#11-roadmap)
12. [Risks](#12-risks)
13. [Open questions](#13-open-questions)
14. [Research notes and sources](#14-research-notes-and-sources)

---

## 1. Decisions so far

| Topic | Decision | Date |
|---|---|---|
| Look and feel | Keep the arcade/pixel aesthetic, the chibi NOG sprite and levelling up | 2026-10-14 |
| Purpose | Useful first: real problems for real users; the game layer is motivation, not the product | 2026-10-15 |
| Breadth | Not only meetings: a diverse, phone-like set of installable apps for many user types | 2026-10-15 |
| Where the "brain" runs | **Laptop first** (speech-to-text, AI, storage, app logic) | 2026-10-15 |
| Cloud | Allowed later, opt-in per app; **everything local and free at the start** | 2026-10-15 |
| Who builds apps | **First-party first**; format designed so outside developers can be added later | 2026-10-15 |
| Personal or product | **Personal now, built product-ready** | 2026-10-15 |
| Plugin architecture | **Declarative app manifests** drawn by built-in device widgets; logic on the laptop brain (see [§8](#8-the-plugin-model)) | 2026-10-15 (proposed) |
| Identity | **A personal assistant first**; apps are its skills, NOG is its face | 2026-10-15 |
| Autonomy | Internal actions happen automatically; anything that leaves your data (invite, email, message) needs one OK press | 2026-10-15 |
| Conversation | Press TALK, speak; answer on screen **and spoken**; short window to reply again | 2026-10-15 |
| Speaker | **Part of the base hardware** (needed to talk back) | 2026-10-15 |
| Recording | Tap to start / tap to stop by default; hold-to-talk for quick captures | proposed — confirm |
| Screen | **3.2" 320×240 colour TFT** (ILI9341), tight layout: the opening hugs the picture, no front logo band. Body about 103 × 61 × 15 mm (depends on the case). 2.8" / 2.4" compared in CAD v1 and retired | 2026-10-15 |

## 2. Product vision

**One line:** a pocket device that captures what you say and runs the small, focused apps your
day needs, with a pixel companion that grows as you get things done.

**What it is not:** a phone replacement, a meeting-only recorder, or a game console.

**Principles**

1. **Useful in under 3 seconds.** Every app opens to the one thing you need; no scrolling to start.
2. **Voice in, glance out.** Speaking is the main input; the screen is for quick glances and picks.
3. **Works without the laptop for a while.** Capture, timers, checklists, tallies and cached data
   work offline; everything syncs when the brain is reachable.
4. **Private by default.** Audio and notes stay on your own laptop. Cloud is a per-app choice.
5. **Apps are installed, not hard-wired.** The device menu is whatever the user has installed.
6. **One companion across all apps.** Every app can feed NOG; the game layer never blocks the work.
7. **Calm, not noisy.** Few notifications, gentle haptics, no infinite feeds.

### The assistant model

Second Brain is **a personal assistant first**. It takes work off your plate the way a good human
assistant does; the apps are its skills and NOG is its face and voice.

**What it does (modelled on real personal/executive assistants)**

1. **Manages the calendar:** schedules interviews and meetings, finds slots, reschedules, protects focus time.
2. **Tracks timelines:** deadlines, milestones, renewals, birthdays — warned early, not on the day.
3. **Reminds at the right moment:** by time, and by context ("before your 3 pm, you promised Raj the deck").
4. **Follows up:** chases what others owe you and nudges what you owe them.
5. **Prepares you:** a short brief before each meeting, call and day.
6. **Captures and summarises:** meetings, ideas, decisions — so nothing is asked twice.
7. **Drafts:** replies, invites, status updates in your tone, ready for approval.
8. **Answers:** "what did we decide?", "when is the review?", "who is Priya?"
9. **Talks with you:** think out loud and it talks back.

**How it differs from Siri**

| | Siri-style assistants | Second Brain |
|---|---|---|
| Memory | Forgets after the request | Remembers people, projects, promises and preferences |
| Initiative | Waits to be asked | Also speaks first: morning brief, pre-meeting brief, follow-ups |
| Privacy | Voice processed in the cloud | Processed on your laptop |
| Presence | A voice | NOG: a face that levels up with your progress |

**Autonomy: what it may do on its own**

| Level | Examples |
|---|---|
| Automatic | File a capture, set a reminder, summarise a meeting, update a task, prepare a brief |
| Ask first (one OK press) | Send an invite, an email or a message; accept or move a meeting; share minutes |
| Never on its own | Delete data, spend money, anything it is unsure about |

**When it speaks up:** morning brief, 10 minutes before each meeting, when a follow-up is due, an
end-of-day wrap — within a daily interruption budget, and silent during focus time and quiet hours.

**Memory:** people (who, role, last talked, what's owed), projects (status, decisions, next steps),
promises (who owes what by when) and preferences (working hours, tone, priorities). Everything is
visible, editable and deletable from the phone app and dashboard.

**Conversation:** press TALK, speak, release or tap again; the answer appears on screen and is
spoken through the speaker; pressing TALK again within a few seconds continues the same
conversation. Measured 2026-10-15 on the dev laptop (i5-11320H, GTX 1650, 16 GB): an 11 s clip takes
2.1 s to transcribe (faster-whisper `small.en`) and 0.7–1.4 s for the LLM step (`llama3.2:3b`, warm),
so about **3 s per reply** before speech output. The first request after start-up adds ~5 s while
models load, so the brain keeps them loaded.

**Reach, in order:** its own data → your calendar (needed for scheduling) → email drafts → other
connectors, each opt-in.

## 3. User types

34 user types across 8 segments. The *Apps* column uses the IDs from the
[App catalogue](#5-app-catalogue). Core apps (Capture, Notes, Tasks, Reminders, NOG) help everyone
and are only listed where they are central.

| # | Segment | User type | Context | What they'd use it for | Apps |
|---:|---|---|---|---|---|
| 1 | Office & business | **Software developer** | Deep work broken by reviews, standups, on-call | Track CI and PRs without opening the laptop; voice-note bugs mid-flow; standup in 10 s; focus blocks; on-call acknowledgements | C1, C3, P1, P5, W1, W2, U4, C7 |
| 2 | Office & business | **Engineering manager** | Many 1:1s, hiring, delegation | 1:1 notes per report; who owes what; interview scorecards; weekly status to leadership; approvals | C4, W13, W6, P5, W4, C6, P2, C5 |
| 3 | Office & business | **Chairman / CEO / founder** | Little time, many decisions, summary-first | Morning exec brief; 3 numbers that matter; approve on the go; board-meeting minutes; people notes before a meeting | W5, W3, W4, W13, C4, P2, S2, C5 |
| 4 | Office & business | **Business analyst** | Stakeholder workshops, requirements, data | Turn a stakeholder chat into user stories; decision log; KPI glance; checklists for UAT; ask past notes | W8, C4, P6, W3, P7, C7, C3 |
| 5 | Office & business | **Product manager** | Ideas, priorities, cross-team decisions | Idea vault; decisions; requirements; standups; customer-call notes | R1, P6, W8, C4, P5, C3 |
| 6 | Office & business | **Project manager** | Deadlines, risks, follow-ups | Status reports; delegation tracker; risk/decision log; checklists; agenda | P5, W13, P6, P7, P2, C6, C4 |
| 7 | Office & business | **Field sales rep** | On the road, between clients | Visit log; hand out visiting card; follow-ups; expenses; next-meeting glance; time per client | W7, S1, S2, C6, W14, P2, P3 |
| 8 | Office & business | **Consultant / lawyer / CA** | Billing by the hour, client confidentiality | Billable timer; client-call minutes kept local; decision log; 2FA | W9, P3, C4, P6, U4, C6 |
| 9 | Office & business | **HR / recruiter** | Back-to-back interviews | Interview kit; agenda; candidate follow-ups; people notes | W6, P2, C6, S2, C4 |
| 10 | Office & business | **Finance / accountant** | Month-end close, approvals | Month-end checklist; KPI board; approvals; expenses; calculator | P7, W3, W4, W14, U2, C3 |
| 11 | Office & business | **Executive assistant** | Runs someone else's day | Boss's agenda; delegation tracker; reminders; shared lists; meeting notes | P2, W13, C6, P9, C4, C3 |
| 12 | Office & business | **Customer support agent** | Queues, SOPs, breaks | SOP checklists; tally of tickets; quick captures; break reminders | P7, P10, C1, B1, C3 |
| 13 | Office & business | **Designer / marketer / creator** | Ideas, campaigns, presenting | Idea vault; writing sprints; focus; presenter clicker; habits | R1, R2, P1, W12, P4, C3 |
| 14 | Office & business | **Data scientist / researcher** | Long experiments, reading | Focus; hypotheses in idea vault; reading log; job-finished alerts; ask notes | P1, R1, L7, W1, C7, C2 |
| 15 | Healthcare | **Doctor** | Dictation, rounds, privacy | Quick dictation kept local; handover; follow-up reminders; flashcards for CME | C1, W10, C6, L1, C3 |
| 16 | Healthcare | **Nurse** | Shifts, rounds, handovers | SBAR handover by voice; dose-time reminders; tally; checklists | W10, H1, P10, P7, U1 |
| 17 | Education | **School student** | Homework, exams, distraction | Assignments; study timer; flashcards; habits; a short break game | L5, L4, L1, P4, F1 |
| 18 | Education | **University student** | Lectures, budget, group work | Lecture capture; flashcards; quiz me; study timer; budget; shared lists | L2, L1, L6, L4, H4, P9 |
| 19 | Education | **Teacher** | Classes, attendance, parents | Attendance tally; lesson-plan checklist; class timer; parent-meeting notes | P10, P7, U1, C4, C3 |
| 20 | Education | **Researcher / PhD** | Reading, ideas, writing | Reading log; idea vault; writing sprints; ask notes | L7, R1, R2, C7, P1 |
| 21 | Field & trades | **Field technician** | Gloves, noise, checklists | Inspection walk-through; voice defect notes; time per job; maker bench | W11, P7, P3, C1, U6 |
| 22 | Field & trades | **Site supervisor** | Crews, safety, daily logs | Site inspection; headcount tally; delegation; site-meeting notes | W11, P10, W13, C4, C5 |
| 23 | Field & trades | **Delivery rider / courier** | Stops, proof, no distraction | Delivery run checklist; time log; timers (glance only, never while riding) | W17, P3, U1 |
| 24 | Field & trades | **Chef / restaurant staff** | Orders, timers, stock | Orders; many kitchen timers; recipe steps; stock count | W15, U1, H6, W16 |
| 25 | Field & trades | **Shop owner** | Stock, sales, customers | Stock count; orders; expenses; visiting card / payment QR | W16, W15, W14, S1, U3 |
| 26 | Home & personal | **Parent** | Family logistics | Family board; shared lists; kid medication; timers; reminders | H2, P9, H1, U1, C6 |
| 27 | Home & personal | **Older adult** | Memory, medication, reassurance | Medication; check-in to family; big text; where-is-it; read aloud | H1, H7, A1, H8, A2 |
| 28 | Home & personal | **Caregiver** | Someone else's routine | Medication for the cared-for person; handover between carers; reminders | H1, W10, C6, H7 |
| 29 | Health & hobby | **Fitness enthusiast** | Training consistency | Workout log; habits; water; stopwatch | B2, P4, B3, U1 |
| 30 | Health & hobby | **Musician / songwriter** | Ideas strike anywhere | Hum/lyric idea vault; metronome; practice habit | R1, R3, P4 |
| 31 | Health & hobby | **Writer** | Daily word goals | Writing sprints; idea vault; focus | R2, R1, P1, P4 |
| 32 | Health & hobby | **Maker / hobbyist** | Electronics on the bench | Maker bench tools; build checklists; idea vault | U6, P7, R1 |
| 33 | Travel | **Frequent traveller** | Time zones, languages, receipts | World clock; phrasebook; packing checklist; expenses; where I parked | U1, L3, P7, W14, H8 |
| 34 | Accessibility | **Low-vision user** | Voice-first, tactile | Big text + haptics; read aloud; capture by voice | A1, A2, C1, C6 |

**Notes on specific groups**

- **Healthcare:** the strongest case for local-only processing — patient details must not leave
  the laptop. Needs a clear "never sync to cloud" mode and auto-deleting audio.
- **Field & trades:** gloves and noise mean big targets, physical buttons, voice notes that are
  short, and offline operation by default.
- **Drivers/riders:** glance-only, never interactive while moving; this shapes which apps ship.
- **Older adults:** big text, read-aloud and one-press check-ins matter more than app count.
- **Students:** focus and study tools first; games stay short and opt-in.

## 4. Same job, different tools

Even inside one company, people use the device very differently:

| | Software developer | Business analyst | Chairman / CEO |
|---|---|---|---|
| Main question | "Is my build green, and what's blocking me?" | "What did the stakeholders actually ask for?" | "What needs my decision today?" |
| Input style | Short voice notes mid-flow; button presses | Long recordings of workshops; structured follow-up | Almost none: reads summaries, approves, dictates one-liners |
| Information density | Status lights and counts | Detailed lists (stories, decisions) | Three numbers and three priorities |
| Daily touches | Many, short (20+) | Few, long (meeting-length captures) | Few, very short (morning brief, approvals) |
| Key apps | Dev Glance, On-call, Focus, Standup, 2FA | Requirements, Meetings, Decision Log, KPI Board, Checklists | Exec Brief, KPI Board, Approvals, Delegation, People Notes |
| What NOG rewards | Focus hours, PRs reviewed, standups done | Stories written, decisions logged | Approvals cleared, follow-ups closed |
| Must never happen | Interrupting deep work | Losing a workshop recording | Information overload |

The design consequences:

- **Persona bundles:** onboarding asks "what do you do?" and pre-installs a matching bundle
  (Developer pack, Analyst pack, Executive pack, Student pack, …). The user can change anything.
- **Density settings per app:** the same Tasks app can show "3 due today" (executive) or the full
  list (analyst).
- **Notification budget per persona:** developers get fewer interruptions, executives get
  summaries rather than events.

## 5. App catalogue

69 apps in 11 categories. *Users* = how many of the 34 user types rely on it (*all* = core app,
*any* = useful to anyone, not tied to a role). Integrations marked "link" are optional connectors
configured in the phone app; every app still works without them on manual input.

### Core

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| C1 | **Talk** | Press TALK, say anything; it files it (note, task, reminder, idea), answers it or acts on it. Merges Capture and Ask | Brain AI | Records offline, files on sync | all |
| C2 | **Notes** | Browse, search and read cleaned-up notes | Brain | Cached recent | all |
| C3 | **Tasks** | Tasks with priority and due date; tick off on device | Brain | Yes (queued) | all |
| C4 | **Meetings** | Record a meeting; minutes, decisions and action items | Brain AI | Records offline | all |
| C5 | **Daily Brief** | Morning plan + evening recap: done, pending, top 3 tomorrow | Brain AI | Last brief cached | all |
| C6 | **Reminders & Follow-ups** | Time-based nudges; 'chase Sam on Friday' | Brain + device clock | Yes (scheduled on device) | all |
| C7 | **Ask** (part of Talk) | Questions answered from your notes, memory or the local LLM; spoken reply | Brain AI | No | all |
| C9 | **Scheduling** | "Set up interviews with these 3 people next week": proposes slots, invites go out after your OK | Calendar link + brain | Proposals queued | all |
| C8 | **NOG** | Companion: levels, career titles, outfits, streaks | Device + brain | Yes | all |

### Productivity

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| P1 | **Focus** | Deep-work / Pomodoro sessions; NOG works beside you | Device | Yes | 5 |
| P2 | **Agenda** | Today's events, next meeting countdown, one-press record | Calendar link | Cached day | 6 |
| P3 | **Time Log** | 'Start Client A' ... 'stop'; daily timesheet | Device + brain | Yes | 4 |
| P4 | **Habits** | Daily check-ins and streaks | Device | Yes | 5 |
| P5 | **Standup & Status** | Yesterday / today / blockers from your captures; weekly update draft | Brain AI | Last draft cached | 4 |
| P6 | **Decision Log** | Every decision from meetings and captures, searchable | Brain | Cached recent | 4 |
| P7 | **Checklists** | Reusable checklists: SOPs, packing, month-end, pre-flight | Device + brain | Yes | 9 |
| P8 | **Inbox Digest** | Read-only summary of important email | Mail link | Last digest cached | any |
| P9 | **Shared Lists** | Grocery / shopping / to-buy lists shared via the phone app | Brain + phone | Cached | 3 |
| P10 | **Tally** | Clicker counter: attendance, inventory, people, reps | Device | Yes | 4 |

### Work tools

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| W1 | **Dev Glance** | CI/build status, PRs awaiting review, deploys | GitHub/GitLab link | Last state cached | 2 |
| W2 | **On-call** | Alert -> acknowledge; voice incident timeline; postmortem notes | Pager link + brain | Timeline offline | 1 |
| W3 | **KPI Board** | A few key numbers with sparklines from a sheet or BI export | Sheet/CSV link | Cached | 3 |
| W4 | **Approvals** | Approve / decline requests (leave, expenses, POs) with a reason by voice | Workflow link | Queued | 3 |
| W5 | **Exec Brief** | Top 3 priorities, key numbers, who owes what, next board item | Brain AI | Cached | 1 |
| W6 | **Interview Kit** | Structured interview notes and a scorecard per candidate | Brain | Yes | 2 |
| W7 | **Field Visit** | Visit log per customer: notes, next steps, follow-up | Brain | Yes | 1 |
| W8 | **Requirements** | Stakeholder talk -> user stories with acceptance criteria | Brain AI | Records offline | 2 |
| W9 | **Billable Timer** | Client/matter timer with billing notes; export to timesheet | Device + brain | Yes | 1 |
| W10 | **Shift Handover** | Structured handover (e.g. SBAR) dictated and read back | Brain AI | Records offline | 3 |
| W11 | **Inspection** | Checklist walk-through with voice defect notes and pass/fail | Device + brain | Yes | 2 |
| W12 | **Presenter** | Bluetooth slide clicker + talk timer with vibration cues | Device (BLE HID) | Yes | 1 |
| W13 | **Delegation** | Who owes me what, by person and date | Brain | Cached | 5 |
| W14 | **Expenses** | 'Taxi 450, client visit' -> categorised expense list | Brain | Queued | 4 |
| W15 | **Orders** | Take orders by voice or picker; running ticket list | Device + brain | Yes | 2 |
| W16 | **Stock Count** | Count items by voice + tally; export a count sheet | Device + brain | Yes | 2 |
| W17 | **Delivery Run** | Stop-by-stop checklist with proof notes | Brain | Yes | 1 |

### Learning

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| L1 | **Flashcards** | Spaced repetition; decks made from your notes | Device + brain | Yes | 3 |
| L2 | **Lecture Capture** | Record a class -> notes, summary, flashcards | Brain AI | Records offline | 1 |
| L3 | **Phrasebook** | Say it in one language, get it in another; saved phrases | Brain AI | Saved phrases offline | 1 |
| L4 | **Study Timer** | Subject-tagged study sessions and weekly totals | Device | Yes | 2 |
| L5 | **Assignments** | Homework and deadlines with countdowns | Device + brain | Yes | 1 |
| L6 | **Quiz Me** | Questions generated from what you noted this week | Brain AI | Cached quiz | 1 |
| L7 | **Reading Log** | Books/papers, pages, key takeaways by voice | Brain | Yes | 2 |

### Home & personal

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| H1 | **Medication** | Dose schedule, taken / skipped, refill alerts | Device | Yes | 4 |
| H2 | **Family Board** | Chores, kids' rewards, family notes | Brain + phone | Cached | 1 |
| H3 | **Home Control** | Scenes and switches via local Home Assistant | Home Assistant (LAN) | LAN only | any |
| H4 | **Budget** | Personal spend by voice; monthly totals | Brain | Queued | 1 |
| H5 | **Journal** | Gratitude / mood / day log by voice | Brain AI | Records offline | any |
| H6 | **Recipe Steps** | Step through a recipe hands-free with timers | Device + brain | Cached recipe | 1 |
| H7 | **Check-in** | One-press 'I'm OK' / 'need help' to family via the phone app | Phone app | Queued | 2 |
| H8 | **Where Is It** | 'Keys in the blue drawer', 'parked level 3 B12' -> ask later | Brain | Yes | 2 |

### Wellbeing

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| B1 | **Breaks & Breathing** | Paced breathing and break nudges | Device | Yes | 1 |
| B2 | **Workout Log** | Sets/reps by voice, rest timer | Device + brain | Yes | 1 |
| B3 | **Water & Posture** | Gentle reminders through the day | Device | Yes | 1 |

### Creative

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| R1 | **Idea Vault** | Voice ideas tagged by project; lyrics, plots, product ideas | Brain | Records offline | 7 |
| R2 | **Writing Sprints** | Timed sprints with word goals and prompts | Device + brain | Yes | 3 |
| R3 | **Metronome & Tuner** | Click track (needs speaker); tuner via mic | Device | Yes | 1 |

### People

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| S1 | **Visiting Card** | Your card as a QR (and NFC sticker); several cards | Device | Yes | 2 |
| S2 | **People Notes** | 'Met Priya, payments team' -> contact + context + follow-up | Brain | Cached | 3 |
| S3 | **Pet Visits** | Two devices meet over ESP-NOW and swap badges/cards | Device radio | Yes | any |

### Utilities

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| U1 | **Clocks & Timers** | Multiple timers, stopwatch, world clock | Device | Yes | 7 |
| U2 | **Calculator** | Calculator + unit/currency converter | Device | Yes (currency cached) | 1 |
| U3 | **QR Tools** | Show Wi-Fi password, links, payment QR | Device | Yes | 1 |
| U4 | **2FA Codes** | Time-based one-time codes (secure storage) | Device | Yes | 2 |
| U5 | **Weather** | Today + next hours; NOG reacts to rain | Weather link | Cached | any |
| U6 | **Maker Bench** | Wi-Fi/BLE scanner, I2C scanner, logic probe, servo tester | Device | Yes | 2 |

### Fun

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| F1 | **Break Games** | Daily word, 2048, snake — opt-in, short sessions | Device | Yes | 1 |

### Accessibility

| ID | App | What it does | Data from | Offline | Users |
|---|---|---|---|---|---:|
| A1 | **Accessibility** | Big text, high contrast, haptic-only, slower input | Device | Yes | 2 |
| A2 | **Read Aloud** | Reads screens and notes aloud (needs speaker) | Brain TTS | Cached clips | 2 |

**Left out on purpose:** Wi-Fi attacks, card cloning and other offensive "hacker" tools (legal
risk, off-mission); infinite feeds and social media; anything that needs a camera.

## 6. What to build first

Ranked by how many user types each non-core app serves:

1. **Checklists** (P7) — 9 user types
2. **Clocks & Timers** (U1) — 7 user types
3. **Idea Vault** (R1) — 7 user types
4. **Agenda** (P2) — 6 user types
5. **Delegation** (W13) — 5 user types
6. **Habits** (P4) — 5 user types
7. **Focus** (P1) — 5 user types
8. **Expenses** (W14) — 4 user types
9. **Decision Log** (P6) — 4 user types
10. **Standup & Status** (P5) — 4 user types
11. **Time Log** (P3) — 4 user types
12. **Tally** (P10) — 4 user types
13. **Medication** (H1) — 4 user types
14. **Approvals** (W4) — 3 user types
15. **KPI Board** (W3) — 3 user types

**Suggested app waves** (each wave is shippable on its own):

| Wave | Apps | Why |
|---|---|---|
| 0 — Core (preinstalled) | Talk (capture + ask + conversation), Notes, Tasks, Reminders & Follow-ups, Scheduling, Meetings, Daily Brief, NOG | The assistant's everyday skills, for everyone |
| 1 — Broad utilities | Checklists, Clocks & Timers, Focus, Habits, Tally, Idea Vault, Calculator, QR Tools | Serve the most user types; all work offline; prove the widget set |
| 2 — Work packs | Agenda, Standup & Status, Decision Log, Delegation, Time Log, Expenses, Visiting Card, People Notes | Make the professional bundles real |
| 3 — Role packs | Dev Glance, KPI Board, Approvals, Exec Brief, Requirements, Interview Kit, Billable Timer | Persona-specific depth; most need integrations |
| 4 — Life & learning | Flashcards, Lecture Capture, Study Timer, Medication, Family Board, Workout Log, Breaks | Expand beyond the office |
| 5 — The rest | Everything else, prioritised by real usage data from waves 0–4 | |

## 7. Platform architecture

```
            ┌──────────────── PHONE APP (React Native / Expo) ─────────────────┐
            │  Marketplace · My apps · Settings · Inbox · NOG · Pairing        │
            └───────────────────────────┬──────────────────────────────────────┘
                                        │ HTTP on the home/office LAN
                                        ▼
┌─────────────────────────── LAPTOP BRAIN (Python, FastAPI) ──────────────────────────┐
│  Speech-to-text (faster-whisper) · LLM (Ollama) · SQLite store                      │
│  App runtime: installed plugins (manifest + handler) · scheduler · XP ledger        │
│  Catalog cache (from the app repo) · connectors (calendar, GitHub, sheets) — opt-in │
└──────────────────────────────────────┬──────────────────────────────────────────────┘
                                       │ Wi-Fi: HTTP + WebSocket (store-and-forward)
                                       ▼
┌─────────────────────────────── DEVICE (NOG-OS on ESP32-S3) ─────────────────────────┐
│  Widget renderer · app launcher built from installed manifests · input · audio      │
│  Local cache: manifests, last data, queued actions, recordings on SD · NOG engine   │
└─────────────────────────────────────────────────────────────────────────────────────┘
   App catalog = a free public Git repo (index.json + one folder per app), cached by the brain.
```

**Who does what**

| Part | Responsibilities |
|---|---|
| Device | Draw screens from widget trees; run timers, tallies, checklists and capture offline; queue actions; cache data; animate NOG; never runs third-party code |
| Laptop brain | Run app logic (plugin handlers), AI, storage, scheduling, connectors; install/uninstall apps; push manifests and data to the device; keep the XP ledger |
| Phone app | Browse and install apps, configure them, see notes/tasks, pair the device, show notifications |
| Catalog repo | Hosts app packages for free (public Git repo); later accepts outside apps by pull request |

**Connectivity rules**

- Device ↔ brain over Wi-Fi (the existing protocol), found via `secondbrain.local`, with a pairing
  token (already required by spec risk #5).
- Phone ↔ brain over the LAN.
- Away from the laptop the device keeps working from its cache and queues everything.
- Later option: device ↔ phone over Bluetooth as a relay; cloud brain as an opt-in.

## 8. The plugin model

**Choice: declarative manifests, logic on the brain.** An app is a package with a manifest that
describes its menu entry, screens (built from a fixed set of device widgets), data, actions,
triggers, permissions and NOG rewards, plus an optional Python handler that runs on the laptop.

Why (from the research in [§14](#14-research-notes-and-sources)):

| Option | Verdict |
|---|---|
| A. Declarative manifests, logic on hub | **Chosen.** No third-party code on the device; low battery; manifests can be linted automatically; fits the ESP32-S3 |
| B. On-device scripting (Lua/Berry) | **Later, narrow tier** for offline automations, with memory caps and review |
| C. Native loadable modules (ELF) | **No.** No isolation; firmware updates break apps (Flipper's API-version problem) |
| D. Frames rendered elsewhere (Tidbyt) | **Only for rare visuals** (e.g. a chart image); passive and battery-hungry otherwise |

### 8.1 Device widget set (v1)

Every app screen is a tree of these. Adding a widget means a firmware update, so the set is kept
small and versioned.

| Widget | Used by (examples) |
|---|---|
| `list` (rows with icon, title, value, check) | Tasks, Notes, Checklists, Approvals, Orders |
| `detail` (scrolling text) | Notes, Daily Brief, Exec Brief, Recipe Steps |
| `card` (title + 2–4 lines + badge) | Agenda next meeting, KPI tile, Dev Glance status |
| `bignum` (one large number + caption) | Tally, KPI, countdowns |
| `timer` (countdown / stopwatch, haptic cues) | Focus, Clocks, Billable Timer, Presenter |
| `progress` (bar or ring) | Habits, Study Timer, Delivery Run |
| `chart` (sparkline, bars) | KPI Board, Workout Log, Budget |
| `picker` (choose one / yes-no / number) | Approvals, Orders, Inspection pass/fail |
| `capture` (record with level meter) | Capture, Meetings, Lecture, Handover |
| `qr` | Visiting Card, QR Tools |
| `sprite` (animated pixel art) | NOG, app icons, celebrations |
| `toast` / `popup` | Confirmations, XP gains |

Every screen also gets a **button-hint bar** (what OK / BACK / arrows do), which fixes the
"confusing to test" problem found in the first UI build.

### 8.2 Manifest (example)

```json
{
  "id": "focus",
  "name": "Focus",
  "version": "1.0.0",
  "schema": 1,
  "minWidgets": 1,
  "icon": "sprites/focus.txt",
  "category": "Productivity",
  "permissions": ["haptics", "notifications"],
  "menu": { "label": "FOCUS", "badge": "data.today.sessions" },
  "screens": {
    "main": { "widget": "timer", "mode": "countdown", "minutes": "settings.length",
              "hints": { "ok": "Start/Pause", "back": "Exit" },
              "onDone": { "action": "session_done" } },
    "stats": { "widget": "bignum", "value": "data.today.minutes", "caption": "MIN TODAY" }
  },
  "actions": { "session_done": { "handler": "on_session_done", "offline": "queue" } },
  "xp": { "session_done": 15, "dailyCap": 60 },
  "settings": [ { "key": "length", "type": "number", "default": 25, "min": 5, "max": 90 } ]
}
```

- `data.*` bindings are filled by the brain and cached on the device.
- `actions` run on the brain; with `"offline": "queue"` the device stores them until it reconnects.
- `xp` declares what feeds NOG and the daily cap that stops grinding.
- `settings` is rendered as a form in the phone app; the device gets only the values.

### 8.3 Install flow

1. User taps **Install** on an app page in the phone app.
2. The phone shows the app's permissions; the user accepts.
3. The brain fetches the package from the catalog (or its cache) and checks the signature and
   schema version against the device's advertised widget/schema version.
4. The brain installs the handler (Python) into its plugin folder and stores the settings.
5. The brain pushes the manifest and initial data to the device; the device saves them and
   rebuilds its menu. The new app appears with a short NOG celebration.
6. Uninstall reverses it; data export is offered first.

### 8.4 Brain plugin runtime

- Each app: `plugins/<id>/manifest.json` + optional `handler.py` with hooks such as
  `on_install`, `on_action(name, params)`, `data(source)`, `on_schedule(name)`.
- First-party apps run in-process at first; outside apps (later) run in a subprocess with an
  allowlisted API (storage under their own namespace, declared connectors only).
- Shared services offered to every app: AI (transcribe, summarise, extract), storage, scheduler,
  notifications, XP ledger.

### 8.5 Versioning and trust

- `schema` versions the manifest format; the device advertises which schema and widgets it
  supports, and the phone hides apps that need a newer firmware (avoids Flipper-style breakage).
- Packages are signed from day one, even first-party ones.
- The catalog supports more than one feed (lesson from Pebble's 2025 store dispute) and the format
  stays open (lesson from Tidbyt's shutdown).

## 9. Phone app and marketplace

**Stack (proposed):** React Native with Expo and TypeScript, sharing protocol types with the
existing web dashboard. Android first (free to sideload); iOS later.

**Screens**

| Screen | What it does |
|---|---|
| Home | Device status (battery, sync, queue), NOG with level and today's XP, quick actions |
| Marketplace | Categories, persona bundles, search, featured; app page with screenshots rendered by the host render tool, permissions, size, version |
| My apps | Installed apps, menu order on the device, per-app settings, uninstall |
| Inbox | Notes, tasks, meeting minutes, briefs from the brain |
| Onboarding | Pair device + brain; "What do you do?" → recommended bundle |
| Settings | Brain address, privacy (local-only mode, audio retention), backups, firmware update |

**Free marketplace hosting:** a public Git repo with `index.json` and one folder per app
(manifest, handler, sprites, screenshots). The brain caches it; the phone reads it through the
brain. No server costs. Outside developers later submit apps by pull request, reviewed and
linted (Bangle.js model).

**Bundles (examples):** Developer · Analyst · Executive · Sales · Student · Teacher · Healthcare ·
Field · Family · Wellbeing.

## 10. NOG: levelling that fits every user

- **XP comes from real outcomes** each app declares: tasks done, meetings summarised, focus
  minutes, checklists completed, follow-ups closed, cards studied. Each app has a daily XP cap.
- **Career titles adapt to the persona bundle** (all fun, all recognisable):
  - Office: Intern → Associate → Manager → Director → CEO
  - Developer: Intern → Junior → Senior → Staff → Principal
  - Student: Fresher → Sophomore → Senior → Graduate → Professor
  - Healthcare: Trainee → Resident → Specialist → Consultant → Chief
  - Everyone else: Rookie → Regular → Pro → Expert → Legend
- **Outfits unlock with levels** (glasses, tie, lab coat, hard hat, coffee mug) and match the
  persona.
- **Never punishing:** no lost progress for missed days; NOG looks sleepy, not sad.
- **Opt-out:** a "quiet mode" hides XP pop-ups for people who want only the tools.

## 11. Roadmap

Each phase gets its own spec → plan → build cycle. Phases 1–4 need no new hardware.

| Phase | Goal | Done when |
|---|---|---|
| 0 ✅ | Brain + dashboard; NOG-OS UI prototype (15 screens, demo data) | Built and reviewed |
| 1 | Device ↔ brain round trip (old Phase 3) + brain hardening (token, limits, timeouts) | A capture made in the simulator appears as a note in the dashboard |
| 2 | Widget renderer + manifest schema v1 in firmware; Wave-0 core apps re-expressed as manifests; button-hint bar; host render tool draws manifests | Core apps run from manifests; renders match the mock |
| 3 | Brain plugin runtime + local catalog + install from the **web dashboard** | Installing "Focus" from the dashboard adds it to the device menu without reflashing |
| 4 | Phone app v1 (Expo, Android): pairing, marketplace, my apps, inbox | Same install flow from the phone |
| 5 | Wave-1 and Wave-2 apps; persona bundles; career titles | 16 apps installable; 3 bundles |
| 6 | Pocket hardware build (compact board, chosen screen, battery, shell) | Device works a full day away from the desk |
| 7 | Waves 3–4; open the catalog to outside developers (SDK docs, PR review, signing) | First outside app merged |

## 12. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Scope explosion (68 apps) | Nothing ships | Waves; each wave shippable; widget set fixed per firmware version |
| Laptop must be on | Device feels dead away from desk | Offline-first apps, cache + queue, later phone relay / opt-in cloud |
| Widget set too limited | Apps feel samey | Pick widgets from the catalogue (§8.1 covers all 68); add rare visuals via frames |
| Recording consent and privacy | Legal and trust problems | REC indicator, consent reminder, local-only mode, audio auto-delete |
| ESP32 memory for many apps | Crashes, slow menus | Manifests on SD, lazy loading, per-app memory budget |
| Wi-Fi battery drain | Short battery life | Batched sync, sleep between syncs, BLE relay later |
| Store/format lock-in | Dead platform if abandoned | Open format, signed packages, multiple feeds |
| Game layer annoys professionals | Product dismissed as a toy | Quiet mode; XP only from real outcomes; calm copy |

## 13. Open questions

- [x] **Screen:** 3.2" 320×240 colour TFT, tight layout — decided 2026-10-15.
- [ ] **Case design:** pick one of the six modelled cases (walnut, instrument, arcade, clear, egg, sticker bomb) or mix two.
- [ ] **Recording default:** tap-to-start/stop with hold-to-talk for quick notes — confirm.
- [ ] **Phone platform:** Android first, then iOS?
- [ ] **Which persona bundles ship first?** Suggested: Developer, Analyst, Executive, Student.
- [ ] **Connectors to support first** (all optional): calendar, GitHub, Google Sheets/CSV?
- [ ] **Offline window target:** how long should the device be useful without the laptop (a day, a week)?
- [x] **Speaker:** in the base hardware — decided 2026-10-15 (the assistant talks back).
- [ ] **Microphone for meetings:** one INMP441 is fine for dictation but weak across a meeting room; test it, and consider a second mic or the laptop mic for room meetings.
- [ ] **Name:** keep "Second Brain" and "NOG" for the product?

**Physical refinements — after the app and flows work** (noted 2026-10-15):

- Thinner body (~14 mm): battery capacity follows volume, so a flat, wide cell behind the screen keeps
  capacity. A ~1000 mAh LiPo is typically 5 mm thick (503450); the 10 mm 103450 cell is ~1800–2000 mAh.
- Softer side edges and back (pebble profile), not only rounded corners.
- Recessed screen behind thin cover glass (~1 mm lip protects it face-down and in pockets).
- Optional pocket clip, lanyard loop and fold-out desk stand.
- **Device CAD v2 (2026-10-15):** 3.2" screen, tight layout, 15 mm stack; six case designs with
  kickstands, from about 103 × 60 to 108 × 73 mm. **Open: pick the case.** Spec
  `docs/superpowers/specs/2026-10-15-device-cad-v2-design.md`, model `hardware/cad/`. (v1 compared
  2.8" at 109 × 64 and 2.4" at 100 × 56; the first quote of 125 × 77 came from a 2D view drawn at ~4".)

## 14. Research notes and sources

How existing small-screen devices deliver installable apps (searched 2026-10-15; several points
from search summaries rather than full pages):

| Product | Where app code runs | Lesson for us |
|---|---|---|
| LaMetric | Cloud/phone pushes JSON frames to a fixed schema | Fixed schema = trivial security, capped richness |
| Tidbyt | Server-side Starlark renders frames | Great developer experience; company joined Modal and hardware paused — keep the format open |
| Pebble / Core Devices | Native C on watch + JavaScript on phone | Device/phone split works; store-ownership dispute → support several feeds |
| Garmin Connect IQ | Monkey C VM on device | Typed app slots with memory budgets keep a store manageable |
| Flipper Zero | Native .fap files, JS apps | API-version mismatches break apps after firmware updates |
| Bangle.js | JavaScript on device, web app loader | Open repo + loader is cheap; trust from PR review |
| Tactility (ESP32) | Native ELF from SD | Feasible but prototype-grade; no isolation |
| Xiaozhi (ESP32) | Tools = name + schema + callback via MCP | Good shape for device capabilities |

Sources: [Tidbyt joining Modal](https://tidbyt.com/blogs/tidbyt/tidbyt-is-joining-modal) ·
[Tidbyt second life](https://macwright.com/2025/04/12/tidbyt-second-life) ·
[Pixlet](https://github.com/tidbyt/pixlet) ·
[Pebble, Rebble and a path forward](https://ericmigi.com/blog/pebble-rebble-and-a-path-forward) ·
[Rebble in a world with Core](https://rebble.io/2025/10/09/rebbles-in-a-world-with-core.html) ·
[Flipper apps](https://docs.flipper.net/apps) ·
[Flipper apps on SD](https://developer.flipper.net/flipperzero/doxygen/apps_on_sd_card.html) ·
[Connect IQ memory limits](https://forums.garmin.com/developer/connect-iq/f/discussion/4060/understanding-connect-iq-device-memory-limits) ·
[BangleApps](https://github.com/espruino/BangleApps) ·
[Tactility](https://cnx-software.com/2025/01/10/tactility-operating-system-for-the-esp32-microcontroller-family-supports-built-in-and-external-applications) ·
[Xiaozhi MCP](https://github.com/toddpan/xiaozhi-esp32-mcp)

Earlier research (device benchmarks, Flipper/Playdate/Tamagotchi/Pebble Index features, INR parts
pricing) lives in the online roadmap doc:
https://claude.ai/code/artifact/25204d2c-d735-47e7-955e-d02a2b1fc2c9
