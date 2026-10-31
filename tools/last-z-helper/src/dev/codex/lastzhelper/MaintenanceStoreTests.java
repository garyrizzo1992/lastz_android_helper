package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Android parser/persistence checks on a private temporary fixture; no game access. */
public final class MaintenanceStoreTests {
 static int checks;static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 public static void main(String[] args)throws Exception{
  File folder=new File("/data/local/tmp/lastz-maintenance-test-"+java.util.UUID.randomUUID());if(!folder.mkdir())throw new IOException("Test folder unavailable");File file=new File(folder,"state.json");
  String first="2059765822000064",second="2028198887000064";
  try{
   MaintenanceStore store=new MaintenanceStore(file);expect(!store.enabled(first,"vip"),"features disabled by default");
   store.record(first,"vip",MaintenanceResult.of(MaintenanceResult.Outcome.PREVIEW,"preview",0),100);expect(!file.exists(),"preview does not create durable outcome");
   store.enabled(first,"vip",true);expect(!store.enabled(second,"vip"),"preferences isolated by UID");
   String key=store.begin(first,"vip","2026-10-29","daily_points",100,new JSONObject().put("claimed",false));
   expect(store.unresolved(first,"vip")&&!store.unresolved(second,"vip"),"pending isolated by UID");
   MaintenanceStore reloaded=new MaintenanceStore(file);expect(reloaded.unresolved(first,"vip")&&!reloaded.due(first,"vip",200),"pending survives restart and blocks due");
   boolean otherRejected=false;try{reloaded.begin(first,"vip","other_revision","daily_freebies",200,new JSONObject());}catch(IOException e){otherRejected=true;}expect(otherRejected,"new revision/target cannot bypass unresolved feature commit");
   boolean rejected=false;try{reloaded.begin(first,"vip","2026-10-29","daily_points",200,new JSONObject());}catch(IOException e){rejected=true;}expect(rejected,"duplicate commit rejected");
   reloaded.uncertain(first,key,"receipt missing");expect(new MaintenanceStore(file).operation(first,key).getString("status").equals("uncertain"),"uncertain persists");
   reloaded.verified(first,key,300,new JSONObject().put("claimed",true));expect(!reloaded.unresolved(first,"vip"),"reconciliation resolves operation");
   expect(reloaded.latestVerified(first,"vip","daily_points").getLong("verifiedMs")==300&&reloaded.latestVerified(first,"vip","daily_freebies")==null,"latest verified evidence selected by category");
   reloaded.record(first,"vip",MaintenanceResult.of(MaintenanceResult.Outcome.COMPLETED,"both claims confirmed",1000),300);
   expect(!reloaded.due(first,"vip",999)&&reloaded.due(first,"vip",1000),"persisted next due respected");
   reloaded.record(second,"vip",MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"missing field",1000),400);expect(reloaded.feature(second,"vip").getInt("failures")==1&&reloaded.feature(first,"vip").getInt("failures")==0,"failure counts isolated");
   expect(reloaded.feature(first,"vip").getLong("lastSuccessMs")==300,"success evidence retained");
   expect(reloaded.begin(second,"vip","2026-10-29","daily_points",500,new JSONObject()).equals(key),"same operation identity allowed for different UID");
   String blocked=reloaded.begin(first,"eight_hour_chest","since_123","collect_full",600,new JSONObject());
   JSONObject noInput=new JSONObject().put("receipt",new JSONObject().put("ok",false).put("inputDispatched",false).put("phase","native_pre_dispatch").put("requestAction","ui-tap")).put("gameTimestampUnchanged",true);
   boolean invalid=false;try{reloaded.cancelBeforeInput(first,blocked,new JSONObject());}catch(IOException e){invalid=true;}expect(invalid&&reloaded.unresolved(first,"eight_hour_chest"),"missing receipt cannot cancel uncertain operation");
   JSONObject dispatched=new JSONObject(noInput.toString());dispatched.getJSONObject("receipt").put("inputDispatched",true);invalid=false;try{reloaded.cancelBeforeInput(first,blocked,dispatched);}catch(IOException e){invalid=true;}expect(invalid,"dispatched input cannot be cancelled");
   reloaded.cancelBeforeInput(first,blocked,noInput);reloaded=new MaintenanceStore(file);expect(!reloaded.unresolved(first,"eight_hour_chest")&&reloaded.operation(first,blocked).getString("status").equals("cancelled_before_input"),"proven cancellation persists and preserves attempt");
   String retried=reloaded.begin(first,"eight_hour_chest","since_123","collect_full",700,new JSONObject());expect(!retried.equals(blocked)&&reloaded.operation(first,blocked).getString("status").equals("cancelled_before_input"),"retry has separate key and retains cancelled evidence");
   reloaded.verified(first,retried,800,new JSONObject());invalid=false;try{reloaded.begin(first,"eight_hour_chest","since_123","collect_full",900,new JSONObject());}catch(IOException e){invalid=true;}expect(invalid,"verified retry prevents another same-period claim");
   ShareLedger.atomic(file,new JSONObject().put("schema",2).put("accounts",new JSONObject()));rejected=false;try{new MaintenanceStore(file);}catch(IOException e){rejected=true;}expect(rejected,"unknown schema rejected");
   System.out.println("Passed "+checks+" Android maintenance store checks");
  }finally{new File(file.getPath()+".tmp").delete();file.delete();folder.delete();}
 }
}
