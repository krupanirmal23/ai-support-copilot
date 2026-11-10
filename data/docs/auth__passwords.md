# Password-based Auth

Allow users to sign in with a password connected to their email or phone number.

Users often expect to sign in to your site with a password. Supabase Auth helps you implement password-based auth safely, using secure configuration options and best practices for storing and verifying passwords.

Users can associate a password with their identity using their [email address](#with-email) or a [phone number](#with-phone).

## With email

### Enabling email and password-based authentication

Email authentication is enabled by default.

You can configure whether users need to verify their email to sign in. On hosted Supabase projects, this is true by default. On self-hosted projects or in local development, this is false by default.

Change this setting on the [Auth Providers page](https://supabase.com/dashboard/project/_/auth/providers) for hosted projects, or in the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.email.enable_confirmations) for self-hosted projects.

### Signing up with an email and password

There are two possible flows for email signup: [implicit flow](https://supabase.com/docs/guides/auth/sessions/implicit-flow) and [PKCE flow](https://supabase.com/docs/guides/auth/sessions/pkce-flow). If you're using SSR, you're using the PKCE flow. If you're using client-only code, the default flow depends upon the client library. The implicit flow is the default in JavaScript and Dart, and the PKCE flow is the default in Swift.

The instructions in this section assume that email confirmations are enabled.

**Implicit flow:**

The implicit flow only works for client-only apps. Your site directly receives the access token after the user confirms their email.

**JavaScript:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/javascript/auth-signup) with their email address and password.

You can optionally specify a URL to redirect to after the user clicks the confirmation link. This URL must be configured as a [Redirect URL](https://supabase.com/docs/guides/auth/redirect-urls), which you can do in the [dashboard](https://supabase.com/dashboard/project/_/auth/url-configuration) for hosted projects, or in the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.additional_redirect_urls) for self-hosted projects.

If you don't specify a redirect URL, the user is automatically redirected to your site URL. This defaults to `localhost:3000`, but you can also configure this.

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
async function signUpNewUser() {
  const { data, error } = await supabase.auth.signUp({
    email: 'valid.email@supabase.io',
    password: 'example-password',
    options: {
      emailRedirectTo: 'https://example.com/welcome',
    },
  })
}
```

**Dart:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/dart/auth-signup) with their email address and password:

**Swift:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/swift/auth-signup) with their email address and password.

You can optionally specify a URL to redirect to after the user clicks the confirmation link. This URL must be configured as a [Redirect URL](https://supabase.com/docs/guides/auth/redirect-urls), which you can do in the [dashboard](https://supabase.com/dashboard/project/_/auth/url-configuration) for hosted projects, or in the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.additional_redirect_urls) for self-hosted projects.

If you don't specify a redirect URL, the user is automatically redirected to your site URL. This defaults to `localhost:3000`, but you can also configure this.

**Kotlin:**

To sign up the user, call [signUpWith(Email)](https://supabase.com/docs/reference/kotlin/auth-signup) with their email address and password:

**Python:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/python/auth-signup) with their email address and password.

You can optionally specify a URL to redirect to after the user clicks the confirmation link. This URL must be configured as a [Redirect URL](https://supabase.com/docs/guides/auth/redirect-urls), which you can do in the [dashboard](https://supabase.com/dashboard/project/_/auth/url-configuration) for hosted projects, or in the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.additional_redirect_urls) for self-hosted projects.

If you don't specify a redirect URL, the user is automatically redirected to your site URL. This defaults to `localhost:3000`, but you can also configure this.

**C#:**

To sign up the user, call [`SignUp()`](https://supabase.com/docs/reference/csharp/sign-up) with their email address and password. You can optionally specify a URL to redirect to after the user clicks the confirmation link.

**PKCE flow:**

The PKCE flow allows for server-side authentication. Unlike the implicit flow, which directly provides your app with the access token after the user clicks the confirmation link, the PKCE flow requires an intermediate token exchange step before you can get the access token.

##### Step 1: Update signup confirmation email

Update your signup email template to send the token hash. For detailed instructions on how to configure your email templates, including the use of variables like `{{ .SiteURL }}`, `{{ .TokenHash }}`, and `{{ .RedirectTo }}`, refer to our [Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates) guide.

Your signup email template should contain the following HTML:

##### Step 2: Create token exchange endpoint

Create an API endpoint at `/auth/confirm` to handle the token exchange.

> **Note:** 

Make sure you're using the right `supabase` client in the following code.

If you're not using Server-Side Rendering or cookie-based Auth, you can directly use the `createClient` from `@supabase/supabase-js`. If you're using Server-Side Rendering, see the [Server-Side Auth guide](https://supabase.com/docs/guides/auth/server-side/creating-a-client) for instructions on creating your Supabase client.

**Next.js:**

Create a new file at `app/auth/confirm/route.ts` and populate with the following:

```ts app/auth/confirm/route.ts
import { type EmailOtpType } from '@supabase/supabase-js'
import { redirect } from 'next/navigation'
import { type NextRequest } from 'next/server'

import { createClient } from '@/utils/supabase/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type') as EmailOtpType | null
  const next = searchParams.get('next') ?? '/'

  if (token_hash && type) {
    const supabase = await createClient()

    const { error } = await supabase.auth.verifyOtp({
      type,
      token_hash,
    })
    if (!error) {
      // redirect user to specified redirect URL or root of app
      redirect(next)
    }
  }

  // redirect the user to an error page with some instructions
  redirect('/auth/auth-code-error')
}
```

**SvelteKit:**

Create a new file at `src/routes/auth/confirm/+server.ts` and populate with the following:

**Astro:**

Create a new file at `src/pages/auth/confirm.ts` and populate with the following:

**Remix:**

Create a new file at `app/routes/auth.confirm.tsx` and populate with the following:

**Express:**

Create a new route in your express app and populate with the following:

##### Step 3: Call the sign up function to initiate the flow

**JavaScript:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/javascript/auth-signup) with their email address and password:

You can optionally specify a URL to redirect to after the user clicks the confirmation link. This URL must be configured as a [Redirect URL](https://supabase.com/docs/guides/auth/redirect-urls), which you can do in the [dashboard](https://supabase.com/dashboard/project/_/auth/url-configuration) for hosted projects, or in the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.additional_redirect_urls) for self-hosted projects.

If you don't specify a redirect URL, the user is automatically redirected to your site URL. This defaults to `localhost:3000`, but you can also configure this.

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
async function signUpNewUser() {
  const { data, error } = await supabase.auth.signUp({
    email: 'valid.email@supabase.io',
    password: 'example-password',
    options: {
      emailRedirectTo: 'https://example.com/welcome',
    },
  })
}
```

**Dart:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/dart/auth-signup) with their email address and password:

**Swift:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/swift/auth-signup) with their email address and password:

**Kotlin:**

To sign up the user, call [signUpWith(Email)](https://supabase.com/docs/reference/kotlin/auth-signup) with their email address and password:

**Python:**

To sign up the user, call [signUp()](https://supabase.com/docs/reference/python/auth-signup) with their email address and password:

**C#:**

To sign up the user, call [`SignUp()`](https://supabase.com/docs/reference/csharp/sign-up) with their email address and password:

### Signing in with an email and password

**JavaScript:**

When your user signs in, call [`signInWithPassword()`](https://supabase.com/docs/reference/javascript/auth-signinwithpassword) with their email address and password:

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
async function signInWithEmail() {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: 'valid.email@supabase.io',
    password: 'example-password',
  })
}
```

**Dart:**

When your user signs in, call [`signInWithPassword()`](https://supabase.com/docs/reference/dart/auth-signinwithpassword) with their email address and password:

**Swift:**

When your user signs in, call [signIn(email:password:)](https://supabase.com/docs/reference/swift/auth-signinwithpassword) with their email address and password:

**Kotlin:**

When your user signs in, call [signInWith(Email)](https://supabase.com/docs/reference/kotlin/auth-signinwithpassword) with their email address and password:

**Python:**

When your user signs in, call [sign_in_with_password()](https://supabase.com/docs/reference/python/auth-signinwithpassword) with their email address and password:

**C#:**

When your user signs in, call [`SignIn()`](https://supabase.com/docs/reference/csharp/sign-in-with-password) with their email address and password:

### Resetting a password

> **Note:** 

To prevent user enumeration, `resetPasswordForEmail()` doesn't reveal whether an account exists for the given email address.

When no user is associated with the address, Supabase Auth won't send an email, though the method still returns without an error.

**Implicit flow:**

#### Step 1: Create a reset password page

Create a **reset password** page. This page should be publicly accessible.

Collect the user's email address and request a password reset email. Specify the redirect URL, which should point to the URL of a **change password** page. This URL needs to be configured in your [redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls).

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
await supabase.auth.resetPasswordForEmail('valid.email@supabase.io', {
  redirectTo: 'http://example.com/account/update-password',
})
```

**Swift:**

**Kotlin:**

If you are on one of the Kotlin targets that have built-in support for redirect URL handling, such as Android, see [OAuth and OTP link verification](https://supabase.com/docs/reference/kotlin/initializing).

**Python:**

**Dart:**

**C#:**

#### Step 2: Create a change password page

Create a **change password** page at the URL you specified in the previous step. This page should be accessible only to authenticated users.

Collect the user's new password and call `updateUser` to update their password.

**PKCE flow:**

The PKCE flow allows for server-side authentication. Unlike the implicit flow, which directly provides your app with the access token after the user clicks the confirmation link, the PKCE flow requires an intermediate token exchange step before you can get the access token.

##### Step 1: Update reset password email

Update your reset password email template to send the token hash. See [Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates) for how to configure your email templates.

Your reset password email template should contain the following HTML:

##### Step 2: Create token exchange endpoint

Create an API endpoint at `/auth/confirm` to handle the token exchange.

> **Note:** 

Make sure you're using the right `supabase` client in the following code.

If you're not using Server-Side Rendering or cookie-based Auth, you can directly use the `createClient` from `@supabase/supabase-js`. If you're using Server-Side Rendering, see the [Server-Side Auth guide](https://supabase.com/docs/guides/auth/server-side/creating-a-client) for instructions on creating your Supabase client.

**Next.js:**

Create a new file at `app/auth/confirm/route.ts` and populate with the following:

```ts app/auth/confirm/route.ts
import { type EmailOtpType } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

// The client you created from the Server-Side Auth instructions
import { createClient } from '@/utils/supabase/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type') as EmailOtpType | null
  const next = searchParams.get('next') ?? '/'
  const redirectTo = request.nextUrl.clone()
  redirectTo.pathname = next

  if (token_hash && type) {
    const supabase = await createClient()

    const { error } = await supabase.auth.verifyOtp({
      type,
      token_hash,
    })
    if (!error) {
      return NextResponse.redirect(redirectTo)
    }
  }

  // return the user to an error page with some instructions
  redirectTo.pathname = '/auth/auth-code-error'
  return NextResponse.redirect(redirectTo)
}
```

**SvelteKit:**

Create a new file at `src/routes/auth/confirm/+server.ts` and populate with the following:

**Astro:**

Create a new file at `src/pages/auth/confirm.ts` and populate with the following:

**Remix:**

Create a new file at `app/routes/auth.confirm.tsx` and populate with the following:

**Express:**

Create a new route in your express app and populate with the following:

##### Step 3: Call the reset password by email function to initiate the flow

**JavaScript:**

```js
async function resetPassword() {
  const { data, error } = await supabase.auth.resetPasswordForEmail(email)
}
```

**Swift:**

**Kotlin:**

**Python:**

**Dart:**

**C#:**

Once you have a session, collect the user's new password and call `updateUser` to update their password.

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
await supabase.auth.updateUser({ password: 'new_password' })
```

**Swift:**

**Kotlin:**

**Python:**

**Dart:**

**C#:**

#### Verifying the current password

If your app requires users to confirm their current password before setting a new one, you can pass `current_password` (available in `supabase-js` v2.102.0+ and `supabase-kt` 3.5.0+):

**JavaScript:**

```js
await supabase.auth.updateUser({
  password: 'new_password',
  current_password: 'old_password',
})
```

**Kotlin:**

### Email sending

The signup confirmation and password reset flows require an SMTP server to send emails.

The Supabase platform comes with a default email-sending service for you to try out. The service has a rate limit of 2 emails per hour, and availability is on a best-effort basis. For production use, you should consider configuring a custom SMTP server.

> **Note:** 

Consider configuring a custom SMTP server for production.

See the [Custom SMTP guide](https://supabase.com/docs/guides/auth/auth-smtp) for instructions.

#### Local development with Mailpit

The Supabase CLI captures every email from local Auth in Mailpit, so you can test sign-up and password reset without sending email. For the steps, see [Test email flows locally](https://supabase.com/docs/guides/auth/testing-auth-flows#test-email-flows-locally).

## With phone

You can use a user's mobile phone number as an identifier, instead of an email address, when they sign up with a password.

This practice is usually discouraged because phone networks recycle mobile phone numbers. Anyone receiving a recycled phone number gets access to the original user's account. To mitigate this risk, [implement MFA](https://supabase.com/docs/guides/auth/auth-mfa).

> **Danger:** 

Protect users who use a phone number as a password-based auth identifier by enabling MFA.

### Enabling phone and password-based authentication

Enable phone authentication on the [Auth Providers page](https://supabase.com/dashboard/project/_/auth/providers) for hosted Supabase projects.

For self-hosted projects or local development, use the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.sms.enable_signup). See the configuration variables namespaced under `auth.sms`.

If you want users to confirm their phone number on signup, you need to set up an SMS provider. Each provider has its own configuration. Supported providers include MessageBird, Twilio, Vonage, and TextLocal (community-supported).

> **Caution:** 

To keep SMS sending costs under control, make sure you adjust your project's rate limits and [configure CAPTCHA](https://supabase.com/docs/guides/auth/auth-captcha). See the [Production Checklist](https://supabase.com/docs/guides/deployment/going-into-prod) to learn more.

Some countries have special regulations for services that send SMS messages to users, (e.g India's TRAI DLT regulations). Remember to look up and follow the regulations of countries where you operate.

### Signing up with a phone number and password

To sign up the user, call [`signUp()`](https://supabase.com/docs/reference/javascript/auth-signup) with their phone number and password:

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { data, error } = await supabase.auth.signUp({
  phone: '+13334445555',
  password: 'some-password',
})
```

**Swift:**

**Kotlin:**

**Python:**

**Dart:**

**C#:**

**HTTP:**

If you have phone verification turned on, the user receives an SMS with a 6-digit pin that you must verify within 60 seconds:

**JavaScript:**

You should present a form to the user so they can input the 6 digit pin, then send it along with the phone number to `verifyOtp`:

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const {
  data: { session },
  error,
} = await supabase.auth.verifyOtp({
  phone: '+13334445555',
  token: '123456',
  type: 'sms',
})
```

**Swift:**

You should present a form to the user so they can input the 6 digit pin, then send it along with the phone number to `verifyOTP`:

**Kotlin:**

You should present a form to the user so they can input the 6 digit pin, then send it along with the phone number to `verifyPhoneOtp`:

**Python:**

You should present a form to the user so they can input the 6 digit pin, then send it along with the phone number to `verify_otp`:

**Dart:**

You should present a form to the user so they can input the 6 digit pin, then send it along with the phone number to `verifyOTP`:

**C#:**

**HTTP:**

### Signing in a with a phone number and password

Call the function to sign in with the user's phone number and password:

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { data, error } = await supabase.auth.signInWithPassword({
  phone: '+13334445555',
  password: 'some-password',
})
```

**Swift:**

**Kotlin:**

**Python:**

**Dart:**

**C#:**

**HTTP:**
