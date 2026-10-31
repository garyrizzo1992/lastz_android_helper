package dev.codex.lastzhelper;
import org.json.*;
public final class BoomerReconciliationTests {
 static int checks;static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 static JSONObject clone(JSONObject value)throws Exception{return new JSONObject(value.toString());}
 static final class FaultStore extends MaintenanceStore {
  boolean fail;int saves;FaultStore(java.io.File file)throws Exception{super(file);}
  void save()throws Exception{saves++;if(fail)throw new java.io.IOException("Injected atomic save failure");super.save();}
 }
 static final class Navigation implements BoomerReceiptRecovery.Navigation {
  final JSONObject receipt;final String fault;boolean scoped,stopped;int opens,closes,leaves,reads;
  Navigation(JSONObject receipt,String fault){this.receipt=receipt;this.fault=fault;}
  public long now(){return 1001000;}
  public void active()throws Exception{if(stopped)throw new InterruptedException("STOP");}
  public void enter()throws Exception{if(fault.equals("overlap"))throw new java.io.IOException("Existing scope");scoped=true;}
  public void leave(){scoped=false;leaves++;}
  public void open()throws Exception{expect(scoped,"Navigation owns restricted scope");opens++;if(fault.equals("stop")){stopped=true;throw new InterruptedException("STOP opening");}if(fault.equals("open"))throw new java.io.IOException("Open failure");}
  public JSONObject read()throws Exception{expect(scoped,"Receipt read owns restricted scope");reads++;if(fault.equals("read-close"))throw new java.io.IOException("Read failure");if(fault.equals("late-stop"))stopped=true;return receipt;}
  public void close()throws Exception{expect(scoped,"Cleanup retains restricted scope");closes++;if(fault.equals("close")||fault.equals("read-close"))throw new java.io.IOException("Close failure");}
 }
 public static void main(String[]args)throws Exception{
  long now=1000000,expiry=now+BoomerPolicy.DURATION;
  JSONArray options=new JSONArray().put(new JSONObject().put("type",1).put("selected",true)).put(new JSONObject().put("type",2).put("selected",false));
  JSONObject before=new JSONObject().put("activationRequestedMs",now).put("observedMs",now-1000).put("expiryMs",0).put("timerSeconds",-2).put("state","INACTIVE").put("activityId","40005").put("accountUid","2059765822000064").put("options",options);
  JSONObject after=clone(before).put("expiryMs",expiry).put("observedMs",now+1000).put("timerSeconds",43199).put("state","ACTIVE");
  expect(BoomerReconciliationPolicy.receipt(before,after),"Exact activation receipt");
  expect(BoomerReconciliationPolicy.receipt(before,clone(after).put("observedMs",now+60000).put("timerSeconds",43140)),"Delayed read-only recovery uses original activation window");
  for(String field:new String[]{"accountUid","activityId","state"})expect(!BoomerReconciliationPolicy.receipt(before,clone(after).put(field,"other")),"Different "+field+" cannot reconcile");
  expect(!BoomerReconciliationPolicy.receipt(before,clone(after).put("expiryMs",expiry+60000)),"Later manual renewal not original receipt");
  expect(!BoomerReconciliationPolicy.receipt(before,clone(after).put("expiryMs",0)),"Disabled after attempt is uncertain, not retry permission");
  expect(!BoomerReconciliationPolicy.receipt(before,clone(after).put("timerSeconds",1)),"Timer must match expiry");
  expect(!BoomerReconciliationPolicy.receipt(before,clone(after).put("observedMs",expiry).put("timerSeconds",0)),"Expired state cannot reconcile");
  expect(!BoomerReconciliationPolicy.receipt(clone(before).put("observedMs",now+1),after),"Future before snapshot rejected");
  expect(!BoomerReconciliationPolicy.receipt(clone(before).put("observedMs",now-20000),after),"Stale before snapshot rejected");
  expect(!BoomerReconciliationPolicy.receipt(clone(before).put("expiryMs",now+1000),after),"Already active before is not activation");
  expect(!BoomerReconciliationPolicy.receipt(clone(before).put("timerSeconds",0),after),"Zero timer is not observed disabled label");
  expect(!BoomerReconciliationPolicy.receipt(clone(before).put("activationRequestedMs",Long.MAX_VALUE-10),after),"Overflow rejected");
  for(int i=0;i<2;i++){JSONObject changed=clone(after);changed.getJSONArray("options").getJSONObject(i).put("selected",!options.getJSONObject(i).getBoolean("selected"));expect(!BoomerReconciliationPolicy.receipt(before,changed),"Changed join option rejected");}
  JSONObject changed=clone(after);changed.getJSONArray("options").getJSONObject(0).put("type",2);expect(!BoomerReconciliationPolicy.receipt(before,changed),"Duplicate option identity rejected");
  changed=clone(after);changed.getJSONArray("options").getJSONObject(0).put("selected","true");expect(!BoomerReconciliationPolicy.receipt(before,changed),"String cannot replace boolean");
  JSONObject disabled=clone(before);disabled.getJSONArray("options").getJSONObject(0).put("selected",false);changed=clone(after);changed.put("options",disabled.getJSONArray("options"));expect(!BoomerReconciliationPolicy.receipt(disabled,changed),"No selected joins is not activation success");
  expect(!BoomerReconciliationPolicy.receipt(before,clone(after).put("options",new JSONArray())),"Unloaded options cannot reconcile");
  String uid=before.getString("accountUid"),id=BoomerReceiptRecovery.ID;
  java.nio.file.Path root=args.length==0?java.nio.file.Files.createTempDirectory("boomer-recovery-"):java.nio.file.Files.createTempDirectory(java.nio.file.Paths.get(args[0]),"receipt-");
  java.io.File file=root.resolve("state.json").toFile();
  MaintenanceStore store=new MaintenanceStore(file);String key=store.begin(uid,id,"initial","activate",now,before);
  final JSONObject receipt=after;
  BoomerReceiptRecovery.World world=new BoomerReceiptRecovery.World(){public void active(){}public long now(){return 1001000;}public JSONObject read(){return receipt;}};
  String disk=StateProbe.text(file.getPath());
  expect(BoomerReceiptRecovery.inspect(store,uid,true,world)==1,"Preview finds exact proof");
  expect(StateProbe.text(file.getPath()).equals(disk)&&store.unresolved(uid,id),"Preview preserves disk and in-memory barrier");
  receipt.put("expiryMs",expiry+60000);expect(BoomerReceiptRecovery.inspect(store,uid,false,world)==0&&store.unresolved(uid,id),"Manual renewal remains fenced");receipt.put("expiryMs",expiry);
  receipt.put("observedMs",now-20000);boolean rejected=false;try{BoomerReceiptRecovery.inspect(store,uid,false,world);}catch(java.io.IOException expected){rejected=true;}expect(rejected&&store.unresolved(uid,id),"Stale recovery snapshot rejected");receipt.put("observedMs",now+1000);
  BoomerReceiptRecovery.World stopped=new BoomerReceiptRecovery.World(){public void active()throws Exception{throw new InterruptedException("STOP");}public long now(){return 0;}public JSONObject read(){throw new AssertionError("read after STOP");}};
  rejected=false;try{BoomerReceiptRecovery.inspect(store,uid,false,stopped);}catch(InterruptedException expected){rejected=true;}expect(rejected&&StateProbe.text(file.getPath()).equals(disk),"STOP before recovery preserves attempt");
  expect(BoomerReceiptRecovery.inspect(store,uid,false,world)==1,"Exact recovery records proof");
  MaintenanceStore reloaded=new MaintenanceStore(file);expect(!reloaded.unresolved(uid,id)&&reloaded.operation(uid,key).getJSONObject("after").getBoolean("reconciledReadOnly"),"Durable receipt clears barrier");
  expect(reloaded.feature(uid,id).getLong("nextDueMs")==expiry,"Recovery retains actual expiry");
  disk=StateProbe.text(file.getPath());expect(BoomerReceiptRecovery.inspect(reloaded,uid,false,world)==0&&StateProbe.text(file.getPath()).equals(disk),"Repeated recovery performs no write");
  java.io.File faultFile=root.resolve("fault-state.json").toFile();FaultStore fault=new FaultStore(faultFile);
  fault.begin(uid,id,"initial","activate",now,before);fault.record(uid,id,MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"interrupted",0),now);
  disk=StateProbe.text(faultFile.getPath());fault.fail=true;rejected=false;
  try{BoomerReceiptRecovery.inspect(fault,uid,false,world);}catch(java.io.IOException expected){rejected=true;}
  expect(rejected&&StateProbe.text(faultFile.getPath()).equals(disk),"Failed replacement preserves durable pending receipt and UNCERTAIN status");
  fault=new FaultStore(faultFile);expect(fault.unresolved(uid,id),"Restart after save failure remains fenced");
  expect(BoomerReceiptRecovery.inspect(fault,uid,false,world)==1&&fault.saves==1,"Receipt and schedule use one atomic save");
  reloaded=new MaintenanceStore(faultFile);expect(!reloaded.unresolved(uid,id)&&reloaded.feature(uid,id).getString("lastOutcome").equals("NOTHING_TO_DO")&&reloaded.feature(uid,id).getLong("nextDueMs")==expiry,"Restart sees both receipt and recovered expiry together");
  MaintenanceStore isolated=new MaintenanceStore(root.resolve("isolation.json").toFile());
  String other="2059770776000064";JSONObject otherBefore=clone(before).put("accountUid",other);
  isolated.begin(other,id,"initial","activate",now,otherBefore);String otherState=isolated.account(other).toString();
  String first=isolated.begin(uid,id,"initial","activate",now,before);
  // A legacy/imported ledger can contain multiple unresolved records even though
  // current begin() forbids creating them. Preserve every unmatched barrier.
  JSONObject legacy=clone(isolated.operation(uid,first));legacy.getJSONObject("before").remove("activationRequestedMs");
  isolated.account(uid).getJSONObject("operations").put("legacy_incomplete",legacy);
  isolated.record(uid,id,MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"two interrupted records",0),now);
  expect(BoomerReceiptRecovery.inspect(isolated,uid,false,world)==1,"Exact partial receipt can be saved beside incomplete legacy record");
  isolated=new MaintenanceStore(isolated.file);
  expect(isolated.operation(uid,first).getString("status").equals("verified")&&isolated.unresolved(uid,id),"Partial recovery preserves remaining barrier durably");
  expect(isolated.feature(uid,id).getString("lastOutcome").equals("UNCERTAIN"),"Partial proof cannot clear feature quarantine");
  expect(isolated.account(other).toString().equals(otherState),"Other account receipt and choices unchanged");
  disk=StateProbe.text(isolated.file.getPath());
  expect(BoomerReceiptRecovery.inspect(isolated,uid,false,world)==0&&StateProbe.text(isolated.file.getPath()).equals(disk),"Incomplete legacy repeat cannot write or consume");
  for(String scenario:new String[]{"success","open","read-close","close","stop","late-stop","overlap"}){
   MaintenanceStore ledger=new MaintenanceStore(root.resolve("navigation-"+scenario+".json").toFile());ledger.begin(uid,id,"initial","activate",now,before);
   Navigation navigation=new Navigation(receipt,scenario);Exception failure=null;int result=-1;
   try{result=BoomerReceiptRecovery.navigate(ledger,uid,false,navigation);}catch(Exception expected){failure=expected;}
   expect(!navigation.scoped,"Scope restored after "+scenario);
   if(scenario.equals("overlap")){expect(navigation.leaves==0&&navigation.opens==0,"Existing scope is never replaced or cleared");continue;}
   expect(navigation.leaves==1,"Scope released exactly once: "+scenario);
   if(scenario.equals("success"))expect(result==1&&navigation.closes==1,"Success only follows cleanup");
   else expect(failure!=null,"Failure cannot report success: "+scenario);
   if(scenario.equals("read-close"))expect(failure.getMessage().equals("Read failure")&&failure.getSuppressed().length==1,"Cleanup preserves original read failure and secondary evidence");
   if(scenario.equals("stop")||scenario.equals("late-stop"))expect(failure instanceof InterruptedException&&navigation.closes==0,"STOP prevents cleanup input");
   boolean persisted=scenario.equals("success")||scenario.equals("close")||scenario.equals("late-stop");
   expect(new MaintenanceStore(ledger.file).unresolved(uid,id)!=persisted,"Only conclusive proof survives interruption: "+scenario);
  }
  System.out.println("Auto Boomer reconciliation: "+checks+" checks passed; no replay/input");
 }
}
