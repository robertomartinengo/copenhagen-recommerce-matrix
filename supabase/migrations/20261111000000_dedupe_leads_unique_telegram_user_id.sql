-- Deduplicate existing leads and enforce one lead per Telegram user.
-- 1) Keep only the most recent row per telegram_user_id (null ids are ignored).
-- 2) Add a UNIQUE constraint on telegram_user_id.
-- 3) Convert insert_lead_with_consent into an upsert so repeated submissions
--    from the same user update the existing row instead of creating duplicates.

-- Step 1: deduplicate existing rows (keep latest by created_at, tie-break by id)
delete from public.leads l1
where l1.telegram_user_id is not null
  and exists (
    select 1
    from public.leads l2
    where l2.telegram_user_id = l1.telegram_user_id
      and (
        l2.created_at > l1.created_at
        or (l2.created_at = l1.created_at and l2.id > l1.id)
      )
  );

-- Step 2: add unique constraint (add if not exists pattern via DO block)
do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'leads_telegram_user_id_key'
          and conrelid = 'public.leads'::regclass
    ) then
        alter table public.leads
            add constraint leads_telegram_user_id_key unique (telegram_user_id);
    end if;
end $$;

-- Step 3: replace insert function with an upsert (on conflict telegram_user_id)
create or replace function public.insert_lead_with_consent(
    p_telegram_user_id bigint,
    p_telegram_username text,
    p_full_name text,
    p_email text,
    p_business_type text,
    p_interested_district text,
    p_consent_version text,
    p_consent_at timestamptz,
    p_privacy_notice_url text,
    p_actor text default 'telegram_bot'
)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
    v_lead_id bigint;
begin
    if p_consent_version is null or p_consent_at is null or p_privacy_notice_url is null then
        raise exception 'Explicit consent is required before storing lead data';
    end if;

    insert into public.leads (
        telegram_user_id,
        telegram_username,
        full_name,
        email,
        business_type,
        interested_district,
        consent_version,
        consent_at,
        privacy_notice_url
    )
    values (
        p_telegram_user_id,
        p_telegram_username,
        p_full_name,
        p_email,
        p_business_type,
        p_interested_district,
        p_consent_version,
        p_consent_at,
        p_privacy_notice_url
    )
    on conflict (telegram_user_id) do update set
        telegram_username = excluded.telegram_username,
        full_name = excluded.full_name,
        email = excluded.email,
        business_type = excluded.business_type,
        interested_district = excluded.interested_district,
        consent_version = excluded.consent_version,
        consent_at = excluded.consent_at,
        privacy_notice_url = excluded.privacy_notice_url,
        created_at = now()
    returning id into v_lead_id;

    insert into public.leads_audit (action, actor, affected_rows)
    values ('upsert', p_actor, 1);

    return v_lead_id;
end;
$$;

-- Re-grant execute to service_role (revoke/re-grant cycle to be explicit)
revoke all on function public.insert_lead_with_consent(bigint, text, text, text, text, text, text, timestamptz, text, text) from public, anon, authenticated;
grant execute on function public.insert_lead_with_consent(bigint, text, text, text, text, text, text, timestamptz, text, text) to service_role;
