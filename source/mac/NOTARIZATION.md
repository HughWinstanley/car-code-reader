# Making the Mac app open on any Mac (notarization)

The Mac build is already wired to sign + notarize automatically. It just needs an Apple
Developer ID certificate and a few credentials added as GitHub **secrets**. Until those are
added, the build falls back to ad-hoc signing (works on the build Mac, not reliably elsewhere).

Because Apple requires the account holder to be 18+, an **adult admin on the Company Six
Services LLC Apple Developer account** does the certificate part once.

## What to get (one time)

1. **Apple Developer Program membership** for Company Six Services LLC (apple.com/developer, ~$99/yr).
   It may already have one.
2. A **Developer ID Application** certificate:
   - developer.apple.com → Certificates → + → "Developer ID Application" → create → download.
   - Open the downloaded `.cer` (adds it to Keychain Access), then in Keychain Access right-click
     it → **Export** → save as a `.p12` and set a password. Keep both.
3. An **app-specific password** for notarizing:
   - account.apple.com → Sign-In & Security → App-Specific Passwords → generate one.
4. The **Team ID** (10 characters): developer.apple.com → Membership details.

## Add these 5 GitHub secrets

In the repo: Settings → Secrets and variables → Actions → New repository secret. Add:

| Secret name | Value |
|---|---|
| `MACOS_CERT_P12_BASE64` | the `.p12` file, base64-encoded: run `base64 -i cert.p12 | pbcopy` and paste |
| `MACOS_CERT_PASSWORD` | the password you set when exporting the `.p12` |
| `APPLE_ID` | the Apple ID email of the developer account |
| `APPLE_TEAM_ID` | the 10-character Team ID |
| `APPLE_APP_PASSWORD` | the app-specific password from step 3 |

That's it. The next Mac build signs with the Developer ID, notarizes with Apple, and staples the
ticket — so the app opens by double-click on any Mac, no warnings, no Terminal.
