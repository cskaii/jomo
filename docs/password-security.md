# New-password security (reviewed 7 November 2026)

JOMO follows the password-length and usability guidance in
[NIST SP 800-63B-4, section 3.1.1](https://pages.nist.gov/800-63-4/sp800-63b.html).
That standard was published in July 2025 and remains the current revision checked
for this implementation; this is not a claim of NIST certification.

## Implemented

- New accounts and password changes require at least **15 Unicode code points**.
- A local zxcvbn strength estimate must score at least **3 out of 4**. The meter
  calls these levels **Strong** and **Very strong**. This threshold is JOMO's
  additional guessability policy, not a threshold prescribed by NIST.
- Common passwords, substitutions, repeats, keyboard patterns, the JOMO name,
  and email-derived choices are penalized by the estimator. Published example
  passphrases are also explicitly blocked as whole-password values.
- Spaces, Unicode, pasted passwords, and password managers are supported. There
  is no forced uppercase/lowercase/number/symbol combination, routine expiry,
  security question, or password hint.
- The UI shows text as well as a colored native meter, with screen-reader status
  announcements and a Show/Hide control. Estimates are debounced and calculated
  in a browser worker, so scoring does not block typing. Estimator dictionaries are loaded separately from the initial
  sign-in page; typing does not send the candidate password to a strength API.
- The backend independently checks new passwords before forwarding them to
  Supabase, including password reset requests. Disabling the browser controls
  cannot bypass these checks. Existing-password sign-in is not subject to the
  new-password policy.
- Actual passwords are not trimmed, truncated, normalized, logged, stored in
  browser storage, or returned in responses by this feature. They are sent to the
  backend/Supabase only when the user submits the account/password operation.
  Supabase manages password hashing and authentication.
- New passwords are limited to **72 UTF-8 bytes** to respect Supabase's current
  bcrypt limit. At least 64 ASCII characters are supported; Unicode characters
  can use several bytes each. Oversized values are rejected, never truncated.
  This provider limit prevents claiming support for every 64-character Unicode
  password. Supporting longer Unicode secrets needs a compatible verifier.

The shared public constants live in `backend/app/data/password_policy.json`.
Frontend and backend use different language ports of zxcvbn and can occasionally
estimate a candidate differently. The backend remains authoritative; the bar
is guidance, not proof of security or a complete breach-database check. Shared
test vectors cover the main policy and Unicode/byte boundaries in both ports.

## Supabase configuration

In **Authentication > Sign In / Providers > Email** (the Auth password settings):

1. Set **Minimum password length** to **15**. This also protects requests made
   directly to Supabase, outside JOMO's backend.
2. Leave the **required character types** option at **no character requirements**,
   following the NIST composition-rule guidance. The app applies a guessability
   check instead of requiring a particular character mix.
3. Enable **leaked password protection** if available on your plan. Supabase's
   current documentation limits this feature to **Pro and above**. It rejects
   passwords found in Have I Been Pwned, beyond JOMO's offline common-password
   and pattern checks. Free-plan operation does not provide this full check.

No SQL migration or new environment variable is needed for password strength.
Commit/deploy the frontend package/lockfile and backend requirements changes.
Render installs the Python estimator during its normal Docker build.

The public Supabase Auth API is independently reachable. Setting its minimum
length protects all signups, but JOMO's exact zxcvbn threshold is enforced only
through JOMO's endpoints. If every possible direct Auth signup must use that
same threshold, add an Auth Before User Created hook or restrict the signup
architecture. Do not represent frontend validation as a project-wide Auth rule.

## Sources and limits

- [NIST password guidance](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [Supabase password security and leaked-password protection](https://supabase.com/docs/guides/auth/password-security)
- [Supabase Auth maximum password length implementation](https://github.com/supabase/auth/blob/master/internal/api/password.go)
- [zxcvbn-ts usage and score meanings](https://zxcvbn-ts.github.io/zxcvbn/guide/getting-started/)

A strong meter score cannot protect against phishing, malware, or password reuse.
This change does not add MFA/passkeys or certify the complete authentication
system against every NIST requirement.
