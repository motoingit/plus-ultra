# MongoDB Persistence Adapter: Architectural Note

This document outlines the architectural strategy for integrating MongoDB as a future persistence backend in PLUS-ULTRA without altering application domain models, business services, or GUI components.

---

## 1. Architectural Boundary: No SQLAlchemy Coupling

SQLAlchemy is designed for relational DBMS backends (SQLite, PostgreSQL, MySQL) and does not provide native document store abstractions.

**MongoDB must never be forced through SQLAlchemy.** Instead, MongoDB persistence is achieved by implementing the existing abstract repository contracts defined in:
`plus_ultra.domain.repositories`

```text
               Application Services & GUI
                          |
                          v
         [ Domain Repository Contracts (Protocols) ]
                          |
             +------------+------------+
             |                         |
    [ SQLAlchemy Adapter ]      [ MongoDB Adapter ]
             |                         |
       SQLite / Postgres          MongoDB Driver
        (Relational DB)          (Document Store)
```

---

## 2. Implementing MongoDB Repositories

To support MongoDB, implement each protocol using the official `pymongo` or `motor` driver:

1. **`MongoTaskRepository(TaskRepositoryContract)`**
   - Collection: `db["tasks"]`
   - Store documents as JSON-compatible BSON:
     ```json
     {
       "_id": "uuid-string",
       "title": "Clean codebase",
       "category_id": "category-uuid",
       "status": "Pending",
       "created_at": "2026-11-15T12:00:00+00:00",
       "is_deleted": 0
     }
     ```
   - Map between MongoDB BSON documents and the plain dataclass `Task` entity in `plus_ultra.domain.entities`.

2. **`MongoCategoryRepository(CategoryRepositoryContract)`**
   - Collection: `db["categories"]`
   - Enforce uniqueness on `{name: 1}` with a partial index filter `{is_deleted: 0}`.

3. **`MongoReminderRepository(ReminderRepositoryContract)`**
   - Collection: `db["reminders"]`
   - Store embedded or referenced device fires.

4. **`MongoAppStateRepository(AppStateRepositoryContract)`**
   - Collection: `db["app_state"]`
   - Key-value documents `{ "_id": key, "value": val }`.

---

## 3. Unit of Work in MongoDB

In MongoDB 4.0+, multi-document transactions are supported when connected to a replica set:

```python
class MongoUnitOfWork(UnitOfWork):
    def __init__(self, client: pymongo.MongoClient) -> None:
        self.client = client
        self.session = None

    def __enter__(self):
        self.session = self.client.start_session()
        self.session.start_transaction()
        self.tasks = MongoTaskRepository(self.session)
        ...
        return self

    def commit(self):
        self.session.commit_transaction()

    def rollback(self):
        self.session.abort_transaction()
```

For standalone MongoDB instances where replica set transactions are unavailable, individual repository operations execute atomically per document.

---

## 4. Activation via Configuration

Switching backends requires only updating the configuration environment variable:

```env
PERSISTENCE_BACKEND=mongodb
DATABASE_URL=mongodb://localhost:27017/plus_ultra
```

`DatabaseFactory` inspects `PERSISTENCE_BACKEND`:
- When `sqlalchemy`: initializes `SqlAlchemyUnitOfWork`.
- When `mongodb`: initializes `MongoUnitOfWork` (once installed).

Application services, scheduler workers, and UI view controllers require zero modifications.

