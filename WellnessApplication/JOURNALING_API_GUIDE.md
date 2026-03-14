# Journaling API Guide

This document describes the backend journaling feature implemented for the wellness application.

## Why a separate Django app?

A dedicated `journal` app keeps concerns isolated:
- Better modularity and maintainability.
- Clear migration history for journaling data.
- Easy to evolve journaling independently from auth/workout logic.

## Implemented Data Models

### 1. JournalEntry
Stores each journal record for a user.
- `user` (FK to user)
- `title`, `content`
- `mood` (1 to 5)
- `entry_date`
- `is_favorite`, `is_archived`
- `word_count`
- `read_count`, `last_read_at`
- `created_at`, `updated_at`
- many-to-many `tags`

### 2. JournalTag
Reusable tags (e.g. `stress`, `gratitude`, `sleep`) attached to entries.

### 3. JournalReadEvent
Tracks each reread event explicitly.
- `entry`, `user`
- `source` (`manual`, `recommendation`, `reflection`)
- `read_at`

### 4. JournalPrompt
Stores guided writing prompts.
- `category` (`reflection`, `gratitude`, `stress`, `goals`, `self_compassion`)
- `prompt_text`
- `is_active`

## API Endpoints

Base path: `/api/journal/`

### Entries
- `GET /api/journal/entries/`
- `POST /api/journal/entries/`
- `GET /api/journal/entries/{id}/`
- `PATCH /api/journal/entries/{id}/`
- `DELETE /api/journal/entries/{id}/`
- `POST /api/journal/entries/{id}/reread/`
- `POST /api/journal/entries/{id}/toggle-favorite/`

### Insights
- `GET /api/journal/insights/`

Returns:
- total entries
- entries in last 7/30 days
- current streak and longest streak
- average word count
- reread totals and reread ratio
- mood distribution and most common mood
- top tags
- timestamp of latest entry

### Prompts
- `GET /api/journal/prompts/random/`
- Optional query: `?category=gratitude`

## Query Filters (List Entries)

`GET /api/journal/entries/` supports:
- `q` (search title/content)
- `mood` (1-5)
- `is_favorite` (true/false)
- `is_archived` (true/false)
- `tag` (tag name)
- `start_date` / `end_date` (YYYY-MM-DD)

## Auth

All journal endpoints require authenticated requests (JWT in this project).

## Migrations Added

- `journal/migrations/0001_initial.py`
- `journal/migrations/0002_seed_journal_prompts.py`

## Next Commands

```bash
python manage.py migrate
python manage.py test journal
```

Swagger docs should automatically include the new `Journal` endpoints via drf-spectacular.
