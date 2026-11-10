# Identity Linking

Manage the identities associated with your user

## Identity linking strategies

Currently, Supabase Auth supports 2 strategies to link an identity to a user:

1. [Automatic Linking](#automatic-linking)
2. [Manual Linking](#manual-linking-beta)

> **Note:** 

Users that signed up with [SAML SSO](https://supabase.com/docs/guides/auth/enterprise-sso/auth-sso-saml) will not be considered as targets for identity linking (automatic or manual) for security reasons.

### Automatic linking

Supabase Auth automatically links identities with the same email address to a single user. This helps to improve the user experience when multiple OAuth sign-in options are presented since the user does not need to remember which OAuth account they used to sign up with. When a new user signs in with OAuth, Supabase Auth will attempt to look for an existing user that uses the same email address. If a match is found, the new identity is linked to the user.

In order for automatic linking to correctly identify the user for linking, Supabase Auth needs to ensure that all user emails are unique. It would also be an insecure practice to automatically link an identity to a user with an unverified email address since that could lead to pre-account takeover attacks. To prevent this from happening, when a new identity can be linked to an existing user, Supabase Auth will remove any other unconfirmed identities linked to an existing user.

### Manual linking (beta)

**JavaScript:**

Supabase Auth allows a user to initiate identity linking with a different email address when they are signed in. To link an OAuth identity to the user, call [`linkIdentity()`](https://supabase.com/docs/reference/javascript/auth-linkidentity):

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
const { data, error } = await supabase.auth.linkIdentity({ provider: 'google' })
```

**Dart:**

Supabase Auth allows a user to initiate identity linking with a different email address when they are signed in. To link an OAuth identity to the user, call [`linkIdentity()`](https://supabase.com/docs/reference/dart/auth-linkidentity):

**Swift:**

Supabase Auth allows a user to initiate identity linking with a different email address when they are signed in. To link an OAuth identity to the user, call [`linkIdentity()`](https://supabase.com/docs/reference/swift/auth-linkidentity):

**Kotlin:**

Supabase Auth allows a user to initiate identity linking with a different email address when they are signed in. To link an OAuth identity to the user, call [`linkIdentity()`](https://supabase.com/docs/reference/kotlin/auth-linkidentity):

**Python:**

Supabase Auth allows a user to initiate identity linking with a different email address when they are signed in. To link an OAuth identity to the user, call [`link_identity()`](https://supabase.com/docs/reference/python/auth-linkidentity):

**C#:**

Supabase Auth allows a user to initiate identity linking with a different email address when they are signed in. To link an OAuth identity to the user, call [`LinkIdentity()`](https://supabase.com/docs/reference/csharp/link-identity):

In the example above, the user will be redirected to Google to complete the OAuth2.0 flow. Once the OAuth2.0 flow has completed successfully, the user will be redirected back to the application and the Google identity will be linked to the user. You can enable manual linking from your project's authentication [configuration options](https://supabase.com/dashboard/project/_/auth/providers) or by setting the environment variable `GOTRUE_SECURITY_MANUAL_LINKING_ENABLED: true` when self-hosting.

### Link identity with native OAuth (ID token)

**JavaScript:**

For native mobile applications, you can link an identity using an ID token obtained from a third-party OAuth provider. This is useful when you want to use native OAuth flows (like Google Sign-In or [Sign in with Apple](https://supabase.com/docs/guides/auth/social-sign-in/auth-apple)) rather than web-based OAuth redirects.

```js
// Example with Google Sign-In (using a native Google Sign-In library)
const idToken = 'ID_TOKEN_FROM_GOOGLE'
const accessToken = 'ACCESS_TOKEN_FROM_GOOGLE'

const { data, error } = await supabase.auth.linkIdentity({
  provider: 'google',
  token: idToken,
  access_token: accessToken,
})
```

**Dart:**

For Flutter applications, you can link an identity using an ID token obtained from native OAuth packages like `google_sign_in` or `sign_in_with_apple`. Call [`linkIdentityWithIdToken()`](https://supabase.com/docs/reference/dart/auth-linkidentitywithidtoken):

This method supports the same OAuth providers as `signInWithIdToken()`: Google, Apple, Facebook, Kakao, and Keycloak.

## Unlink an identity

**JavaScript:**

You can use [`getUserIdentities()`](https://supabase.com/docs/reference/javascript/auth-getuseridentities) to fetch all the identities linked to a user. Then, call [`unlinkIdentity()`](https://supabase.com/docs/reference/javascript/auth-unlinkidentity) to unlink the identity. The user needs to be signed in and have at least 2 linked identities in order to unlink an existing identity.

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('https://your-project-id.supabase.co', 'sb_publishable_...')

// ---cut---
// retrieve all identities linked to a user
const { data: identities, error: identitiesError } = await supabase.auth.getUserIdentities()

if (!identitiesError) {
  // find the google identity linked to the user
  const googleIdentity = identities.identities.find((identity) => identity.provider === 'google')

  if (googleIdentity) {
    // unlink the google identity from the user
    const { data, error } = await supabase.auth.unlinkIdentity(googleIdentity)
  }
}
```

**Dart:**

You can use [`getUserIdentities()`](https://supabase.com/docs/reference/dart/auth-getuseridentities) to fetch all the identities linked to a user. Then, call [`unlinkIdentity()`](https://supabase.com/docs/reference/dart/auth-unlinkidentity) to unlink the identity. The user needs to be signed in and have at least 2 linked identities in order to unlink an existing identity.

**Swift:**

You can use [`getUserIdentities()`](https://supabase.com/docs/reference/swift/auth-getuseridentities) to fetch all the identities linked to a user. Then, call [`unlinkIdentity()`](https://supabase.com/docs/reference/swift/auth-unlinkidentity) to unlink the identity. The user needs to be signed in and have at least 2 linked identities in order to unlink an existing identity.

**Kotlin:**

You can use [`currentIdentitiesOrNull()`](https://supabase.com/docs/reference/kotlin/auth-getuseridentities) to get all the identities linked to a user. Then, call [`unlinkIdentity()`](https://supabase.com/docs/reference/kotlin/auth-unlinkidentity) to unlink the identity. The user needs to be signed in and have at least 2 linked identities in order to unlink an existing identity.

**Python:**

You can use [`get_user_identities()`](https://supabase.com/docs/reference/python/auth-getuseridentities) to fetch all the identities linked to a user. Then, call [`unlink_identity()`](https://supabase.com/docs/reference/python/auth-unlinkidentity) to unlink the identity. The user needs to be signed in and have at least 2 linked identities in order to unlink an existing identity.

**C#:**

Use `CurrentUser.Identities` to get all the identities linked to a user. Then, call [`UnlinkIdentity()`](https://supabase.com/docs/reference/csharp/unlink-identity) to unlink the identity. The user needs to be signed in and have at least 2 linked identities in order to unlink an existing identity.

## Frequently asked questions

### How to add email/password sign-in to an OAuth account?

Call the `updateUser({ password: 'validpassword'})` to add email with password authentication to an account created with an OAuth provider (Google, GitHub, etc.).

### Can you sign up with email if already using OAuth?

If you try to create an email account after previously signing up with OAuth using the same email, you'll receive an obfuscated user response with no verification email sent. This prevents user enumeration attacks.
