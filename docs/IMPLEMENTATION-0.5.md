# MOJO AGENT 0.5 implementation notes

## Persistent evolution
Candidate strategy parameters, fitness, generation, validation and approval state now persist in SQLite. The champion is stored separately and restored when the API starts. Candidate approval still requires passing validation and an explicit approval request. This does not mutate source code or security policy.

## Workflow hardening
Only text, calculator and text-statistics steps are accepted. Inputs are size-bounded before storage. Failed executions are recorded in history. Per-workflow history is available through the API.

## Android build
AndroidX is enabled explicitly in android/gradle.properties to address the previous Gradle metadata failure. A successful debug APK still requires a passing GitHub Actions run and artifact upload.

## Remaining boundaries
No arbitrary shell execution, unattended evolution activation, background scheduler, signed release APK/AAB, full Android dashboard port or native Mojo compiler certification is included here.
