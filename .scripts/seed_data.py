"""Demo dataset seeding and unseeding utility for PLUS-ULTRA workspace.

Lives in .scripts/ outside the primary package src tree.
Provides standalone CLI to populate or remove demo records across all tabs.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Ensure 'src' is in sys.path when executed directly
_src_dir = Path(__file__).resolve().parents[1] / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from plus_ultra import config  # noqa: E402
from plus_ultra.database.connection import (  # noqa: E402
    get_connection,
    transaction,
)

# Known signatures of seeded demo data for selective unseeding
DEMO_CATEGORY_NAMES = [
    "College",
    "Systems & OS",
    "Projects",
    "Personal",
    "Career",
]

DEMO_CODE_TITLES = [
    "Python Atomic File Write",
    "Rust RAII Scoped Mutex Guard",
    "C POSIX Shared Memory & Mmap",
    "Go Goroutine Worker Pool with Context",
    "Bash Safe Unofficial Strict Mode",
    "Kill Process on TCP Port",
    "Inspect Process File Descriptors & Sockets",
    "Find Largest Directories On Filesystem",
    "Git Interactive Rebase & Autosquash",
    "Systemd Service Real-Time Log Follow",
    "SQLite WAL & Pragmas",
    "Modern Python Type Hinting & Protocols",
    "Docker Multi-Stage Build Pattern",
    "Makefile Automatic Variables Reference",
    "Two Sum (LeetCode #1)",
    "Course Schedule (LeetCode #207)",
    "LRU Cache (LeetCode #146)",
    "Trapping Rain Water (LeetCode #42)",
    "Number of Connected Components in Graph (LeetCode #323)",
    "Median of Two Sorted Arrays (LeetCode #4)",
]

DEMO_COURSE_TITLES = [
    "Operating Systems: Three Easy Pieces (OSTEP)",
    "Database Management Systems & Transactions",
    "Modern Python Software Architecture",
    "MIT 6.004 Computation Structures",
    "Stanford CS144 Introduction to Computer Networking",
    "Distributed Systems Engineering (MIT 6.824)",
    "3Blue1Brown: Essence of Linear Algebra",
    "Rust Book: Fearless Concurrency & Systems Programming",
]

DEMO_IDEA_TITLES = [
    "Real-time Top-bar System Monitor Plasmoid",
    "SQLite Vector Search Extension",
    "Local Offline Knowledge Graph Extractor",
    "Zero-Copy Linux IPC Shared Memory Ring Buffer",
    "Automatic Wallpaper Tint-based Dark Theme Generator",
    "Legacy File Sync Daemon",
    "Why Tkinter on XWayland falls back to fixed bitmap font?",
    "How does WAL mode handle checkpointing under read loads?",
    "Can eBPF kprobes inspect TLS traffic before encryption?",
    "Can eBPF kprobes inspect TLS traffic before socket encryption?",
    "Difference between O_SYNC and fsync() under ext4",
    "Difference between O_SYNC and fsync() under ext4 journal modes",
]

DEMO_OPP_TITLES = [
    "Google Summer of Code 2026",
    "Smart India Hackathon (SIH) 2026",
    "Systems Software Engineering Intern",
    "Linux Foundation Mentorship Program (LFX)",
    "CERN Openlab Summer Student Programme",
    "Jane Street Systems Software Engineer (Linux/Core)",
    "Rust Foundation Community Fellowship Grant",
    "ICPC Regional Collegiate Programming Contest",
]

DEMO_LINK_NAMES = [
    "GitHub Dashboard",
    "LeetCode Problem Set",
    "Python Official Docs",
    "arXiv CS / Systems Papers",
    "Kernel.org Documentation",
    "Project Workspace Directory",
    "Application Config Directory",
    "System Logs Directory",
    "System Resource Monitor (htop)",
    "Git Branch Status & Log",
]

DEMO_TASK_TITLES = [
    "OS Lab Concurrency Semaphore Assignment",
    "DBMS B+ Tree Index Optimization",
    "Linux Kernel Module Rootkit Detector",
    "eBPF Network Packet Filter Daemon",
    "Build Wayland Native Desktop Overlay",
    "Portfolio Website & Technical Blog Deployment",
    "Daily Ergonomic Posture & Eye Break",
    "Weekly DSA Contest & Retrospective",
    "Apply to GSoC & Linux Foundation Mentorship",
    "Revise Computer Architecture & Cache Notes",
]


def seed_demo_workspace_data(
    conn: sqlite3.Connection, force: bool = False
) -> dict[str, int]:
    """Seed initial sample data for all workspace tabs if empty or forced."""
    now = datetime.now(UTC).isoformat()
    seeded_counts: dict[str, int] = {}

    # 1. Code items
    cur = conn.execute("SELECT COUNT(*) FROM code_items WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
        demo_code = [
            (
                uuid.uuid4().hex,
                "Snippets",
                "Python Atomic File Write",
                (
                    "import os, tempfile\n"
                    "with tempfile.NamedTemporaryFile("
                    "'w', dir='.', delete=False) as f:\n"
                    "    f.write(data)\n"
                    "    tmp_name = f.name\n"
                    "os.replace(tmp_name, target_file)"
                ),
                "python",
                "Easy",
                0,
                "",
                "Atomic file write prevents corruption on power loss.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Snippets",
                "Rust RAII Scoped Mutex Guard",
                (
                    "use std::sync::{Arc, Mutex};\n"
                    "let counter = Arc::new(Mutex::new(0));\n"
                    "let c = Arc::clone(&counter);\n"
                    "std::thread::spawn(move || {\n"
                    "    let mut num = c.lock().unwrap();\n"
                    "    *num += 1;\n"
                    "});"
                ),
                "rust",
                "Medium",
                0,
                "https://doc.rust-lang.org/book/ch16-03-shared-state.html",
                "Guaranteed lock release on scope exit via Drop trait.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Snippets",
                "C POSIX Shared Memory & Mmap",
                (
                    'int fd = shm_open("/myshm", O_CREAT | O_RDWR, 0666);\n'
                    "ftruncate(fd, 4096);\n"
                    "char *ptr = (char *)mmap(NULL, 4096, "
                    "PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);\n"
                    'sprintf(ptr, "Hello from shared memory");\n'
                    "munmap(ptr, 4096);\n"
                    "close(fd);"
                ),
                "c",
                "Medium",
                0,
                "",
                "High performance zero-copy IPC between processes.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Snippets",
                "Go Goroutine Worker Pool with Context",
                (
                    "func worker(ctx context.Context, jobs <-chan int, "
                    "results chan<- int) {\n"
                    "    for {\n"
                    "        select {\n"
                    "        case <-ctx.Done():\n"
                    "            return\n"
                    "        case j, ok := <-jobs:\n"
                    "            if !ok { return }\n"
                    "            results <- j * 2\n"
                    "        }\n"
                    "    }\n"
                    "}"
                ),
                "go",
                "Medium",
                0,
                "",
                "Bounded concurrency pool with clean cancellation.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Snippets",
                "Bash Safe Unofficial Strict Mode",
                (
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "IFS=$'\\n\\t'\n"
                    "trap 'echo \"Error at line $LINENO\" >&2' ERR"
                ),
                "bash",
                "Easy",
                0,
                "http://redsymbol.net/articles/unofficial-bash-strict-mode/",
                "Prevents silent errors, unset variable reads, and pipe masks.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CLI Commands",
                "Kill Process on TCP Port",
                "lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9",
                "bash",
                "Easy",
                0,
                "",
                "One-liner to terminate zombie dev servers.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CLI Commands",
                "Inspect Process File Descriptors & Sockets",
                "ls -la /proc/$PID/fd && ss -tlpn",
                "bash",
                "Easy",
                0,
                "",
                "Diagnose leaked sockets, open pipes, and disk files.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CLI Commands",
                "Find Largest Directories On Filesystem",
                "du -ahx / 2>/dev/null | sort -rh | head -n 25",
                "bash",
                "Easy",
                0,
                "",
                "Quickly locate runaway logs and disk consumption.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CLI Commands",
                "Git Interactive Rebase & Autosquash",
                "git rebase -i --autosquash HEAD~5",
                "bash",
                "Easy",
                0,
                "",
                "Clean up feature branches before merging PR.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CLI Commands",
                "Systemd Service Real-Time Log Follow",
                "journalctl -u plus-ultra -f -n 100",
                "bash",
                "Easy",
                0,
                "",
                "Stream live systemd logs with priority filtering.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Syntax Reference",
                "SQLite WAL & Pragmas",
                (
                    "PRAGMA journal_mode = WAL;\n"
                    "PRAGMA foreign_keys = ON;\n"
                    "PRAGMA busy_timeout = 5000;"
                ),
                "sql",
                "Easy",
                0,
                "",
                "Concurrency and integrity defaults for SQLite.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Syntax Reference",
                "Modern Python Type Hinting & Protocols",
                (
                    "from typing import Protocol, runtime_checkable\n\n"
                    "@runtime_checkable\n"
                    "class Resizable(Protocol):\n"
                    "    def resize(self, width: int, height: int) -> None:\n"
                    "        ..."
                ),
                "python",
                "Easy",
                0,
                "https://peps.python.org/pep-0544/",
                "Structural subtyping / duck typing with compile-time checks.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Syntax Reference",
                "Docker Multi-Stage Build Pattern",
                (
                    "FROM python:3.12-slim AS builder\n"
                    "WORKDIR /app\n"
                    "COPY pyproject.toml .\n"
                    "RUN pip install --user .\n\n"
                    "FROM python:3.12-slim\n"
                    "WORKDIR /app\n"
                    "COPY --from=builder /root/.local /root/.local\n"
                    'CMD ["python", "-m", "plus_ultra"]'
                ),
                "bash",
                "Easy",
                0,
                "",
                "Minimizes container image attack surface and footprint.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Syntax Reference",
                "Makefile Automatic Variables Reference",
                (
                    "$@  # Target name\n"
                    "$<  # First prerequisite\n"
                    "$^  # All prerequisites\n"
                    "$?  # Prerequisites newer than target"
                ),
                "bash",
                "Easy",
                0,
                "https://www.gnu.org/software/make/manual/",
                "Essential cheat-sheet for robust build systems.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Two Sum (LeetCode #1)",
                (
                    "class Solution:\n"
                    "    def twoSum(self, nums: list[int], "
                    "target: int) -> list[int]:\n"
                    "        seen = {}\n"
                    "        for i, n in enumerate(nums):\n"
                    "            if target - n in seen:\n"
                    "                return [seen[target - n], i]\n"
                    "            seen[n] = i"
                ),
                "python",
                "Easy",
                1,
                "https://leetcode.com/problems/two-sum/",
                "Single-pass hash table with O(n) time and O(n) space.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Course Schedule (LeetCode #207)",
                (
                    "class Solution:\n"
                    "    def canFinish(self, numCourses: int, "
                    "prerequisites: list[list[int]]) -> bool:\n"
                    "        # Topological sort with Kahn's algorithm or DFS\n"
                    "        pass"
                ),
                "python",
                "Medium",
                0,
                "https://leetcode.com/problems/course-schedule/",
                "Directed graph cycle check for prerequisites.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "LRU Cache (LeetCode #146)",
                (
                    "from collections import OrderedDict\n\n"
                    "class LRUCache(OrderedDict):\n"
                    "    def __init__(self, capacity: int):\n"
                    "        self.capacity = capacity\n"
                    "    def get(self, key: int) -> int:\n"
                    "        if key not in self: return -1\n"
                    "        self.move_to_end(key)\n"
                    "        return self[key]"
                ),
                "python",
                "Medium",
                1,
                "https://leetcode.com/problems/lru-cache/",
                "Doubly-linked list with hash map for O(1) get and put.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Trapping Rain Water (LeetCode #42)",
                (
                    "class Solution:\n"
                    "    def trap(self, height: list[int]) -> int:\n"
                    "        left, right = 0, len(height) - 1\n"
                    "        l_max, r_max = 0, 0\n"
                    "        ans = 0\n"
                    "        while left < right:\n"
                    "            if height[left] < height[right]:\n"
                    "                l_max = max(l_max, height[left])\n"
                    "                ans += l_max - height[left]\n"
                    "                left += 1\n"
                    "            else:\n"
                    "                r_max = max(r_max, height[right])\n"
                    "                ans += r_max - height[right]\n"
                    "                right -= 1\n"
                    "        return ans"
                ),
                "python",
                "Hard",
                0,
                "https://leetcode.com/problems/trapping-rain-water/",
                "Two-pointer approach in O(n) time and O(1) memory.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Number of Connected Components in Graph (LeetCode #323)",
                (
                    "class UnionFind:\n"
                    "    def __init__(self, n: int):\n"
                    "        self.parent = list(range(n))\n"
                    "        self.count = n\n"
                    "    def find(self, x: int) -> int:\n"
                    "        if self.parent[x] != x:\n"
                    "            self.parent[x] = self.find(self.parent[x])\n"
                    "        return self.parent[x]"
                ),
                "python",
                "Medium",
                1,
                "https://leetcode.com/problems/number-of-connected-components/",
                "Disjoint Set Union (DSU) with path compression.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "DSA Problem Tracker",
                "Median of Two Sorted Arrays (LeetCode #4)",
                (
                    "class Solution:\n"
                    "    def findMedianSortedArrays(self, nums1: list[int], "
                    "nums2: list[int]) -> float:\n"
                    "        # Binary search partition O(log(min(m, n)))\n"
                    "        pass"
                ),
                "python",
                "Hard",
                0,
                "https://leetcode.com/problems/median-of-two-sorted-arrays/",
                "Logarithmic binary search partitioning.",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO code_items ("
                "id, category, title, content, language, difficulty, is_done, "
                "url, notes, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_code,
            )
        seeded_counts["code_items"] = len(demo_code)

    # 2. Courses
    cur = conn.execute("SELECT COUNT(*) FROM courses WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
        demo_courses = [
            (
                uuid.uuid4().hex,
                "Operating Systems: Three Easy Pieces (OSTEP)",
                "University",
                "Remzi Arpaci-Dusseau",
                12,
                8,
                "https://pages.cs.wisc.edu/~remzi/OSTEP/",
                "Virtualization, Concurrency, and Persistence.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Database Management Systems & Transactions",
                "University",
                "Prof. Partha Pratim Das",
                10,
                6,
                "https://example.edu/dbms",
                "Relational algebra, B+ Trees, ACID, WAL logging.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Modern Python Software Architecture",
                "Other",
                "ArjanCodes",
                8,
                5,
                "https://docs.python.org/3/",
                "Clean architecture, SOLID principles, testing with pytest.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "MIT 6.004 Computation Structures",
                "University",
                "MIT OCW",
                16,
                4,
                "https://ocw.mit.edu/courses/6-004-computation-structures/",
                "Digital circuits, processor pipeline, and memory hierarchy.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Stanford CS144 Introduction to Computer Networking",
                "University",
                "Nick McKeown",
                10,
                10,
                "https://cs144.github.io/",
                "Packet switching, TCP/IP stack, congestion control.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Distributed Systems Engineering (MIT 6.824)",
                "YouTube",
                "Robert Morris",
                18,
                3,
                "https://pdos.csail.mit.edu/6.824/",
                "Raft consensus, MapReduce, fault tolerance, Paxos.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "3Blue1Brown: Essence of Linear Algebra",
                "YouTube",
                "Grant Sanderson",
                15,
                15,
                "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
                "Geometric intuition for vectors, matrices, and eigenvectors.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Rust Book: Fearless Concurrency & Systems Programming",
                "Other",
                "Steve Klabnik & Carol Nichols",
                20,
                12,
                "https://doc.rust-lang.org/book/",
                "Ownership, lifetimes, traits, smart pointers, unsafe Rust.",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO courses ("
                "id, title, platform, instructor, total_modules, "
                "completed_modules, url, notes, created_at, updated_at, "
                "is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_courses,
            )
        seeded_counts["courses"] = len(demo_courses)

    # 3. Ideas & Doubts
    cur = conn.execute(
        "SELECT COUNT(*) FROM ideas_doubts WHERE is_deleted = 0;"
    )
    if force or cur.fetchone()[0] == 0:
        demo_ideas = [
            (
                uuid.uuid4().hex,
                "Idea",
                "Real-time Top-bar System Monitor Plasmoid",
                "Minimal floating Linux desktop widget reading /proc/stat.",
                "Python, /proc, Wayland",
                "In Progress",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Idea",
                "SQLite Vector Search Extension",
                "Embeddings index inside standard sqlite3 with SIMD.",
                "C, SQLite, SIMD",
                "Idea",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Idea",
                "Local Offline Knowledge Graph Extractor",
                "Extract code symbols and graph relations into SQLite via AST.",
                "Python, SQLite, AST, Tree-sitter",
                "Idea",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Idea",
                "Zero-Copy Linux IPC Shared Memory Ring Buffer",
                "Circular ring buffer with atomic futex synchronization.",
                "C, Linux shm_open, futex",
                "In Progress",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Idea",
                "Automatic Wallpaper Tint-based Dark Theme Generator",
                "Extract dominant palette from desktop background via k-means.",
                "Python, PIL, X11, Wayland",
                "Implemented",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Idea",
                "Legacy File Sync Daemon",
                "Backup tool replaced by rsync and Borg.",
                "Python, rsync, inotify",
                "Archived",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Doubt",
                "Why Tkinter on XWayland falls back to fixed bitmap font?",
                "Tkinter font lookup fails silently on missing font names.",
                "XWayland, fontconfig, Tk",
                "Resolved",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Doubt",
                "How does WAL mode handle checkpointing under read loads?",
                (
                    "Active readers lock earlier WAL frames until transactions "
                    "commit."
                ),
                "SQLite WAL, concurrency",
                "Open",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Doubt",
                "Can eBPF kprobes inspect TLS traffic before encryption?",
                "User-space uretprobes on SSL_read / SSL_write capture plain.",
                "eBPF, kprobe, OpenSSL, uretprobe",
                "Investigating",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Doubt",
                "Difference between O_SYNC and fsync() under ext4",
                "O_SYNC synchronizes both data and metadata synchronously.",
                "Linux ext4, VFS, POSIX",
                "Resolved",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO ideas_doubts ("
                "id, kind, title, description, tech_stack_or_ref, status, "
                "created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_ideas,
            )
        seeded_counts["ideas_doubts"] = len(demo_ideas)

    # 4. Opportunities
    cur = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE is_deleted = 0;"
    )
    if force or cur.fetchone()[0] == 0:
        demo_opps = [
            (
                uuid.uuid4().hex,
                "Google Summer of Code 2026",
                "Google Open Source",
                "Internship",
                "https://summerofcode.withgoogle.com",
                "2026-11-15",
                "Applied",
                "Submitted project proposal on open source system tooling.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Smart India Hackathon (SIH) 2026",
                "Ministry of Education",
                "Hackathon",
                "https://sih.gov.in",
                "2026-12-01",
                "Saved",
                "Hardware & Software edition student innovation challenge.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Systems Software Engineering Intern",
                "Red Hat Linux",
                "Internship",
                "https://redhat.com/jobs",
                "2026-11-30",
                "In Progress",
                "Interview round 1 scheduled for next week.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Linux Foundation Mentorship Program (LFX)",
                "Linux Foundation",
                "Fellowship",
                "https://lfx.linuxfoundation.org",
                "2026-11-25",
                "Saved",
                "Mentorship on Linux kernel tooling and virtualization.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "CERN Openlab Summer Student Programme",
                "CERN",
                "Internship",
                "https://openlab.cern/summer-student-programme",
                "2027-01-31",
                "Saved",
                "High-performance computing and distributed particle data.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Jane Street Systems Software Engineer (Linux/Core)",
                "Jane Street",
                "Job",
                "https://www.janestreet.com/join-jane-street/position/core-dev",
                "2026-12-15",
                "Saved",
                "Low-latency systems development, OCaml, and Linux kernel.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Rust Foundation Community Fellowship Grant",
                "Rust Foundation",
                "Grant",
                "https://foundation.rust-lang.org/grants/",
                "2026-12-10",
                "Applied",
                "Grant funding for open-source async ecosystem tooling.",
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "ICPC Regional Collegiate Programming Contest",
                "ACM ICPC",
                "Contest",
                "https://icpc.global",
                "2026-11-05",
                "Accepted",
                "Team registered for regional competitive programming finals.",
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO opportunities ("
                "id, title, organization, kind, url, deadline, status, "
                "notes, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_opps,
            )
        seeded_counts["opportunities"] = len(demo_opps)

    # 5. Quick Links
    cur = conn.execute("SELECT COUNT(*) FROM quick_links WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
        demo_links = [
            (
                uuid.uuid4().hex,
                "GitHub Dashboard",
                "https://github.com",
                "Web",
                14,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "LeetCode Problem Set",
                "https://leetcode.com/problemset/all/",
                "Web",
                9,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Python Official Docs",
                "https://docs.python.org/3/",
                "Web",
                18,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "arXiv CS / Systems Papers",
                "https://arxiv.org/corr",
                "Web",
                5,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Kernel.org Documentation",
                "https://www.kernel.org/doc/html/latest/",
                "Web",
                7,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Project Workspace Directory",
                str(config.get_data_dir()),
                "Local Folder",
                22,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Application Config Directory",
                str(config.get_config_dir()),
                "Local Folder",
                11,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "System Logs Directory",
                str(config.get_state_dir()),
                "Local Folder",
                6,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "System Resource Monitor (htop)",
                "htop",
                "CLI Script",
                15,
                now,
                now,
                0,
            ),
            (
                uuid.uuid4().hex,
                "Git Branch Status & Log",
                "git status -s && git log -n 5 --oneline",
                "CLI Script",
                8,
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO quick_links ("
                "id, name, target_uri, category, click_count, created_at, "
                "updated_at, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                demo_links,
            )
        seeded_counts["quick_links"] = len(demo_links)

    # 6. Categories, Tasks & Reminders
    cur = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_deleted = 0;")
    if force or cur.fetchone()[0] == 0:
        categories_to_seed = [
            ("College", "#00e5ff"),
            ("Systems & OS", "#3b82f6"),
            ("Projects", "#8b5cf6"),
            ("Personal", "#10b981"),
            ("Career", "#f59e0b"),
        ]
        cat_map: dict[str, str] = {}
        for cat_name, cat_color in categories_to_seed:
            cat_cur = conn.execute(
                "SELECT id FROM categories WHERE name = ? AND is_deleted = 0;",
                (cat_name,),
            )
            cat_row = cat_cur.fetchone()
            if not cat_row:
                cat_id = uuid.uuid4().hex
                with transaction(conn) as c:
                    c.execute(
                        "INSERT INTO categories ("
                        "id, name, color, created_at, updated_at, is_deleted) "
                        "VALUES (?, ?, ?, ?, ?, 0);",
                        (cat_id, cat_name, cat_color, now, now),
                    )
                cat_map[cat_name] = cat_id
            else:
                cat_map[cat_name] = cat_row[0]

        t_ids = {i: uuid.uuid4().hex for i in range(1, 11)}

        demo_tasks = [
            (
                t_ids[1],
                cat_map["College"],
                "OS Lab Concurrency Semaphore Assignment",
                "Implement reader-writer lock using POSIX named semaphores.",
                "2026-10-25 18:00",
                "In Progress",
                "College",
                "High",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[2],
                cat_map["College"],
                "DBMS B+ Tree Index Optimization",
                "Analyze query plans and optimize secondary composite scans.",
                "2026-10-30 23:59",
                "Pending",
                "College",
                "Medium",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[3],
                cat_map["Systems & OS"],
                "Linux Kernel Module Rootkit Detector",
                "Hook sys_call_table to scan memory and verify call integrity.",
                "2026-11-15 12:00",
                "In Progress",
                "Systems & OS",
                "High",
                "Long-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[4],
                cat_map["Systems & OS"],
                "eBPF Network Packet Filter Daemon",
                "Attach XDP socket filter to drop SYN flood packets at driver.",
                "2026-12-01 17:00",
                "Pending",
                "Systems & OS",
                "Medium",
                "Long-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[5],
                cat_map["Projects"],
                "Build Wayland Native Desktop Overlay",
                "Prototype wlr-layer-shell surface client using Python CFFI.",
                "2026-10-28 20:00",
                "In Progress",
                "Projects",
                "High",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[6],
                cat_map["Projects"],
                "Portfolio Website & Technical Blog Deployment",
                "Deploy static blog on Cloudflare Pages with OS articles.",
                "2026-10-15 14:00",
                "Completed",
                "Projects",
                "Low",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[7],
                cat_map["Personal"],
                "Daily Ergonomic Posture & Eye Break",
                "Stand up, 20-20-20 eye rest rule, and hydration stretch.",
                "2026-10-18 16:00",
                "Pending",
                "Personal",
                "Low",
                "Short-term",
                1,
                now,
                now,
                0,
            ),
            (
                t_ids[8],
                cat_map["Personal"],
                "Weekly DSA Contest & Retrospective",
                "Join LeetCode biweekly contest and solve 3 problems.",
                "2026-10-24 21:30",
                "Pending",
                "Personal",
                "Medium",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
            (
                t_ids[9],
                cat_map["Career"],
                "Apply to GSoC & Linux Foundation Mentorship",
                "Draft proposals for tooling and submit PR contributions.",
                "2026-11-20 23:59",
                "In Progress",
                "Career",
                "High",
                "Long-term",
                1,
                now,
                now,
                0,
            ),
            (
                t_ids[10],
                cat_map["College"],
                "Revise Computer Architecture & Cache Notes",
                "Review MESI cache coherence, TLB hierarchy, and pipelining.",
                "2026-10-14 11:00",
                "Completed",
                "College",
                "Low",
                "Short-term",
                0,
                now,
                now,
                0,
            ),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO tasks (id, category_id, title, description, "
                "due_date, status, task_label, critical_level, pace_level, "
                "is_google_task, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                demo_tasks,
            )
        seeded_counts["tasks"] = len(demo_tasks)

        # Seed linked reminders
        demo_reminders = [
            (uuid.uuid4().hex, t_ids[1], "2026-10-24 09:00", now, now, 0),
            (uuid.uuid4().hex, t_ids[3], "2026-11-10 10:00", now, now, 0),
            (uuid.uuid4().hex, t_ids[5], "2026-10-27 15:00", now, now, 0),
            (uuid.uuid4().hex, t_ids[7], "2026-10-18 15:45", now, now, 0),
            (uuid.uuid4().hex, t_ids[9], "2026-11-18 12:00", now, now, 0),
        ]
        with transaction(conn) as c:
            c.executemany(
                "INSERT INTO reminders ("
                "id, task_id, remind_at, created_at, updated_at, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, ?);",
                demo_reminders,
            )
        seeded_counts["reminders"] = len(demo_reminders)

    return seeded_counts


def unseed_demo_workspace_data(
    conn: sqlite3.Connection, hard_delete: bool = True
) -> dict[str, int]:
    """Remove demo seeded records while preserving user-created entries."""
    unseeded_counts: dict[str, int] = {}

    def _execute_unseed(table: str, col: str, values: list[str]) -> int:
        placeholders = ",".join("?" for _ in values)
        query_sel = (
            f"SELECT COUNT(*) FROM {table} "  # noqa: S608
            f"WHERE {col} IN ({placeholders});"
        )
        with transaction(conn) as cur:
            cur.execute(query_sel, values)
            cnt = cur.fetchone()[0]
            if cnt > 0:
                if hard_delete:
                    query_del = (
                        f"DELETE FROM {table} "  # noqa: S608
                        f"WHERE {col} IN ({placeholders});"
                    )
                    cur.execute(query_del, values)
                else:
                    query_upd = (
                        f"UPDATE {table} SET is_deleted = 1 "  # noqa: S608
                        f"WHERE {col} IN ({placeholders});"
                    )
                    cur.execute(query_upd, values)
            return cnt

    # 1. Unseed demo tasks & cascade to their reminders
    with transaction(conn) as cur:
        q_marks = ",".join("?" for _ in DEMO_TASK_TITLES)
        cur.execute(
            f"SELECT id FROM tasks WHERE title IN ({q_marks});",  # noqa: S608
            DEMO_TASK_TITLES,
        )
        task_ids = [r[0] for r in cur.fetchall()]
        if task_ids:
            rem_marks = ",".join("?" for _ in task_ids)
            if hard_delete:
                cur.execute(
                    f"DELETE FROM reminders "  # noqa: S608
                    f"WHERE task_id IN ({rem_marks});",
                    task_ids,
                )
            else:
                cur.execute(
                    "UPDATE reminders SET is_deleted = 1 "
                    f"WHERE task_id IN ({rem_marks});",  # noqa: S608
                    task_ids,
                )

    unseeded_counts["tasks"] = _execute_unseed(
        "tasks", "title", DEMO_TASK_TITLES
    )
    unseeded_counts["code_items"] = _execute_unseed(
        "code_items", "title", DEMO_CODE_TITLES
    )
    unseeded_counts["courses"] = _execute_unseed(
        "courses", "title", DEMO_COURSE_TITLES
    )
    unseeded_counts["ideas_doubts"] = _execute_unseed(
        "ideas_doubts", "title", DEMO_IDEA_TITLES
    )
    unseeded_counts["opportunities"] = _execute_unseed(
        "opportunities", "title", DEMO_OPP_TITLES
    )
    unseeded_counts["quick_links"] = _execute_unseed(
        "quick_links", "name", DEMO_LINK_NAMES
    )

    # Clean up empty demo categories if no remaining tasks reference them
    with transaction(conn) as cur:
        for cat_name in DEMO_CATEGORY_NAMES:
            cur.execute(
                "SELECT id FROM categories WHERE name = ? AND is_deleted = 0;",
                (cat_name,),
            )
            cat_row = cur.fetchone()
            if cat_row:
                cid = cat_row[0]
                cur.execute(
                    "SELECT COUNT(*) FROM tasks WHERE category_id = ? "
                    "AND is_deleted = 0;",
                    (cid,),
                )
                if cur.fetchone()[0] == 0:
                    if hard_delete:
                        cur.execute(
                            "DELETE FROM categories WHERE id = ?;", (cid,)
                        )
                    else:
                        cur.execute(
                            "UPDATE categories SET is_deleted = 1 "
                            "WHERE id = ?;",
                            (cid,),
                        )

    return unseeded_counts


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for seed_data script."""
    parser = argparse.ArgumentParser(
        description=(
            "Seed or unseed demo dataset in PLUS-ULTRA SQLite database."
        )
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--seed",
        action="store_true",
        default=True,
        help="Seed demo records if tables are empty (default).",
    )
    group.add_argument(
        "--unseed",
        action="store_true",
        help="Remove all demo seeded records from the database.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force re-seeding even if tables are not empty.",
    )
    parser.add_argument(
        "--soft",
        action="store_true",
        help="During unseeding, soft-delete records instead of hard delete.",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    """CLI script entrypoint."""
    args = parse_args(argv)
    conn = get_connection()
    try:
        if args.unseed:
            print("Unseeding demo workspace data...")
            counts = unseed_demo_workspace_data(conn, hard_delete=not args.soft)
            print("Unseeding complete:")
            for tbl, cnt in counts.items():
                print(f"  - {tbl}: {cnt} demo records removed")
        else:
            print("Seeding demo workspace data...")
            counts = seed_demo_workspace_data(conn, force=args.force)
            if not counts:
                print("Tables already contained data (use --force to reseed).")
            else:
                print("Seeding complete:")
                for tbl, cnt in counts.items():
                    print(f"  - {tbl}: {cnt} demo records added")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
