# Android client

A native Kotlin + Jetpack Compose client for the MOJO AGENT local API.

## Build
1. Install Android Studio (Ladybug or newer) with Android SDK 35 and JDK 17.
2. Open this `android/` folder as a Gradle project.
3. Let Android Studio sync Gradle; it will create/download the wrapper as needed.
4. Select the `app` run configuration and build a debug APK.

## Connect
- Android emulator: API base URL `http://10.0.2.2:8766/api/v1`.
- Physical Android device over USB: start the backend on the PC, then run `adb reverse tcp:8766 tcp:8766`; use `http://127.0.0.1:8766/api/v1` in the app.
- The API binds to loopback only. Do not expose it to a public or untrusted network.

The client currently supports runtime health checks and goal planning. More Android-native screens, offline cache, background task controls and release signing remain future implementation work. Cleartext HTTP is only for local development; production remote access requires authenticated TLS.
