# DB Migration & Scaling Plan for Cthulu

Purpose: Document a practical, low-risk path from the current SQLite/WAL persistence to a horizontally scalable solution for trade history and a dedicated vector DB for ML embeddings.

---

## Goals
- Preserve transactional guarantees for trade data (ACID) and ensure no data loss.
- Provide a scalable time-series and analytical store for high-throughput operations.
- Introduce a separate vector DB for ML/RL artifacts and nearest-neighbor queries.

---

## Phased Approach

### Phase 0 — Stabilize SQLite (short-term)
- Tune WAL settings, checkpoint cadence, and ensure WAL file placement on fast disks.
- Add monitoring: `db_write_errors_total`, `db_tx_latency_seconds`.
- Ensure regular backups (daily) and an archive retention policy.

### Phase 1 — PostgreSQL (medium-term)
- Move transactional trade data (orders/trades/positions) to Postgres (or Timescale if heavy time-series needs).
- Migration steps:
  1. Add a Postgres replica as read replica next to SQLite (ETL sync via logical replication or CDC tool like `pg_chameleon` or `Debezium`).
  2. Run dual-writes (app layer toggled) and compare stats for a trial period.
  3. Switch reads gradually, then cut over writes after validation.
- Benefits: stronger concurrency, indexing, and horizontal scaling via replicas.

### Phase 2 — Vector DB for ML (long-term)
- Purpose: store embeddings, vector indexes, and metadata to support similarity searches and fast nearest-neighbor queries used by ML components.
- Candidate systems: Milvus (open-source) or Weaviate (vector DB with schema), or managed Pinecone (hosted).
- Use cases: model memory, retrieval-augmented features, fast similarity for regime detection.

### Phase 3 — Operationalization
- Backup/restore for Postgres and vector DB.
- Add migrations for schema changes, rollback steps, and capacity planning.
- Document runbook and failover procedures.

---

## Data Modelling Notes
- Keep trade and order data (time-series + transaction) in Postgres.
- Keep ML embeddings and vector indexes in vector DB with links back to canonical IDs in Postgres.
- Consider time-partitioning large tables and retention policies for historic data.

---

## Migration Safety & Rollback
- Use dry-run ETL with checksums; verify row counts and critical aggregates before cutover.
- Keep dual-write mode until safe; have read-only rollback option.
- Run in a staging environment first with realistic volumes.

---

## Recommendations
- Start Phase 1 planning within 2 weeks with a PoC Postgres and a small vector DB PoC (Milvus).
- Add performance benchmarks and a cost estimate for managed vs self-hosted vector DB.
- Add `docs/DB_MIGRATION_CHECKLIST.md` with exact migration commands and validation queries.

---

*This document is a plan — we should iterate based on operational constraints and tradeoffs.*