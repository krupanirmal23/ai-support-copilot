# Rate limits

Rate limits protect your services from abuse

Supabase Auth enforces rate limits on authentication endpoints to prevent abuse. Some rate limits are customizable, and you can configure them in your project [**Authentication** > **Rate Limits**](https://supabase.com/dashboard/project/_/auth/rate-limits).

You can also manage rate limits using the Management API:

```bash
# Get your access token from https://supabase.com/dashboard/account/tokens
export SUPABASE_ACCESS_TOKEN="your-access-token"
export PROJECT_REF="your-project-ref"

# Get current rate limits
curl -X GET "https://api.supabase.com/v1/projects/$PROJECT_REF/config/auth" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  | jq 'to_entries | map(select(.key | startswith("rate_limit_"))) | from_entries'

# Update rate limits
curl -X PATCH "https://api.supabase.com/v1/projects/$PROJECT_REF/config/auth" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rate_limit_anonymous_users": 10,
    "rate_limit_email_sent": 10,
    "rate_limit_sms_sent": 10,
    "rate_limit_verify": 10,
    "rate_limit_token_refresh": 10,
    "rate_limit_otp": 10,
    "rate_limit_web3": 10
  }'
```

## Rate limit behavior

Supabase Auth uses a token bucket algorithm for endpoint operations that are limited by IP address.

Most buckets have a maximum capacity of 30 requests. When a bucket is full, brief bursts of up to 30 requests can be allowed in a short period. [Anonymous sign-ins](https://supabase.com/docs/guides/auth/auth-anonymous) are an exception: the bucket capacity matches the configured number of anonymous sign-ins per hour. Once a bucket empties, requests are rate limited until tokens refill. The rate limit defines the rate at which the bucket is refilled.

This means a client that has been idle will tolerate a brief spike in traffic, but sustained requests above the rate limit are denied. When rate limits are exceeded, a **429 Too Many Requests** error is returned.

The table below shows the rate limit quotas and additional details for authentication endpoints.

| Operation                          | Path                                                                                                       | Limited By | Customizable                   | Limit                                                                                                                                                                                                                                                                                                                |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Emails sent by Supabase Auth       | All email-sending Auth endpoints                                                                           | Project    | Custom SMTP or Send Email hook | 2 emails per hour with the built-in email provider. You can configure this limit when you use custom SMTP or the Send Email hook.                                                                                                  |
| SMS messages sent by Supabase Auth | All SMS-sending Auth endpoints                                                                             | Project    | Yes                            | Defaults to 30 SMS messages per hour.                                                                                                                                                                                                     |
| Sign-ups and sign-ins              | `/auth/v1/signup` `/auth/v1/recover` `/auth/v1/resend` `/auth/v1/magiclink` `/auth/v1/otp` `/auth/v1/user` | IP Address | Yes                            | Defaults to 30 requests per 5 minutes, with bursts up to 30 requests. This limit excludes anonymous sign-ins.                   |
| Send OTPs or magic links           | `/auth/v1/otp`                                                                                             | User       | Yes                            | Defaults to a 60 seconds window before a new request is allowed for the same user.                                                                                                                                                                           |
| Signup confirmation request        | `/auth/v1/signup`                                                                                          | User       | Yes                            | Defaults to a 60 seconds window before a new request is allowed for the same user.                                                                                                                                                           |
| Password reset request             | `/auth/v1/recover`                                                                                         | User       | Yes                            | Defaults to a 60 seconds window before a new request is allowed for the same user.                                                                                                                                                                |
| Verification requests              | `/auth/v1/verify`                                                                                          | IP Address | Yes                            | Defaults to 30 requests per 5 minutes, with bursts up to 30 requests.                                                                   |
| Token endpoint requests            | `/auth/v1/token`                                                                                           | IP Address | Yes                            | Defaults to 150 requests per 5 minutes, with bursts up to 30 requests. This covers password, refresh token, ID token, and PKCE grants. |
| Create or verify an MFA challenge  | `/auth/v1/factors/:id/challenge` `/auth/v1/factors/:id/verify`                                             | IP Address | No                             | 15 requests per minute, with bursts up to 30 requests.                                                                                                          |
| Anonymous sign-ins                 | `/auth/v1/signup`                                                                                          | IP Address | Yes                            | Defaults to 30 requests per hour, with a burst capacity equal to the configured limit. This limit only applies if the endpoint is called without an email or phone number in the request body.                               |
| Web3 sign-ups and sign-ins         | `/auth/v1/token`                                                                                           | IP Address | Yes                            | Defaults to 30 requests per 5 minutes, with bursts up to 30 requests.                                                                                   |

[Test auth flows](https://supabase.com/docs/guides/auth/testing-auth-flows) shows how to test email and phone sign-in without hitting the email and SMS sending limits. The other limits on this page apply to tests too.

## IP address forwarding

By default, Supabase Auth uses the IP address of the client for rate limiting. In certain cases, such as when using server-side frameworks or proxies in front of a project, it may be necessary to forward the end-user IP address to avoid being rate limited based on the address of the server-side client. To use a forwarded IP address for rate limiting in Supabase Auth, set the `Sb-Forwarded-For` header to the end-user IP address and make a request with a [secret API key](https://supabase.com/docs/guides/getting-started/api-keys). Publishable API keys and legacy `anon`/`service_role` API keys are not supported.

IP address forwarding must be explicitly enabled for new projects. You can enable this feature in your project under the **IP Address Forwarding** section of your project's rate limit settings at [**Authentication** > **Rate Limits**](https://supabase.com/dashboard/project/_/auth/rate-limits).

You can also enable IP address forwarding using the management API:

```bash
# Get your access token from https://supabase.com/dashboard/account/tokens
export SUPABASE_ACCESS_TOKEN="your-access-token"
export PROJECT_REF="your-project-ref"

# Update IP address forwarding settings
curl -X PATCH "https://api.supabase.com/v1/projects/$PROJECT_REF/config/auth" \
     -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
      "security_sb_forwarded_for_enabled": true
        }' \
    | jq '.security_sb_forwarded_for_enabled'
```

Once IP address forwarding is enabled, set the `Sb-Forwarded-For` header using the Supabase SDK:

```typescript
import { createServerClient } from '@supabase/ssr'

const supabase = createServerClient(
  'https://<your-project-id>.supabase.co',
  '<your-secret-key>', // Key should start with sb_secret
  {
    global: {
      headers: {
        'sb-forwarded-for': request.headers.get('x-forwarded-for'),
      },
    },
  }
)
```
