# Codebase access and instrumentation audit coverage

Updated 2026-10-29. This is a coverage checkpoint, not a completed security or anti-cheat assessment. No detector probing or enforcement experiments were performed. Actual detection mechanisms and probabilities remain unknown.

The saved BOT_DETECTION_AUDIT_MANIFEST.csv inventories181 source entries:180 first-party and1 excluded vendor bridge. It records56 focused source reviews and124 pattern-only scans. Languages:100Java,57Python,10Go,7JavaScript,5PowerShell,1shell,1cmd. These are manifest counts, not proof every repository artifact or dependency was reviewed. Generated/runtime dumps, packaged binaries, third-party dependencies and vendor internals are outside this review.

## Reviewed areas and concrete improvements

Focused review covers the helper's memory readers and identity checks, injector session lifecycle, native geometry/input guards, maintenance journal, truck/bounty sharing receipts, diagnostic capture, and current Mail/Wanted/training flows. File-level labels are in the manifest; targeted function review does not imply every line was independently verified.

- Diagnostic screen capture is now explicit opt-in rather than automatic for metadata checks. Four mocked tests and a live unchanged-before.png timestamp check support this behavior.
- World truck/bounty share PNGs are opt-in; exact own-sender/room/tile metadata receipts and pending/verified ledgers remain unchanged. Attack screenshots remain enabled under the existing policy.
- Wanted and finished-troop collection defer instrumentation until native inspection/input is required. Every requested native send requires a compatible initial session; a caught compatibility failure cannot enable subsequent sends. UID, process/focus, one-controller and unresolved-operation barriers remain.
- Mail coverage and allowlisted header-state diagnostics use memory reads without injection, native actions or completion writes. They do not read subjects/bodies/attachments and do not claim full mailbox coverage.
- Geometry preview failures are reported as blocked, not successful inspections. Unknown windows, unloaded caches, changed identities and clipped task controls stop the workflow.

These reduce unnecessary access and retention. They do not establish invisibility or a numerical decrease in enforcement likelihood. Installed status and evidence are authoritative in CURRENT_HANDOFF.md.

## Work still required

1. Review the124 pattern-only entries by subsystem, prioritizing legacy Python controller/capture paths, Go scanner and remote-phone/launcher scripts. Record reviewed functions, concrete findings and exclusions rather than promoting files merely because a keyword search ran.
2. Review retained data schemas and opt-in capture lifecycle. Preserve deduplication/uncertain-operation evidence; do not automatically delete prior user data or images.
3. Review runtime asset preparation and capability disclosure, then batch bounded UI getters where identity/freshness checks can remain intact.
4. Review memory discovery/read bounds and performance instrumentation without expanding raw dumps or retaining unrelated player/chat data.
5. Investigate publisher-supported interfaces or permissions before expanding unsupported actions. OS input support alone does not establish publisher approval.

Detailed prioritized tasks and source references: BOT_DETECTION_IMPROVEMENTS.md. Per-function exposure matrix: BOT_DETECTION_RISK_ANALYSIS.md. No concealment, detector bypass, human-mimic timing, or anti-cheat evasion is proposed by this audit.


## Legacy transport/observability and remote-session review

Focused function review completed for bot/android.py (device discovery, command transport, screenshot/cache/input and recovery), bot/observability.py (trace capture and external log handlers), LastZRemotePhone/mac_lease.py and Open-RemotePhone.ps1 (session ownership/heartbeat/restore). These labels do not imply a complete line-by-line audit of all functions or dependencies.

| Finding | Evidence | Improvement/status |
|---|---|---|
| Device recovery may silently change the controlled phone. | android.py:get_device_id falls back after model mismatch; AndroidMixin._recover_adb_device assigns a rediscovered different serial. | High-priority migration constraint: require explicit serial/account ownership, stop on identity change. Do not port this fallback into the helper. Legacy behavior unchanged pending a separately tested transport change. |
| Legacy raw input lacks the helper's same shared lease and account/window guard at this boundary. | AndroidMixin.adb_tap/swipe/keyevent call adb_command directly; command transport logs failures instead of throwing them. | Require a shared device-side controller lease before interoperating. Do not run Python/Go and helper simultaneously. Existing helper guards remain intact. |
| Saved trace screenshots defaulted on despite a comment describing default-off. | main_scrcpy.py CONFIG and ObservabilityMixin._init_observability. | Changed both defaults to false; explicit --trace still enables capture. In-memory screen capture required by vision is unchanged; old images preserved. Source-only desktop change, no bot restart. Three changed Python files AST-parse successfully. |
| External logs may retain arbitrary formatted messages and block or accumulate work. | DiscordWebhookHandler.emit performs synchronous delivery; AxiomLogHandler.emit creates one daemon thread per record, while _send serializes on a lock. | Future bounded queue/drop accounting and field/redaction allowlist. Existing failure cutoff is not a bound on pending threads. No network request or configuration change performed during audit. |
| Local and remote leases protect different controllers. | mac_lease.py flock owns a LaunchAgent pause; Open-RemotePhone.ps1 uses Windows mutex and heartbeat SSH; helper owns separate control.lock on Android. | Existing30second heartbeat recovery restores prior loaded service; it does not prove Androidhelper stopped. Unify lease scope or require explicit helper-idle evidence before legacy resume. No service/session started in this audit. |
| Random tap offset has no established detector-protection evidence. | android.py:AndroidMixin.adb_tap docstring claimed exact-coordinate detection protection. | Corrected documentation; no timing/jitter behavior changed or expanded. Live validated geometry remains the migration target. |

Remote tunneling uses loopback endpoints, SSH keepalives, explicit device and an owned watchdog; finally restores previous environment. Remaining areas include remote host identity policy, installed service definitions and cross-process cancellation under failures. Do not treat these source observations as proof of secure deployment or anti-cheat approval.


## Go scanner transport, startup, evidence and sharing review

Focused function review: tools/truck-scanner/phone.go, main.go, scanner.go (frame/evidence/state persistence), share.go (World sharing). No Go controller was started and no chat/attack/tap was sent during this audit.

- connect() requires exactlyone authorizedlocalUSBdevice afterfiltering andhonors anexplicitserial. Subsequentcommands remain pinnedtoPhone.Serial. Unlike oldPythonrecovery, thistransport doesnotautomaticallyrebind. CommandContext boundscommands15seconds andsignalcontextcancels waits.
- Optional --capture isno-tap, but normal scan/share writesPNG evidence too. evidence() createsfiles inper-rundirectory; noaggregate retentionpolicy. Receipts arevision/OCR comparisons, nothelpermetadataacknowledgments. Do not removePNG writes blindly withoutunderstandingdiagnostic/receiptneeds.
- Inputmethods areADBinputtap/swipe withoutsharedhelpercontrol.lock orperactionUIDguard. Startupuniquedeviceisnotuniqueaccount/controllerownership. Do not runGo andAndroidhelper concurrently.
- Default max-refreshes=-1 searcheswithoutafixedrefreshcap, boundedonlybycontext/stop/foundcriteria. Exposeexplicitoperatorbudget whenmigrating; do notinferunlimitedautorunauthorizationfromnewhelpermaintenancebuttons.
- Go World-sharing rules/logmessages differfromcurrentAndroidhelpergroup/attackmodes. Thesearelegacyindependentworkflows; donotportorchangehelperpolicyfromGoconfigsilently. PreserveinitialnativeShare andexactdestinations inhelper.
- saveJSON usesowneddirectory/tempfile/fsync/rename forstatepersistence. Thisreducespartialwriteexposure butdoesnotreplacecrossprocessownership orserverreceiptproof.

Remaining Go audit: chat navigation/receipt matching, OCR subprocess/tempdata, visualcalibration andhostalerts. Existingfocusedlabels recordreviewedsurfaces/functions, notcompletemodulecorrectness. No detectorlikelihood inferred.


## Additional Go receipt/OCR/alert review

Focusedfunctionreviewadded chat.go,ocr.go,alert_windows.go. OCR sendscroppedPNG via stdin/stdout tobounded15second subprocess withouttempimagefiles inthispath. MultipleOCRstrategies/limits improveconsistencybutarenotmetadataidentityproof. WindowsalertonlycallsMessageBeep3times; no network/capture/action.

Go findWorldCard verifiesWorldtab/power/state/fragmentcount butdoesnotjoinexactownsender/postUUID/serveracklikeAndroidWorldReceipt. Anothermatchingcardcouldsatisfythatvisualshape; donotpromotethislegacyreceipttohelperproof. Chatnavigationstillusesconfiguredpoint/fixedROIs andsavesfullWorldchatreceiptPNG. Keepcurrentmetadata-basedhelperreceiptandlivegeometry, neverportthosefixedpositionsorbroaderretention.

NoGo runtime/chatmessageswereexecuted. RemainingfirstpartyGo review includesvisualcalibration/visionmodule,nonWindowsalerts andtests; testsarenotproofliveaccountownership.

## Legacy log payload minimization implemented

adb_command logsallowlistedoperation/toolcategoriesonly, notserial/path/fullarguments. Rawstderrandexceptiontextareomitted (length/typeonly); transportrecoveryusesconstantreasoncode. Executionstillreceivesunchangedarguments andreturnsoriginalresulttocaller. Fivemockedtestsverifytypedmessage/path/serial/stderr/exceptionpayloadsdonotreachthisboundarylogs. Thisdoesnotredacteveryotherlegacycaller or externalhandler; followupsremain.

Legacy startup nowrequires explicitauthorizedserialoroneuniquemodelmatch; noarbitraryavailabledevicefallback. Recoveryprobesonlyselectedserial. Ninecombinedmockfixturespass. Sharedcontrollerlease/accountguardstillmissinginlegacyinputboundary; neverrunconcurrentlywithhelper.


## Helper preparation ownership follow-up

JobRunner.prepare previously rewrote input-agent-v06.js before its child acquired control.lock. Source now extracts/uses immutable SHA256-named agent files, verifiesexistingcontent andfailsclosedonmismatch. Olderfilesarenotdeleted. Runtimeassettests/fullhelpervalidationpass; seehandofffordeployment. Remainingpreparationraces(ledgerfirstcreation, sharedSTOPcoordination), assetretention andcrosslegacyownershiparenotsolvedbycontentaddressing. No broaderexclusivityclaim.
