"""Conversations / jobs / answers <-> Postgres.

Wired up in Step 6. Tables (rough): conversations(id, job_id, summary, model,
messages jsonb, timestamps), jobs(wellfound_id, title, company, description, url),
applications(job_id, questions, answers, status, dates).
"""
