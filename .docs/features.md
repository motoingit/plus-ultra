# PLUS-ULTRA Features & Tab Specification

This document serves as the single source of truth for dashboard tabs, features, data attributes, and navigation layout.

---

## 1. Dashboard Workspace Tabs (Alphabetical Order)

The sidebar arranges main workspace tabs alphabetically by default, supporting drag-and-drop reordering.

| Tab | Icon | Sub-sections / Scope | Key Attributes & Capabilities |
|---|---|---|---|
| **Code** | 💻 | • Code Snippets<br>• CLI Commands<br>• Syntax Reference<br>• DSA Problem Tracker | • 1-click instant clipboard copy button for snippets and CLI commands.<br>• DSA Problem Tracker: URL link, `is_done` (bool), `your_note` (notes), difficulty, tags. |
| **Courses** | 🎓 | • Course Tracker<br>• Certifications<br>• Tutorials | • Course title, platform/provider, total hours/modules, completed count, progress percentage, lecture links, certificates. |
| **Ideas-Doubt** | 💡 | • Problem Statements<br>• Doubts | • **Problem Statements**: Project/app ideas, description, proposed tech stack, milestones, status (`Idea`, `Planned`, `In Progress`, `Completed`).<br>• **Doubts**: Concept/technical doubts, question notes, references, resolution status (`Open`, `Resolved`). |
| **Opportunities** | 🚀 | • Internships<br>• Jobs<br>• Hackathons<br>• Scholarships | • Role/event title, organization, application URL, deadline, eligibility notes.<br>• Application status: `Saved`, `Applied`, `In Progress`, `Accepted`, `Rejected`. |
| **Quick Links** | ⚡ | • Web URLs<br>• Local OS Files & Folders | • Display name, target URI (`https://...` for browser or `/home/...` for local OS files/folders), category, click count.<br>• 1-click launch via default browser or native Linux file manager (`xdg-open`). |
| **Tasks** | 📌 | • Task List<br>• Categories<br>• Reminders<br>• Micro-Timers | • Replaces old "Daily Drop" naming.<br>• Attributes: `title`, `description`, `due_date`, `status` (`Pending`, `In Progress`, `Completed`, `Overdue`), `category_id`.<br>• **Priority / Metadata**: `task_label` (`Optional`, `College`, `No-use`), `critical_level` (`High`, `Medium`, `Low`), `pace_level` (`Long-term`, `Short-term`).<br>• **Cloud Integration**: `is_google_task` (`bool`, prepared for Google Tasks integration). |
| **Settings & Account** | ⚙️ | Pinned at bottom / avatar modal | • Always-on-top toggle, offline-mode toggle, language.<br>• Supabase cloud sync status (last sync time, manual sync trigger, auth). |

---

## 2. Tab Navigation & UX Behavior
- **Default Order**: Alphabetical (`Code` -> `Courses` -> `Ideas-Doubt` -> `Opportunities` -> `Quick Links` -> `Tasks`).
- **Interactive Drag Reordering**: Tabs in the sidebar can be grabbed and dragged to customize order, persisting order in `app_state`.
- **Settings & Account**: Pinned separately at the bottom of the sidebar or as an avatar action button in the top-right header.

---

## 3. Database Architecture (Local-First + Cloud Sync)

### Unified SQLite Local Store & Cache
All features share the single, ultra-fast local SQLite database (`$XDG_DATA_HOME/plus-ultra/plus-ultra.sqlite3`):
- **Zero latency**: Instant reads/writes in 1 millisecond.
- **100% Offline capability**: Works completely offline; local database acts as the offline cache and primary source of truth for the UI.
- **ACID Transactions**: Atomic updates and WAL journal mode (`PRAGMA journal_mode = WAL;`).

### Remote Cloud Store (Phase 7)
- **Supabase (PostgreSQL)** serves as the cloud backup and sync destination.
- Background sync worker compares local `updated_at > last_synced_at` to push/pull differential mutations.

### Schema Evolution: Pattern A (Versioned Migrations)
- Uses SQLite `PRAGMA user_version`.
- Phase 3 implements Migration 1 (`tasks`, `categories`, `reminders`, `reminder_fires`, `app_state`).
- Future columns and feature tables are added via incremental versioned migrations using `ALTER TABLE ADD COLUMN` or `CREATE TABLE`, guaranteeing zero data loss.

---

## 4. Dashboard Window Layout (3-Column Architecture)

Phase 4 implements a structured 3-column desktop layout:
1. **Left Sidebar (Navigation)**:
   - 6 main workspace tabs arranged alphabetically: `Code`, `Courses`, `Ideas-Doubt`, `Opportunities`, `Quick Links`, `Tasks`.
   - Bottom-pinned Settings & Account controls.
2. **Main Center Panel (Workspace Content)**:
   - Header with active tab title, search bar, and "Add New" button.
   - Filter pills (status, critical level, pace level, categories).
   - Item views (cards/table/snippets) with instant action buttons.
3. **Right Sidebar (Notification Panel)**:
   - Dedicated stream of past and unread reminders, system alerts, and notifications.
   - Unread badge indicator.
   - Actions: "Mark All as Read", "Clear All", and individual notification dismissal.
   - Marking notifications as read automatically clears the orange bell indicator on the floating desktop capsule.

```
┌─────────────────┬───────────────────────────────┬──────────────────────┐
│  Left Sidebar   │       Main Center Panel       │    Right Sidebar     │
├─────────────────┼───────────────────────────────┼──────────────────────┤
│ 1. Code         │ Tab content, search bar,      │ Dedicated            │
│ 2. Courses      │ filter pills, item cards,     │ Notification Panel:  │
│ 3. Ideas-Doubt  │ code snippet copy buttons,    │ • Unread list        │
│ 4. Opportunities│ forms, detail dialogs         │ • Unread badge count │
│ 5. Quick Links  │                               │ • "Mark All as Read" │
│ 6. Tasks        │                               │ • "Clear All"        │
│ ─────────────── │                               │                      │
│ ⚙️ Settings     │                               │ (Clearing unread     │
│                 │                               │ removes orange bell) │
└─────────────────┴───────────────────────────────┴──────────────────────┘

```