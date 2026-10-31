package dev.codex.lastzhelper;
import org.json.*;
public final class BoomerReconciliationTests {
 static int checks;static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 static JSONObject clone(JSONObject value)throws Exception{return new JSONObject(value.toString());}
 static final class FaultStore extends MaintenanceStore {
  boolean fail;int saves;FaultStore(java.io.File file)throws Exception{super(file);}
  void save()throws Exception{saves++;if(fail)throw new java.io.IOException("Injected atomic save failure");super.save();}
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
  java.io.File file=java.nio.file.Files.createTempDirectory("boomer-recovery-").resolve("state.json").toFile();
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
  java.io.File faultFile=java.nio.file.Files.createTempDirectory("boomer-recovery-fault-").resolve("state.json").toFile();FaultStore fault=new FaultStore(faultFile);
  fault.begin(uid,id,"initial","activate",now,before);fault.record(uid,id,MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"interrupted",0),now);
  disk=StateProbe.text(faultFile.getPath());fault.fail=true;rejected=false;
  try{BoomerReceiptRecovery.inspect(fault,uid,false,world);}catch(java.io.IOException expected){rejected=true;}
  expect(rejected&&StateProbe.text(faultFile.getPath()).equals(disk),"Failed replacement preserves durable pending receipt and UNCERTAIN status");
  fault=new FaultStore(faultFile);expect(fault.unresolved(uid,id),"Restart after save failure remains fenced");
  expect(BoomerReceiptRecovery.inspect(fault,uid,false,world)==1&&fault.saves==1,"Receipt and schedule use one atomic save");
  reloaded=new MaintenanceStore(faultFile);expect(!reloaded.unresolved(uid,id)&&reloaded.feature(uid,id).getString("lastOutcome").equals("NOTHING_TO_DO")&&reloaded.feature(uid,id).getLong("nextDueMs")==expiry,"Restart sees both receipt and recovered expiry together");
  System.out.println("Auto Boomer reconciliation: "+checks+" checks passed; no replay/input");
 }
}
