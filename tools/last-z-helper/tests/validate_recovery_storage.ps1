$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path (Split-Path $PSScriptRoot))
$jdk=if($env:JAVA_HOME){$env:JAVA_HOME}else{'C:/Program Files/Java/jdk-17'}
$jar="$root/runtime/helper-build/json-20240303.jar"
$expected='3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'
if(-not(Test-Path $jar)){Invoke-WebRequest -UseBasicParsing -Uri 'https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar' -OutFile $jar}
if((Get-FileHash $jar -Algorithm SHA256).Hash.ToLower() -ne $expected){throw 'Pinned test JSON dependency mismatch'}
$classes="$root/runtime/helper-build/recovery-jvm-$([Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Force $classes | Out-Null
$src="$root/tools/last-z-helper/src/dev/codex/lastzhelper"
$files=@('MaintenanceResult','MaintenanceSchedule','RotationPolicy','RotationShortcut','RotationProfiles','RecoveryPolicy','RecoveryState','RunRequest','ControllerOwnership','LegacyOwnershipSession','ReconciliationPolicy','RecoveryEngine','ControllerLease','BoomerPolicy','BoomerReconciliationPolicy') | ForEach-Object {"$src/$_.java"}
& "$jdk/bin/javac.exe" -encoding UTF-8 -cp $jar -d $classes $files "$PSScriptRoot/jvm/StateProbe.java" "$PSScriptRoot/jvm/RotationFiles.java" "$PSScriptRoot/jvm/RecoveryStorageTests.java" "$PSScriptRoot/jvm/OwnershipProtocolTests.java" "$PSScriptRoot/jvm/OwnershipLockProbe.java" "$PSScriptRoot/jvm/ReconciliationTests.java" "$PSScriptRoot/jvm/RecoveryEngineTests.java" "$PSScriptRoot/jvm/ControllerLeaseTests.java" "$PSScriptRoot/jvm/BoomerReconciliationTests.java"
if($LASTEXITCODE){throw 'Recovery/session JVM compilation failed'}
& "$jdk/bin/java.exe" -cp "$classes;$jar" dev.codex.lastzhelper.RecoveryStorageTests
if($LASTEXITCODE){throw 'Recovery/session/default persistence tests failed'}

& "$jdk/bin/java.exe" -cp "$classes;$jar" dev.codex.lastzhelper.OwnershipProtocolTests
if($LASTEXITCODE){throw 'Shared ownership protocol tests failed'}

& "$jdk/bin/java.exe" -cp "$classes;$jar" dev.codex.lastzhelper.ReconciliationTests
if($LASTEXITCODE){throw 'Read-only reconciliation tests failed'}

& "$jdk/bin/java.exe" -cp "$classes;$jar" dev.codex.lastzhelper.RecoveryEngineTests
if($LASTEXITCODE){throw 'Recovery orchestration tests failed'}

& "$jdk/bin/java.exe" -cp "$classes;$jar" dev.codex.lastzhelper.ControllerLeaseTests
if($LASTEXITCODE){throw 'Recovery ownership handoff tests failed'}

& "$jdk/bin/java.exe" -cp "$classes;$jar" dev.codex.lastzhelper.BoomerReconciliationTests
if($LASTEXITCODE){throw 'Auto Boomer read-only reconciliation tests failed'}
