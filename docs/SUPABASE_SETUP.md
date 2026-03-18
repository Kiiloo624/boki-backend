# Supabase Setup Guide

## 1. Create a Project

1. Go to https://supabase.com and sign in
2. Click **New Project**
3. Set a strong database password — save it somewhere safe
4. Choose region: **Europe West** (closest to Nigeria with good latency)
5. Wait ~2 minutes for provisioning

## 2. Get Your API Keys

Go to **Settings → API** in your project dashboard:

| Key | Where to use | Notes |
|---|---|---|
| `Project URL` | `.env` as `SUPABASE_URL` | Public |
| `anon / public` | `.env` as `SUPABASE_ANON_KEY` | Safe for Flutter/web clients |
| `service_role` | `.env` as `SUPABASE_SERVICE_ROLE_KEY` | **Never expose — full DB access** |

## 3. Database Schema

Run these SQL migrations in **SQL Editor** in the Supabase dashboard.

### Venues Table
```sql
create table venues (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  slug text unique not null,
  description text,
  category text,                        -- e.g. 'bar', 'lounge', 'club', 'restaurant'
  city text not null default 'Abuja',
  district text,                        -- e.g. 'Wuse 2', 'Maitama', 'Garki'
  address text,
  landmark_directions text,             -- e.g. 'Opposite First Bank, Wuse 2'
  latitude double precision,
  longitude double precision,
  phone text,
  instagram_handle text,
  opening_hours jsonb,                  -- { mon: "5pm-2am", tue: null, ... }
  entry_fee_info text,
  menu_price_range text,                -- e.g. '₦3,000 – ₦15,000'
  minimum_spend text,
  dress_code text,
  camera_policy text,
  verified boolean default false,
  active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Full-text search index
create index venues_fts on venues using gin(to_tsvector('english', name || ' ' || coalesce(district, '') || ' ' || coalesce(description, '')));
```

### Venue Media Table
```sql
create table venue_media (
  id uuid default gen_random_uuid() primary key,
  venue_id uuid references venues(id) on delete cascade,
  url text not null,
  type text not null check (type in ('photo', 'video')),
  is_cover boolean default false,
  created_at timestamptz default now()
);
```

### Reviews Table (Phase 2)
```sql
create table reviews (
  id uuid default gen_random_uuid() primary key,
  venue_id uuid references venues(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  rating int check (rating between 1 and 5),
  body text,
  is_verified boolean default false,   -- curated reviews shown in Phase 1
  created_at timestamptz default now()
);
```

### Agent Action Log (for rate limiting)
```sql
create table agent_action_log (
  id uuid default gen_random_uuid() primary key,
  user_id uuid,                         -- null for anonymous users (use device_id)
  device_id text,
  action_type text not null,            -- e.g. 'search', 'save_venue', 'get_directions'
  performed_at timestamptz default now()
);

-- Index for fast rate-limit queries
create index agent_log_user_day on agent_action_log (user_id, performed_at);
create index agent_log_device_day on agent_action_log (device_id, performed_at);
```

## 4. Row Level Security (RLS)

Enable RLS on all tables. Start with these policies:

```sql
-- Venues: anyone can read, only service role can write
alter table venues enable row level security;
create policy "Public read" on venues for select using (true);

-- Reviews: anyone can read verified reviews
alter table reviews enable row level security;
create policy "Public read verified" on reviews for select using (is_verified = true);

-- Agent log: service role only (backend writes this directly)
alter table agent_action_log enable row level security;
```

## 5. Storage Buckets

Go to **Storage → New Bucket**:

| Bucket name | Public? | Purpose |
|---|---|---|
| `venue-media` | Yes | Venue photos and videos |
| `venue-media-raw` | No | Scraped/unverified media before review |

## 6. Auth Configuration (Phase 2 — do this when ready)

Go to **Authentication → Settings**:
- Enable **Email** provider (basic)
- Enable **Google** OAuth (for social login)
- Set **Site URL** to your production domain
- Add `http://localhost:3000` to redirect URLs for dev

## 7. Flutter SDK Setup

In your Flutter `pubspec.yaml`:
```yaml
dependencies:
  supabase_flutter: ^2.0.0
```

Initialize in `main.dart`:
```dart
await Supabase.initialize(
  url: 'YOUR_SUPABASE_URL',
  anonKey: 'YOUR_ANON_KEY',
);
```

Use `SUPABASE_ANON_KEY` here — never the service role key in mobile apps.
