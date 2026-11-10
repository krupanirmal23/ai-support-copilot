# Custom Access Token Hook

Customize the access token issued by Supabase Auth

The custom access token hook runs before a token is issued and allows you to add additional claims based on the authentication method used.

Claims returned must conform to our specification. Supabase Auth will check for these claims after the hook is run and return an error if they are not present.

These are the fields currently available on an access token:

Required Claims: `iss`, `aud`, `exp`, `iat`, `sub`, `role`, `aal`, `session_id`, `email`, `phone`, `is_anonymous`

Optional Claims: `jti`, `nbf`, `app_metadata`, `user_metadata`, `amr`,

**Inputs**

| Field                   | Type     | Description                                                                                                                                                                                                                                                                |
| ----------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `user_id`               | `string` | Unique identifier for the user attempting to sign in.                                                                                                                                                                                                                      |
| `claims`                | `object` | Claims which are included in the access token.                                                                                                                                                                                                                             |
| `authentication_method` | `string` | The authentication method used to request the access token. Possible values include: `oauth`, `password`, `otp`, `totp`, `recovery`, `invite`, `sso/saml`, `magiclink`, `email/signup`, `email_change`, `token_refresh`, `oauth_provider/authorization_code`, `anonymous`. |

**JSON:**

```json
{
  "user_id": "8ccaa7af-909f-44e7-84cb-67cdccb56be6",
  "claims": {
    "aud": "authenticated",
    "exp": 1715690221,
    "iat": 1715686621,
    "sub": "8ccaa7af-909f-44e7-84cb-67cdccb56be6",
    "email": "",
    "phone": "",
    "app_metadata": {},
    "user_metadata": {},
    "role": "authenticated",
    "aal": "aal1",
    "amr": [ { "method": "anonymous", "timestamp": 1715686621 } ],
    "session_id": "4b938a09-5372-4177-a314-cfa292099ea2",
    "is_anonymous": true,
    "client_id": "oauth-client-id-if-oauth-flow"
  },
  "authentication_method": "anonymous"
}
```

**JSON Schema:**

**Outputs**

Return these only if your hook processed the input without errors.

| Field    | Type     | Description                                     |
| -------- | -------- | ----------------------------------------------- |
| `claims` | `object` | The updated claims after the hook has been run. |

**SQL:**

**Minimal JWT:**

Sometimes the size of the JWT can be a problem especially if you're using a [Server-Side Rendering framework](https://supabase.com/docs/guides/auth/server-side). Common situations where the JWT can get too large include:

- The user has a particularly large name, email address or phone number
- The default JWT has too many claims coming from OAuth providers
- A large avatar URL is included

To lower the size of the JWT you can define a Custom Access Token hook like the one below which will instruct the Auth server to issue a JWT with only the listed claims. Check the documentation above on what JWT claims must be present and cannot be removed.

Refer to the [Postgres JSON functions](https://www.postgresql.org/docs/current/functions-json.html) on how to manipulate `jsonb` objects.

```sql
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
as $$
  declare
    original_claims jsonb;
    new_claims jsonb;
    claim text;
  begin
    original_claims = event->'claims';
    new_claims = '{}'::jsonb;

    foreach claim in array array[
      -- add claims you want to keep here
      'iss',
      'aud',
      'exp',
      'iat',
      'sub',
      'role',
      'aal',
      'session_id',
      'email',
      'phone',
      'is_anonymous'
   ] loop
      if original_claims ? claim then
        -- original_claims contains one of the listed claims, set it on new_claims
        new_claims = jsonb_set(new_claims, array[claim], original_claims->claim);
      end if;
    end loop;

    return jsonb_build_object('claims', new_claims);
  end
$$;
```

**Add admin role:**

You can allow registered admin users to perform restricted actions by granting an `admin` claim to their token.

Create a profiles table with an `is_admin` flag:

Create a hook:

**Restrict access to SSO users:**

You can restrict access to internal applications with a hook. For example, you can require that employees sign in via [SAML Single Sign On (SSO)](https://supabase.com/docs/guides/auth/enterprise-sso/auth-sso-saml). You can exempt select employees from the policy via an allowlist.

**HTTP:**

**Add claim:**

Your company wishes to add assign permissions via the role claim on the `app_metadata` field. Add the role claim to the token via a Hook.

```javascript
import { readAll } from 'https://deno.land/std/io/read_all.ts'
import * as base64 from 'https://denopkg.com/chiefbiiko/base64/mod.ts'
import { Webhook } from 'https://esm.sh/standardwebhooks@1.0.0'

Deno.serve(async (req) => {
  const payload = await req.text()
  const base64_secret = Deno.env.get('CUSTOM_ACCESS_TOKEN_SECRET').replace('v1,whsec_', '')
  const headers = Object.fromEntries(req.headers)
  const wh = new Webhook(base64_secret)
  try {
    const { user_id, claims, authentication_method } = wh.verify(payload, headers)
    if (claims.app_metadata && claims.app_metadata.role) {
      claims['role'] = claims.app_metadata.role
    }
    return new Response(
      JSON.stringify({
        claims,
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: `Failed to process the request: ${error}`,
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
  }
})
```

**Restrict access to SSO users:**

You can restrict access to internal applications with a hook. For example, you can require that employees sign in via [SAML Single Sign On (SSO)](https://supabase.com/docs/guides/auth/enterprise-sso/auth-sso-saml). You can exempt select employees from the policy via an allowlist.
