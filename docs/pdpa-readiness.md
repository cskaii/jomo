# Singapore PDPA readiness

This is an engineering/operating checklist, not legal certification. Consent boxes
and a notice alone do not establish PDPA compliance. The operator must verify the
actual deployment before public launch. A school/side project is not automatically
exempt when it processes other people's personal data.

## Implemented controls

| Area | Implementation and limits |
| --- | --- |
| Purposes/notification | Public `/privacy` describes data, purposes/viewers, optional choices, providers and retention; no continuous/cross-app tracking claims. |
| Consent | Separate location setting, browser permission and per-check-in consent; separate photo and Guardian consent; purpose/version/time records. Onboarding acknowledgement does not enable optional collection. |
| Withdrawal | Disable location to remove coordinates; remove individual check-ins/evidence or all proof photos; clear screening history. Alternative activity methods avoid requiring photo/location sharing. |
| Minimisation | One location per member/activity rounded to 3 decimal places, never routes; opaque random photo filenames; re-encoding removes EXIF/GPS, unsafe/oversized images rejected. Approximate location is still personal data. |
| Protection | Backend authorisation, private Storage/restrictive RLS, owner/eligible-peer access, 60-second preview links, server-only admin key, safe logs and body limits. Previously issued links persist briefly until expiry/deletion. |
| Retention | Coordinates 24 hours, photos default 7 days, notification/screening metadata 30 days, minimal photo-access events up to 366 days. Physical removal depends on worker/provider operation and retries. These periods need an operator rationale. |
| Access/correction | Editable profile/preferences/screen time, account export and a contact route for formal requests. Minimal photo storage/preview history assists access handling. Export is not an exhaustive statutory response. |
| Account deletion | Auth/public-user deletion is atomic through PostgreSQL triggers; ownership transfers, shared assets survive, ledger attribution is removed and proof files enter a durable deletion queue. |

Personal activities are self-reported and peer approval is a review decision.
Geolocation can be inaccurate/spoofed; a photo cannot establish activity authenticity.
Photos can still show personal information after metadata removal. Guardian can miss
identifiers and does not certify content as safe.

## Operator actions before public launch

1. **Accountability:** identify the actual operator and responsible DPO/privacy
   contact, publish a monitored contact, assign request/complaint ownership and
   maintain procedures. Filling an email field alone is not the accountability process.
2. **Purpose/retention review:** maintain a data inventory including Auth, tables,
   Storage, logs/backups and exports; approve necessity and retention for accounts,
   activities, consent/security records, inactivity and any legal holds. Stop retaining
   identifiable data when no longer reasonably required. The chosen 366-day access
   metadata period is not a blanket statutory obligation.
3. **Providers/overseas transfers:** verify actual Supabase and Vercel regions,
   contracts/DPA terms, subprocessors, support access, comparable protection and
   backup arrangements. A Singapore hosting region alone does not establish all
   transfers are compliant. Make the public notice match the actual arrangements.
4. **Access/correction/withdrawal:** verify identity proportionately, preserve relevant
   records during formal access handling, assess exceptions/third-party privacy,
   provide personal data and relevant use/disclosure history, and correct/propagate
   corrections where required. Self-service export assists this process; it does not
   replace it. Maintain a request register and escalation path.
5. **Audience:** prefer invited adult testers initially as a product scope decision.
   Before admitting children, assess PDPC children's-data guidance, age-appropriate
   notices/controls and when a parent/guardian must give valid consent. There is no
   universal minimum age established by this checklist. Do not collect NRICs merely
   to age-gate this prototype.
6. **Security operations:** restrict provider/admin access, use administrator MFA,
   rotate exposed credentials, verify HTTPS/private bucket/RLS, patch dependencies,
   test backup restoration and safely reapply deletions after restore. Logs must not
   contain passwords, request payloads or signed photo links.
7. **Retention operations:** monitor cleanup failures/retry backlog and sleeping-host
   behaviour; reconcile exceptional orphan objects and document backup expiry.
   Deleting a live account does not instantly erase every hosted backup/export.
8. **Incidents:** assign detection, containment, investigation and notification
   responsibility. Assess suspected breaches reasonably and expeditiously. PDPC
   guidance aims to complete assessment within 30 calendar days; do not wait
   unnecessarily. For a notifiable breach, notify PDPC as soon as practicable and
   within three calendar days after determining it is notifiable, and notify affected
   individuals where required as soon as practicable. Assess actual harm, scale,
   exceptions and statutory circumstances.

These actions require operational facts/authority that the repository cannot supply.
They have not been represented as completed because tests pass.

## Official references

- [PDPC data protection obligations](https://www.pdpc.gov.sg/overview-of-pdpa/the-legislation/personal-data-protection-act/data-protection-obligations)
- [Personal Data Protection Act 2012](https://sso.agc.gov.sg/Act/PDPA2012)
- [PDPC breach management/notification guide](https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/other-guides/guide-on-managing-and-notifying-data-breaches-under-the-pdpa-15-mar-2021.pdf)
- [PDPC children's data guidelines](https://www.pdpc.gov.sg/guidelines-and-consultation/2024/03/advisory-guidelines-on-the-pdpa-for-childrens-personal-data-in-the-digital-environment)

Review current law/guidance and obtain qualified advice for the actual public
deployment. The implementation is designed to support these duties, not certify them.
