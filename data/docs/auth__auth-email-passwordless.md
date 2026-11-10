# Passwordless email sign-in

Email sign-in using Magic Links or One-Time Passwords (OTPs)

Supabase Auth provides several passwordless sign-in methods. Passwordless sign-in allows users to sign in without a password, by clicking a confirmation link or entering a verification code.

Passwordless sign-in can:

- Improve the user experience by not requiring users to create and remember a password
- Increase security by reducing the risk of password-related security breaches
- Reduce support burden of dealing with password resets and other password-related flows

Supabase Auth offers two passwordless sign-in methods that use the user's email address:

- [Magic Link](#with-magic-link)
- [OTP](#with-otp)

## With Magic Link

Magic Links are a form of passwordless sign-in where users click on a link sent to their email address to sign in to their accounts. Magic Links only work with email addresses and are one-time use only.

### Enabling Magic Link

Email authentication methods, including Magic Links, are enabled by default.

Configure the Site URL and any additional [redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls). These are the only URLs that are allowed as redirect destinations after the user clicks a Magic Link. You can change the URLs on the [URL Configuration page](https://supabase.com/dashboard/project/_/auth/url-configuration) for hosted projects, in the `config.toml` [file](https://supabase.com/docs/guides/local-development/cli/config#auth.additional_redirect_urls) for local development, or in the `.env` configuration file for [self-hosted Supabase](https://supabase.com/docs/guides/self-hosting/docker).

By default, a user can only request a magic link once every 60 seconds and they expire after 1 hour.

To test magic links without hitting email limits, see [Test auth flows](https://supabase.com/docs/guides/auth/testing-auth-flows).

### Signing in with Magic Link

Call the "sign in with OTP" method from the client library.

Though the method is labelled "OTP", it sends a Magic Link by default. The two methods differ only in the content of the confirmation email sent to the user.

If the user hasn't signed up yet, they are automatically signed up by default. To prevent this, set the `shouldCreateUser` option to `false`.

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
async function signInWithEmail() {
  const { data, error } = await supabase.auth.signInWithOtp({
    email: 'valid.email@supabase.io',
    options: {
      // set this to false if you do not want the user to be automatically signed up
      shouldCreateUser: false,
      emailRedirectTo: 'https://example.com/welcome',
    },
  })
}
```

**Expo React Native:**

Read the [Deep Linking Documentation](https://supabase.com/docs/guides/auth/native-mobile-deep-linking) to learn how to handle deep linking.

**Dart:**

**Swift:**

**Kotlin:**

**Python:**

**C#:**

That's it for the implicit flow.

If you're using PKCE flow, edit the Magic Link [email template](https://supabase.com/docs/guides/auth/auth-email-templates) to send a token hash:

```html
<h2>Sign in to your account</h2>

<p>Use this link to sign in to your account:</p>
<p><a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email">Sign in</a></p>
```

At the `/auth/confirm` endpoint, exchange the hash for the session:

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { error } = await supabase.auth.verifyOtp({
  token_hash: 'hash',
  type: 'email',
})
```

## With OTP

Email one-time passwords (OTP) are a form of passwordless sign-in where users key in a six-digit code sent to their email address to sign in to their accounts.

### Enabling email OTP

Email authentication methods, including Email OTPs, are enabled by default.

Email OTPs share an implementation with Magic Links. To send an OTP instead of a Magic Link, alter the **Magic Link** [email template](https://supabase.com/dashboard/project/_/auth/templates/magic-link-or-otp). Refer to the [Email Templates guide](https://supabase.com/docs/guides/auth/auth-email-templates) for more information.

Modify the template to include the `{{ .Token }}` variable, for example:

```html
<h2>One time login code</h2>

<p>Please enter this code: {{ .Token }}</p>
```

By default, a user can only request an OTP once every 60 seconds, and they expire after 1 hour. This is configurable via **Authentication > Sign In / Providers > Auth Providers > Email > Email OTP expiration**. An expiry duration of more than 86,400 seconds (one day) is strongly discouraged and can only be set via the [Management API](https://supabase.com/docs/reference/api/v1-update-auth-service-config). Make sure to read the [security recommendations](https://supabase.com/docs/guides/security/production-checklist#auth) before going into production.

> **Caution:** 

The **Email OTP Expiration** setting also governs the validity of Magic Links and other email links, including confirmation, password recovery, email change, and [invitation](https://supabase.com/docs/guides/auth/users#inviting-users) links.

If users see an expired-token error, see [OTP verification failures](/kb/troubleshooting/otp-verification-failures-token-has-expired-or-otp_expired-errors-5ee4d0).

### Signing in with email OTP

#### Step 1: Send the user an OTP code

Get the user's email and call the "sign in with OTP" method from your client library.

If the user hasn't signed up yet, they are automatically signed up by default. To prevent this, set the `shouldCreateUser` option to `false`.

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'valid.email@supabase.io',
  options: {
    // set this to false if you do not want the user to be automatically signed up
    shouldCreateUser: false,
  },
})
```

**Dart:**

**Swift:**

**Kotlin:**

**Python:**

**C#:**

If the request is successful, you receive a response with `error: null` and a `data` object where both `user` and `session` are null. Let the user know to check their email inbox.

```json
{
  "data": {
    "user": null,
    "session": null
  },
  "error": null
}
```

#### Step 2: Verify the OTP to create a session

Provide an input field for the user to enter their one-time code.

Call the "verify OTP" method from your client library with the user's email address, the code, and a type of `email`:

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const {
  data: { session },
  error,
} = await supabase.auth.verifyOtp({
  email: 'email@example.com',
  token: '123456',
  type: 'email',
})
```

**Swift:**

**Kotlin:**

**Python:**

**C#:**

If successful, the user is now signed in, and you receive a valid session that looks like:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNjI3MjkxNTc3LCJzdWIiOiJmYTA2NTQ1Zi1kYmI1LTQxY2EtYjk1NC1kOGUyOTg4YzcxOTEiLCJlbWFpbCI6IiIsInBob25lIjoiNjU4NzUyMjAyOSIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6InBob25lIn0sInVzZXJfbWV0YWRhdGEiOnt9LCJyb2xlIjoiYXV0aGVudGljYXRlZCJ9.1BqRi0NbS_yr1f6hnr4q3s1ylMR3c1vkiJ4e_N55dhM",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "LSp8LglPPvf0DxGMSj-vaQ",
  "user": {...}
}
```
