# Phone sign-in

Phone sign-in is a method of authentication that allows users to sign in to a website or application without using a password. The user authenticates through a one-time password (OTP) sent via a channel (SMS or WhatsApp).

> **Note:** 

At this time, `WhatsApp` is only supported as a channel for the Twilio and Twilio Verify Providers.

Users can also sign in with their phones using Native Mobile Login with the built-in identity provider. For Native Mobile Login with Android and iOS, see the [social sign-in guides](https://supabase.com/docs/guides/auth/social-sign-in).

Phone OTP sign-in can:

- Improve the user experience by not requiring users to create and remember a password
- Increase security by reducing the risk of password-related security breaches
- Reduce support burden of dealing with password resets and other password-related flows

> **Caution:** 

To keep SMS sending costs under control, make sure you adjust your project's rate limits and [configure CAPTCHA](https://supabase.com/docs/guides/auth/auth-captcha). See the [Production Checklist](https://supabase.com/docs/guides/deployment/going-into-prod) to learn more.

Some countries have special regulations for services that send SMS messages to users, (e.g India's TRAI DLT regulations). Remember to look up and follow the regulations of countries where you operate.

## Enabling phone sign-in

Enable phone authentication on the [Auth Providers page](https://supabase.com/dashboard/project/_/auth/providers) for hosted Supabase projects.

For self-hosted projects or local development, use the [configuration file](https://supabase.com/docs/guides/local-development/cli/config#auth.sms.enable_signup). See the configuration variables namespaced under `auth.sms`.

You also need to set up an SMS provider. Each provider has its own configuration. Supported providers include MessageBird, Twilio, Vonage, and TextLocal (community-supported).

By default, a user can only request an OTP once every 60 seconds and they expire after 1 hour.

To test phone sign-in without sending SMS, [add test phone numbers with fixed codes](https://supabase.com/docs/guides/auth/testing-auth-flows#test-phone-sign-in-with-test-numbers).

## Signing in with phone OTP

With OTP, a user can sign in without setting a password on their account. They need to verify their phone number each time they sign in.

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { data, error } = await supabase.auth.signInWithOtp({
  phone: '+13334445555',
})
```

**Swift:**

**Kotlin:**

To send the OTP via WhatsApp instead of SMS (requires Twilio or Twilio Verify provider):

**Python:**

**C#:**

**HTTP:**

The user receives an SMS with a 6-digit pin that you must verify within 60 seconds.

## Verifying a phone OTP

To verify the one-time password (OTP) sent to the user's phone number, call [`verifyOtp()`](https://supabase.com/docs/reference/javascript/auth-verifyotp) with the phone number and OTP:

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
  phone: '13334445555',
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

**C#:**

You should present a form to the user so they can input the 6 digit pin, then send it along with the phone number to `VerifyOTP`:

**HTTP:**

If successful, the user will now be signed in and you should receive a valid session like:

```json
{
  "access_token": "<ACCESS_TOKEN>",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "<REFRESH_TOKEN>"
}
```

The access token can be sent in the Authorization header as a Bearer token for any CRUD operations on supabase-js. See our guide on [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) for more info on restricting access on a user basis.

## Updating a phone number

To update a user's phone number, the user must be signed in. Call [`updateUser()`](https://supabase.com/docs/reference/javascript/auth-updateuser) with their phone number:

**JavaScript:**

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { data, error } = await supabase.auth.updateUser({
  phone: '123456789',
})
```

**Swift:**

**Kotlin:**

**Python:**

**C#:**

The user receives an SMS with a 6-digit pin that you must [verify](#verifying-a-phone-otp) within 60 seconds.
Use the `phone_change` type when calling `verifyOTP` to update a user’s phone number.
