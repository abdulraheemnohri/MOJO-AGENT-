# Platform integration and release checklist
- Windows: run `scripts/windows-start.bat` or `scripts/windows-start.ps1`; requires Python 3.10+.
- Android: open `android/` in Android Studio; build a debug APK with Gradle. Configure the API URL. Emulator uses `10.0.2.2`; a physical phone needs the host LAN address and same trusted network. Cleartext HTTP is only suitable for local development; do not expose this service to untrusted networks.
- API settings persist in SQLite. The service deliberately accepts only loopback bind addresses in the current release.
- Evolution candidate activation is separate from generation: run experiment, validate candidate, then explicitly approve. This is in-memory until process restart.
- Native Mojo compiler support remains dependent on a compatible Modular toolchain. Python reference runtime is the supported cross-platform baseline today.
- No APK/AAB or Windows executable is claimed until built and tested in their respective toolchains.
