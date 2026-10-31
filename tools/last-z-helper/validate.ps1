$ErrorActionPreference='Stop'
& "$PSScriptRoot/build.ps1" -DexOnly
if($LASTEXITCODE){throw 'Build failed'}
$root=Split-Path (Split-Path $PSScriptRoot)
$jdk=if($env:JAVA_HOME){$env:JAVA_HOME}else{'C:/Program Files/Java/jdk-17'}
$classes=[IO.File]::ReadAllText("$root/runtime/helper-build/latest-classes.txt")
$testClasses="$root/runtime/helper-build/validation-tests"
New-Item -ItemType Directory -Force $testClasses | Out-Null
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/RunLogTests.java"
if($LASTEXITCODE){throw 'Run log test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.RunLogTests
if($LASTEXITCODE){throw 'Run log retention tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/RecoveryPolicyTests.java"
if($LASTEXITCODE){throw 'Recovery policy test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.RecoveryPolicyTests
if($LASTEXITCODE){throw 'Recovery policy tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/RotationPolicyTests.java"
if($LASTEXITCODE){throw 'Rotation test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.RotationPolicyTests
if($LASTEXITCODE){throw 'Rotation policy tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/RuleTests.java"
if($LASTEXITCODE){throw 'Rule test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.RuleTests
if($LASTEXITCODE){throw 'Rule tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/TruckCargoTests.java"
if($LASTEXITCODE){throw 'Truck cargo test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.TruckCargoTests
if($LASTEXITCODE){throw 'Truck cargo tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/TruckHideTests.java"
if($LASTEXITCODE){throw 'Truck filter test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.TruckHideTests
if($LASTEXITCODE){throw 'Truck filter tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/DeadStatePolicyTests.java"
if($LASTEXITCODE){throw 'Dead-state policy compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.DeadStatePolicyTests
if($LASTEXITCODE){throw 'Dead-state policy tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/MaintenanceCoreTests.java"
if($LASTEXITCODE){throw 'Maintenance test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.MaintenanceCoreTests
if($LASTEXITCODE){throw 'Maintenance tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/WantedWorkflowTests.java"
if($LASTEXITCODE){throw 'Wanted test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.WantedWorkflowTests
if($LASTEXITCODE){throw 'Wanted tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/WantedWindowPolicyTests.java"
if($LASTEXITCODE){throw 'Wanted window policy compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.WantedWindowPolicyTests
if($LASTEXITCODE){throw 'Wanted window policy tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/WantedCacheTests.java"
if($LASTEXITCODE){throw 'Wanted cache test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.WantedCacheTests
if($LASTEXITCODE){throw 'Wanted cache tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/MailCoverageTests.java"
if($LASTEXITCODE){throw 'Mail coverage test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.MailCoverageTests
if($LASTEXITCODE){throw 'Mail coverage tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/MailHeaderProbeTests.java"
if($LASTEXITCODE){throw 'Mail header test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.MailHeaderProbeTests
if($LASTEXITCODE){throw 'Mail header tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/BaseBubblePolicyTests.java"
if($LASTEXITCODE){throw 'Base bubble test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.BaseBubblePolicyTests
if($LASTEXITCODE){throw 'Base bubble tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/RuntimeAssetIdentityTests.java"
if($LASTEXITCODE){throw 'Runtime asset test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.RuntimeAssetIdentityTests
if($LASTEXITCODE){throw 'Runtime asset tests failed'}
& "$jdk/bin/javac.exe" -cp $classes -d $testClasses "$PSScriptRoot/tests/TrainingStartPolicyTests.java"
if($LASTEXITCODE){throw 'Training start policy test compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.TrainingStartPolicyTests
if($LASTEXITCODE){throw 'Training start policy tests failed'}
node --check "$PSScriptRoot/assets/input-agent.js"
if($LASTEXITCODE){throw 'Agent syntax failed'}
node "$PSScriptRoot/tests/alliance_menu_guard.test.js"
if($LASTEXITCODE){throw 'Alliance menu guard tests failed'}
node "$PSScriptRoot/tests/gesture_geometry.test.js"
if($LASTEXITCODE){throw 'Geometry tests failed'}
node "$PSScriptRoot/tests/native_field_cache.test.js"
if($LASTEXITCODE){throw 'Native field-cache tests failed'}
python -m unittest discover -s "$PSScriptRoot/tests" -p 'test_*.py'
if($LASTEXITCODE){throw 'Python tests failed'}

node "$PSScriptRoot/tests/scene_geometry.test.js"
if($LASTEXITCODE){throw 'Scene geometry tests failed'}

& "$PSScriptRoot/tests/validate_recovery_storage.ps1"

& "$jdk/bin/javac.exe" -encoding UTF-8 -cp $classes -d $testClasses "$PSScriptRoot/tests/BoomerPolicyTests.java"
if($LASTEXITCODE){throw 'Auto Boomer policy compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.BoomerPolicyTests
if($LASTEXITCODE){throw 'Auto Boomer policy tests failed'}
node "$PSScriptRoot/tests/event_carousel_guard.test.js"
if($LASTEXITCODE){throw 'Event carousel guard tests failed'}

node "$PSScriptRoot/tests/boomer_activation_guard.test.js"
if($LASTEXITCODE){throw 'Auto Boomer native activation tests failed'}

& "$jdk/bin/javac.exe" -encoding UTF-8 -cp $classes -d $testClasses "$PSScriptRoot/tests/BoomerNavigationTests.java"
if($LASTEXITCODE){throw 'Auto Boomer navigation scope compilation failed'}
& "$jdk/bin/java.exe" -cp "$testClasses;$classes" dev.codex.lastzhelper.BoomerNavigationTests
if($LASTEXITCODE){throw 'Auto Boomer navigation scope tests failed'}
node "$PSScriptRoot/tests/boomer_navigation_guard.test.js"
if($LASTEXITCODE){throw 'Auto Boomer native navigation tests failed'}
