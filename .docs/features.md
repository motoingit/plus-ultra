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

# Futuere Scope and Improvements
- use better tech stack
- make app for large audience

- using online drive for sync

- ai integraton
- gogole task integratioin
- googole drive integration
- installaton and unstallation window
- mobile app syncable