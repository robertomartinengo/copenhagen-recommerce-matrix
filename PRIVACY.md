# Privacy Notice — Copenhagen Re-Commerce Matrix

Version: **2026-11-10**

## Data controller

The project owner is the data controller for information submitted through the Telegram bot and the lead-deletion API. Questions about this notice or personal-data rights can be submitted through the repository's GitHub issue tracker without publishing personal data in a public issue.

## Data collected and purpose

When a user requests the Executive PDF report, the project stores:

- name or company name;
- professional email address;
- Telegram user ID and username;
- selected business model;
- district of interest;
- consent version, consent timestamp, and the URL of this notice.

The data is used to prepare and deliver the requested report and to respond to the user's request. No personal data is included in prompts sent to Gemini, Groq, OpenRouter, or other AI providers. The AI receives aggregated zone metrics only.

## Legal basis and consent

Lead data is stored only after the user explicitly accepts this notice and the processing described above. Consent is recorded with the notice version and timestamp.

Consent to receive the report is separate from any future consent to marketing or additional contact. The current flow does not request marketing consent and does not add users to a mailing list.

## Retention

Lead data is retained for no longer than **12 months**. After that period, identifying fields (Telegram ID, username, name, and email) are anonymized; aggregate business-type and district metadata may be retained for statistics. Leads can also be deleted sooner at the user's request.

## User rights

A user can request access, correction, or deletion through the Telegram command `/delete_my_data` or through the protected `DELETE /leads/{telegram_user_id}` API endpoint. The bot deletes all matching lead rows and records a deletion audit event without including personal data in the audit log.

## Data minimization

The project does not intentionally collect phone numbers, postal addresses, identity-document data, payment data, or special-category data. Do not include such information in the report form.

## Changes

Material changes to this notice require a new version. The stored `consent_version` identifies the notice accepted by each user.
