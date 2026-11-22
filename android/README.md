# Android client

Native Kotlin + Jetpack Compose companion for the MOJO AGENT local API.

## Build a debug APK

### Recommended: GitHub Actions (no local Android SDK required)

1. Open the repository's **Actions** tab.
2. Select **Android Debug APK**.
3. Choose **Run workflow** on the `implementation/full-platform` branch.
4. Open the completed run and download the `mojo-agent-debug-apk` artifact.
5. Extract the ZIP; it contains `app-debug.apk`.

The workflow uses JDK 17, Android SDK 35 and Gradle 8.9. It builds the debug variant only. The artifact is retained for 14 days. Pull requests and pushes that change `android/**` also trigger the build.

### Build locally on Windows 10

1. Install Android Studio and its Android SDK Platform 35.
2. Install JDK 17 and Gradle 8.9, and ensure `java`, `gradle` and `sdkmanager` are on PATH.
3. Open a terminal in the repository root and run:

```powershell
gradle --no-daemon -p android :app:assembleDebug
```

APK output:

```
android/app/build/outputs/apk/debug/app-debug.apk
```

## Connect to the backend

- Android emulator: `http://10.0.2.2:8766/api/v1`
- Physical Android device over USB: start the backend on the PC, run `adb reverse tcp:8766 tcp:8766`, then use `http://127.0.0.1:8766/api/v1`.

The API binds to loopback only. Do not expose it to a public or untrusted network. The app currently supports backend health checks and goal planning. Cleartext HTTP is intended only for local development; production remote access requires authenticated TLS.

## Build status

The workflow builds and packages a debug APK. It does not create a signed release APK or AAB. Android UI coverage is currently a starter client, not the full desktop dashboard port.
