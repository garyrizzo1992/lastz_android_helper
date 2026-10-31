param([switch]$Install,[switch]$DexOnly,[string]$Serial='emulator-5556')
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot)
python "$PSScriptRoot/audit_input_positions.py"
if($LASTEXITCODE){throw 'Input-position audit failed'}
$sdk=if($env:LASTZ_ANDROID_SDK){$env:LASTZ_ANDROID_SDK}else{"$env:LOCALAPPDATA/Android/Sdk"}
$jdk=if($env:JAVA_HOME){$env:JAVA_HOME}else{'C:/Program Files/Java/jdk-17'}
$tools="$sdk/build-tools/35.0.1"
$build="$root/runtime/helper-build"
$classes="$build/compile-classes-$([Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Force $classes,"$build/dex","$root/bin" | Out-Null
if(-not(Test-Path "$PSScriptRoot/assets/injector.dat")){throw 'Bundled Frida 17.24.3 injector is missing; see README.'}
if((Get-FileHash "$PSScriptRoot/assets/injector.dat" -Algorithm SHA256).Hash.ToLower() -ne 'a76888ee76394b5909d4b3cbb81761ead1f87e14178e6ed3252e60755f664240'){throw 'Injector hash mismatch'}
if(-not(Test-Path "$PSScriptRoot/assets/injector-arm64.dat")){throw 'Run python tools/last-z-helper/fetch_arm64.py first'}
if((Get-FileHash "$PSScriptRoot/assets/injector-arm64.dat" -Algorithm SHA256).Hash.ToLower() -ne '3133d798ef48aa10fec06594ad9b69d80220038ebdaa4775c836741bfc3bf5a4'){throw 'ARM64 injector hash mismatch'}
$prefix=[IO.File]::ReadAllText("$PSScriptRoot/assets/java-bridge-prefix.js")
$tail=[IO.File]::ReadAllText("$PSScriptRoot/gesture-geometry.js")+[IO.File]::ReadAllText("$PSScriptRoot/scene-geometry.js")+[IO.File]::ReadAllText("$PSScriptRoot/unity-ui.js")+[IO.File]::ReadAllText("$PSScriptRoot/input-agent-tail.js")
[IO.File]::WriteAllText("$PSScriptRoot/assets/input-agent.js",$prefix+$tail,(New-Object Text.UTF8Encoding($false)))
New-Item -ItemType Directory -Force "$PSScriptRoot/assets/licenses" | Out-Null
Copy-Item "$PSScriptRoot/FRIDA-LICENSE.txt","$PSScriptRoot/FRIDA-JAVA-BRIDGE-LICENSE.txt" "$PSScriptRoot/assets/licenses"
python "$PSScriptRoot/package_history.py"
if($LASTEXITCODE){throw 'History packaging failed'}
& "$jdk/bin/javac.exe" -encoding UTF-8 -source 8 -target 8 -classpath "$sdk/platforms/android-35/android.jar" -d $classes (Get-ChildItem "$PSScriptRoot/src" -Recurse -Filter '*.java' | ForEach-Object FullName)
if($LASTEXITCODE){throw 'javac failed'}
$env:JAVA_HOME=$jdk
& "$jdk/bin/jar.exe" cf "$build/compiled-classes.jar" -C $classes .
if($LASTEXITCODE){throw 'Class archive failed'}
& "$tools/d8.bat" --lib "$sdk/platforms/android-35/android.jar" --min-api 26 --output "$build/dex" "$build/compiled-classes.jar"
if($LASTEXITCODE){throw 'd8 failed'}
[IO.File]::WriteAllText("$build/latest-classes.txt",$classes)
if($DexOnly){Write-Output "Built $build/dex/classes.dex";return}
& "$tools/aapt.exe" package -f -A "$PSScriptRoot/assets" -M "$PSScriptRoot/AndroidManifest.xml" -I "$sdk/platforms/android-35/android.jar" -F "$build/unsigned.apk"
if($LASTEXITCODE){throw 'aapt failed'}
python -c "import zipfile; z=zipfile.ZipFile(r'$build/unsigned.apk','a'); z.write(r'$build/dex/classes.dex','classes.dex'); z.close()"
if($LASTEXITCODE){throw 'dex packaging failed'}
& "$tools/zipalign.exe" -f 4 "$build/unsigned.apk" "$build/aligned.apk"
if($LASTEXITCODE){throw 'zipalign failed'}
$key="$build/test-key.jks"
if(-not(Test-Path $key)){& "$jdk/bin/keytool.exe" -genkeypair -keystore $key -storepass android -keypass android -alias helper -keyalg RSA -keysize 2048 -validity 3650 -dname 'CN=Local Last Z Helper' -noprompt}
& "$tools/apksigner.bat" sign --ks $key --ks-pass pass:android --out "$root/bin/last-z-helper.apk" "$build/aligned.apk"
if($LASTEXITCODE){throw 'sign failed'}
& "$tools/apksigner.bat" verify "$root/bin/last-z-helper.apk"
if($LASTEXITCODE){throw 'signature verification failed'}
if($Install){& "$root/scrcpy/adb.exe" -s $Serial install --no-incremental -r "$root/bin/last-z-helper.apk";if($LASTEXITCODE){throw 'Install failed'}}
Write-Output "Built $root/bin/last-z-helper.apk"
