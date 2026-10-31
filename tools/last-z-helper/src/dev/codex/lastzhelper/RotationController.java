package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.*;import java.util.regex.*;import org.json.*;
/** One ownership lease across visits, waits, retries and controlled game recovery. */
public final class RotationController {
 final File dir,stop,injector,agent,checkpoint;final String cache,ownerStart,generation;final int owner;final boolean preview;final RunRequest request;
 RecoveryState recovery;String lastUid="",stage="preparing",feature="";int completedFeatures,deferredFeatures;
 RotationController(String[] args)throws Exception{dir=new File(args[1]);injector=new File(args[2]);agent=new File(args[3]);stop=new File(args[4]);JSONObject o=new JSONObject(args[5]);preview=o.optBoolean("dryRun",true);generation=o.optString("runGeneration");owner=Integer.parseInt(args[6]);ownerStart=owner>0?StateProbe.start(""+owner):null;cache=new File(dir,"probe-cache.txt").getPath();checkpoint=new File(dir,"rotation-progress.json");request=new RunRequest(dir);StateProbe.stopSignal=stop;}
 void active()throws Exception{StateProbe.cancelCheck();if(!generation.isEmpty()&&!request.active(generation,stop))throw new InterruptedException("Run cancelled or device restarted");if(owner>0&&(!ownerStart.equals(StateProbe.start(""+owner))||!"dev.codex.lastzhelper".equals(StateProbe.cmdline(""+owner))))throw new InterruptedException("Helper ended; rotation stopped");}
 void event(String state,String message,String uid)throws Exception{active();stage=state;if(!uid.isEmpty())lastUid=uid;else if(lastUid.isEmpty()&&StateProbe.pinnedUid!=null)lastUid=StateProbe.pinnedUid;JSONObject o=new JSONObject().put("event","rotation-progress").put("stage",state).put("message",message).put("accountUid",uid).put("lastAccountUid",lastUid).put("feature",feature).put("generation",generation).put("timestampMs",System.currentTimeMillis()).put("dryRun",preview).put("running",true).put("completedChecks",completedFeatures);
  if(StateProbe.pinnedPid!=null)o.put("gamePid",StateProbe.pinnedPid).put("gameStart",StateProbe.pinnedStart);RotationFiles.write(checkpoint,o);System.out.println(o);System.out.flush();}
 void pause(long ms,boolean verifyFocus)throws Exception{long end=android.os.SystemClock.elapsedRealtime()+ms;while(android.os.SystemClock.elapsedRealtime()<end){active();if(verifyFocus&&StateProbe.pinnedUid!=null){if(DeviceInput.active==null&&RecoveryGuard.gone(StateProbe.pinnedPid,StateProbe.pinnedStart)&&RecoveryGuard.home()){StateProbe.releaseRotationIdentity();event("waiting","Game exited while idle; it will reopen when work is due","");}else StateProbe.verifyPinned();}Thread.sleep(Math.min(500,Math.max(1,end-android.os.SystemClock.elapsedRealtime())));}}
 static int cloneInMaps(String maps)throws Exception{Set<Integer> found=new HashSet<>();Matcher m=Pattern.compile("/parallel_intl/([0-9]+)/com\\.readygo\\.barrel\\.gp/").matcher(maps);while(m.find())found.add(Integer.parseInt(m.group(1)));if(found.size()!=1)throw new IOException("Cannot prove one Parallel Space game identity from its process");return found.iterator().next();}
 void routeProof(RotationShortcut route)throws Exception{if(StateProbe.pinnedPid==null||cloneInMaps(StateProbe.text("/proc/"+StateProbe.pinnedPid+"/maps"))!=route.clone)throw new IOException("Opened game does not match selected shortcut");}
 JSONObject open(RotationShortcut route,String expected,List<RotationShortcut> registered)throws Exception{
  active();boolean exists=false;for(RotationShortcut s:registered)if(s.same(route))exists=true;if(!exists)throw new IOException("Saved game shortcut changed; set up games again");
  if(StateProbe.pinnedUid!=null)StateProbe.verifyPinned();StateProbe.releaseRotationIdentity();event("opening","Opening "+route.id,expected==null?"":expected);
  String launch=DeviceInput.exec(15,route.launch());if(launch.contains("Error:")||launch.contains("Exception"))throw new IOException("Game launch failed: "+launch);
  long until=android.os.SystemClock.elapsedRealtime()+120000;String last="Waiting for game";
  while(android.os.SystemClock.elapsedRealtime()<until){active();
   try{StateProbe.pinForeground();routeProof(route);}catch(Exception e){if(e instanceof InterruptedException)throw e;last=e.getMessage();StateProbe.releaseRotationIdentity();pause(1000,false);continue;}
   JSONObject state;try{state=StateProbe.snapshot(cache);}catch(Exception e){if(e instanceof InterruptedException)throw e;last=e.getMessage();StateProbe.releaseRotationIdentity();pause(1500,false);continue;}
   routeProof(route);if(expected!=null&&!expected.equals(state.getString("accountUid")))throw new IOException("Selected game opened a different character; no maintenance input sent");
   if(state.optBoolean("gameStarted")&&(state.getInt("sceneId")==1||state.getInt("sceneId")==2)){StateProbe.verifyPinned();return state;}pause(1000,true);
  }throw new IOException("Game did not become ready: "+route.id+": "+last);
 }
 boolean quarantined(JSONObject p,MaintenanceStore s,String id)throws Exception{return s.unresolved(p.getString("uid"),id)||"UNCERTAIN".equals(s.feature(p.getString("uid"),id).optString("lastOutcome"));}
 long due(JSONObject p,MaintenanceStore s)throws Exception{long earliest=Long.MAX_VALUE;for(String id:RotationPolicy.FEATURES)if(p.getJSONObject("features").getBoolean(id)){if(quarantined(p,s,id)){if(MaintenanceReconciler.supported(id))earliest=Math.min(earliest,recovery.deferred(p.getString("uid"),id));}else earliest=Math.min(earliest,Math.max(s.feature(p.getString("uid"),id).getLong("nextDueMs"),recovery.deferred(p.getString("uid"),id)));}return earliest==Long.MAX_VALUE?earliest:Math.max(earliest,recovery.accountUntil(p.getString("uid")));}
 static final class Reopen extends IOException{final String feature;Reopen(String f,String message){super(message);feature=f;}}
 void step(MaintenanceContext c,JSONObject profile,MaintenanceFeature f,boolean reopened)throws Exception{
  String uid=c.uid;feature=f.id();if(quarantined(profile,c.store,feature)){deferredFeatures++;event("needs-attention","Unresolved "+feature+" is fenced; other tasks remain available",uid);return;}
  long now=System.currentTimeMillis();if(recovery.deferred(uid,feature)>now){deferredFeatures++;event("deferred",feature+" is cooling down until "+recovery.deferred(uid,feature),uid);return;}if(!preview&&!c.store.due(uid,feature,now))return;
  recovery.allowEpisode(uid,feature,now);
  RecoveryEngine.Result result=RecoveryEngine.run(recovery,uid,feature,reopened,new RecoveryEngine.World(){
   public void active()throws Exception{RotationController.this.active();c.active();}public long now(){return System.currentTimeMillis();}public void pause(long ms)throws Exception{RotationController.this.pause(ms,true);}
   public MaintenanceResult execute()throws Exception{return MaintenanceRunner.run(c,Collections.singletonList(f),false,true,true).get(0);}public boolean unresolved()throws Exception{return c.store.unresolved(uid,f.id());}public boolean clear()throws Exception{return RecoveryGuard.clear(cache);}
   public void event(String stage,String message)throws Exception{RotationController.this.event(stage,profile.getString("name")+": "+message,uid);}
  });
  if(result.end==RecoveryEngine.End.COMPLETE){completedFeatures++;return;}
  if(result.end==RecoveryEngine.End.REOPEN)throw new Reopen(feature,result.outcome.reason);
  deferredFeatures++;
  if(result.end==RecoveryEngine.End.QUARANTINED){event("needs-attention",feature+" has an uncertain operation; no replay",uid);return;}
  if(!preview){Map<String,String> proof=new LinkedHashMap<>(result.outcome.evidence);proof.put("lastFailure",result.outcome.reason);c.store.record(uid,feature,new MaintenanceResult(MaintenanceResult.Outcome.WAITING,"Retries exhausted; deferred 15 minutes: "+result.outcome.reason,recovery.deferred(uid,feature),proof),System.currentTimeMillis());}event("deferred",feature+": retry limit reached; other tasks continue",uid);
 }
 void visit(JSONObject p,int minutes)throws Exception{
  String uid=p.getString("uid");int crashes=0;Set<String> reopened=new HashSet<>();long deadline=android.os.SystemClock.elapsedRealtime()+minutes*60000L;
  while(true){
   try{open(RotationShortcut.from(p.getJSONObject("launch")),uid,RotationShortcut.parse(DeviceInput.exec(8,"/system/bin/dumpsys","shortcut")));}catch(Exception e){if(e instanceof InterruptedException)throw e;if(!e.getMessage().startsWith("Game did not become ready:")||!RecoveryGuard.home())throw e;if(crashes++>=1||!recovery.restart(uid,System.currentTimeMillis())){deferredFeatures++;recovery.deferAccount(uid,System.currentTimeMillis());StateProbe.releaseRotationIdentity();event("deferred","Account launch deferred 15 minutes after recovery limit",uid);return;}StateProbe.releaseRotationIdentity();event("restarting","Retrying the same registered game's loading",uid);pause(RecoveryPolicy.delay(0),false);continue;}
   String pid=StateProbe.pinnedPid,start=StateProbe.pinnedStart;
   try(DeviceInput.Scope scope=new DeviceInput.Scope()){
    AutomationController legacy=new AutomationController(dir,injector,agent,stop,preview,owner);legacy.mode="maintenance-rotation";MaintenanceContext c=new MaintenanceContext(legacy);if(!uid.equals(c.uid))throw new IOException("Expected rotation character is not active");DeviceInput.Guard previous=legacy.input.guard;legacy.input.guard=()->{active();if(previous!=null)previous.verify();};
    MaintenanceReconciler.inspect(c,p.getJSONObject("features"));for(String id:RotationPolicy.FEATURES)if(p.getJSONObject("features").getBoolean(id)&&quarantined(p,c.store,id)&&MaintenanceReconciler.supported(id))recovery.defer(uid,id,"Read-only reconciliation remains inconclusive",System.currentTimeMillis());
    do{for(MaintenanceFeature f:MaintenanceRegistry.selected(p.getJSONObject("features")))step(c,p,f,reopened.contains(f.id()));if(preview||android.os.SystemClock.elapsedRealtime()>=deadline||due(p,c.store)>System.currentTimeMillis())break;}while(true);
   }catch(Exception e){
    if(e instanceof InterruptedException)throw e;
    if(e.getSuppressed().length>0&&!RecoveryGuard.gone(pid,start))throw e; // a live game still requires confirmed detach
    boolean commanded=e instanceof Reopen;
    if(commanded){StateProbe.verifyPinned();if(!RecoveryGuard.clear(cache))throw e;}else if(!RecoveryGuard.gone(pid,start)||!RecoveryGuard.home())throw e;
    RecoveryGuard.noInjector();if((!commanded&&crashes++>=1)||!recovery.restart(uid,System.currentTimeMillis())){deferredFeatures++;recovery.deferAccount(uid,System.currentTimeMillis());if(commanded){StateProbe.verifyPinned();}StateProbe.releaseRotationIdentity();event("deferred","Account deferred 15 minutes; game/worker restart limit reached",uid);return;}
    if(commanded){reopened.add(((Reopen)e).feature);routeProof(RotationShortcut.from(p.getJSONObject("launch")));StateProbe.verifyPinned();event("restarting","Restarting this game after bounded navigation retries",uid);DeviceInput.exec(5,"/system/bin/kill","-15",pid);long end=android.os.SystemClock.elapsedRealtime()+5000;while(!RecoveryGuard.gone(pid,start)&&android.os.SystemClock.elapsedRealtime()<end)pause(100,false);if(!RecoveryGuard.gone(pid,start))throw new IOException("Selected game did not exit; no additional restart sent");}
    StateProbe.releaseRotationIdentity();event("restarting","Reopening the same verified account; pending operations remain fenced",uid);pause(RecoveryPolicy.delay(0),false);continue;
   }
   feature="";event("visited","Finished maintenance on "+p.getString("name"),uid);return;
  }
 }
 void run(String mode,JSONObject options)throws Exception{
  recovery=new RecoveryState(new File(dir,preview?"bot-recovery-preview.json":"bot-recovery.json"));
  if(options.optBoolean("restartingWorker")){JSONObject previous=checkpoint.exists()?new JSONObject(StateProbe.text(checkpoint.getPath())):new JSONObject();RecoveryGuard.resume(checkpoint,cache);lastUid=previous.optString("lastAccountUid",StateProbe.pinnedUid==null?"":StateProbe.pinnedUid);feature=previous.optString("feature");event("reconciling","Worker restarted; rechecking history before any action","");}
  List<RotationShortcut> shortcuts=RotationShortcut.parse(DeviceInput.exec(8,"/system/bin/dumpsys","shortcut"));RotationProfiles profiles=options.has("selectedProfiles")?new RotationProfiles(new File(dir,"rotation-profiles.json"),new JSONObject().put("schema",1).put("profiles",options.getJSONArray("selectedProfiles"))):new RotationProfiles(new File(dir,"rotation-profiles.json"));
  if(mode.equals("maintenance-enroll")){for(RotationShortcut route:shortcuts){JSONObject state=open(route,null,shortcuts);profiles.enroll(route,state);event("enrolled",route.id+": "+state.getString("accountName")+" ("+state.getString("accountUid")+")",state.getString("accountUid"));}return;}
  List<JSONObject> selected=profiles.selected();int minutes=RotationPolicy.minutes(options.optInt("visitMinutes",20));MaintenanceStore initial=new MaintenanceStore(new File(dir,"maintenance-state.json"));boolean usable=false;for(JSONObject p:selected){if(due(p,initial)!=Long.MAX_VALUE)usable=true;else{deferredFeatures++;event("needs-attention",p.getString("name")+": selected tasks require reconciliation",p.getString("uid"));}}if(!usable)throw new IOException("Selected features have unresolved operations; reconcile before running");
  do{for(JSONObject p:selected){active();MaintenanceStore store=new MaintenanceStore(new File(dir,"maintenance-state.json"));long next=due(p,store);if(next==Long.MAX_VALUE||(!preview&&next>System.currentTimeMillis()))continue;visit(p,minutes);}
   if(preview)return;
   long earliest=Long.MAX_VALUE;MaintenanceStore after=new MaintenanceStore(new File(dir,"maintenance-state.json"));for(JSONObject p:selected)earliest=Math.min(earliest,due(p,after));if(earliest==Long.MAX_VALUE)throw new IOException("No task can continue until uncertain operations are reconciled");
   if(earliest>System.currentTimeMillis()){event("waiting","Waiting for next maintenance task","");pause(Math.max(1000,Math.min(60000,earliest-System.currentTimeMillis())),true);}
  }while(true);
 }
 static void failed(JSONObject output,Throwable e){try{output.put("event","result").put("ok",false).put("rotation",true).put("stopped",e instanceof InterruptedException).put("error",e.toString());}catch(Exception ignored){}}
 static void finalCheckpoint(RotationController c,JSONObject output)throws Exception{
  if(!c.generation.isEmpty()&&!c.request.matches(c.generation))return;
  JSONObject state=new JSONObject(output.toString()).put("generation",c.generation).put("lastAccountUid",c.lastUid).put("feature",c.feature).put("stage",c.stage).put("running",false).put("timestampMs",System.currentTimeMillis());if(StateProbe.pinnedPid!=null)state.put("gamePid",StateProbe.pinnedPid).put("gameStart",StateProbe.pinnedStart);RotationFiles.write(c.checkpoint,state);
 }
 public static void main(String[] args){JSONObject output=new JSONObject();try{
  if(args.length!=7||!(args[0].equals("maintenance-enroll")||args[0].equals("maintenance-rotation")))throw new IOException("Unsupported rotation mode");final RotationController c=new RotationController(args);JSONObject options=new JSONObject(args[5]);File locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile file=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel channel=file.getChannel()){
   FileLock acquired=ControllerLease.acquire(channel,options.optBoolean("restartingWorker"),c::active);if(acquired==null)throw new IOException("Another controller is active; recovery ownership was not acquired");
   try(FileLock held=acquired){
    try(DeviceInput.Scope scope=new DeviceInput.Scope()){
     ControllerOwnership.check();RecoveryGuard.noInjector();c.active();c.run(args[0],options);
     output.put("event","result").put("ok",true).put("rotation",true).put("needsAttention",c.deferredFeatures>0).put("deferredFeatures",c.deferredFeatures).put("message",args[0].equals("maintenance-enroll")?"Games inspected. Select accounts in Accounts and features.":c.deferredFeatures>0?"Preview finished with deferred tasks needing attention; no claims sent.":"Bot preview completed; no claims sent.");
    }catch(Throwable e){failed(output,e);}
    // Finalize while ownership is STILL held; a successor cannot read stale or
    // concurrently overwritten state after it acquires the released lease.
    try{finalCheckpoint(c,output);}catch(Exception e){failed(output,new IOException("Cannot save final rotation checkpoint",e));}
   }
  }
 }catch(Throwable e){failed(output,e);}System.out.println(output);if(!output.optBoolean("ok"))System.exit(1);
 }
}
