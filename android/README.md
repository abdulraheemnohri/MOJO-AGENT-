# Android client

Native Kotlin + Jetpack Compose companion for the MOJO AGENT local API.

## Current screens

- **Home:** backend health check and connection guidance.
- **Planner:** submit goals to deterministic task decomposition.
- **Memory:** add/list/export persistent memory through the API.
- **Workflows:** create a bounded text-step workflow and list saved workflows.
- **Settings:** read and update the server theme preference; shows the security boundary.

## Build a debug APK

### GitHub Actions

1. Open the repository's Actions tab.
2. Select **Android Debug APK** and choose **Run workflow** on `implementation/full-platform`.
3. Download the `mojo-agent-debug-apk` artifact from a successful run.

The workflow uses JDK 17, Android SDK 35 and Gradle 8.9. It builds a debug APK and retains the artifact for 14 days.

### Windows 10

Install Android Studio, Android SDK Platform 35, JDK 17 and Gradle 8.9, then run:

```powershell
gradle --no-daemon -p android :app:assembleDebug
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`.

## Connect to backend

- Android emulator: `http://10.0.2.2:8766/api/v1`
- Physical phone over USB: start the backend on the PC, run `adb reverse tcp:8766 tcp:8766`, then use `http://127.0.0.1:8766/api/v1`.

The API binds to loopback only. Cleartext HTTP is intended for local development; production remote access requires authenticated TLS. The Android app is a companion client, not a full desktop-dashboard port. The current client does not include graph visualization, voice, file attachments, or background execution.
