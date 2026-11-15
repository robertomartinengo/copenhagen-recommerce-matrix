-- 2.02 Separate consent for being contacted (marketing)
-- Adds contact_consent (boolean) and contact_consent_at (timestamptz) to leads,
-- distinct from consent_version/consent_at which cover report delivery.
-- Additive and repeatable: safe to re-run.

alter table public.leads
    add column if not exists contact_consent boolean not null default false,
    add column if not exists contact_consent_at timestamptz;
