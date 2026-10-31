package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Existing receipts use getters; Boomer uses a separate navigation-only scope. */
final class MaintenanceReconciler {
 static boolean supported(String f){return f.equals("training_collection")||f.equals("wanted_finished_reward")||f.equals(BoomerReceiptRecovery.ID);}
 static int inspect(MaintenanceContext c,JSONObject flags)throws Exception{
  int resolved=0;
  // Missing flag is deliberately false until production enrollment. Explicit
  // opt-outs also prohibit recovery navigation for this feature.
  if(flags.optBoolean(BoomerReceiptRecovery.ID,false))resolved+=BoomerRecoveryNavigation.inspect(c);
  JSONObject operations=c.store.account(c.uid).getJSONObject("operations");Iterator<String> keys=operations.keys();
  while(keys.hasNext()){
   String key=keys.next();JSONObject op=operations.getJSONObject(key);String feature=op.getString("feature"),status=op.getString("status");if(!supported(feature)||!flags.optBoolean(feature,false)||status.equals("verified")||status.equals("cancelled_before_input"))continue;
   if(feature.equals(BoomerReceiptRecovery.ID))continue;
   JSONObject before=op.getJSONObject("before"),after=null;
   try(GameMemory m=new GameMemory(c.controller.cache)){
    c.active();if(!c.uid.equals(m.state.getString("accountUid")))throw new java.io.IOException("Reconciliation account changed");
    if(feature.equals("wanted_finished_reward")){
     String uuid=before.getString("uuid");long task=m.path("DataCenter/ActDispatchTaskDataManager/singleTask/#"+uuid);after=new JSONObject().put("uuid",Long.toString(GameMemory.number(task,"uuid"))).put("configId",GameMemory.number(task,"cfgId")).put("startTime",GameMemory.number(task,"startTime")).put("completionTime",GameMemory.number(task,"completionTime")).put("rewarded",GameMemory.number(task,"rewarded"));if(!ReconciliationPolicy.wanted(before,after))after=null;
    }else{
     String queueId=before.getString("queueId"),unit=before.getString("unitId");long queue=m.path("DataCenter/QueueDataManager/queueDic/#"+queueId),army=m.path("DataCenter/ArmyManager/allArmy/"+unit);if(!unit.equals(GameMemory.string(army,"id")))continue;
     after=new JSONObject().put("queueId",Long.toString(GameMemory.number(queue,"uuid"))).put("unitId",unit).put("buildingUid",Long.toString(GameMemory.number(queue,"funcUuid"))).put("queueState",GameMemory.number(queue,"state")).put("freeUnits",GameMemory.number(army,"free")).put("trainingUnits",GameMemory.number(army,"train"));if(!ReconciliationPolicy.training(before,after))after=null;
    }
   }catch(org.json.JSONException|java.io.IOException e){c.active();continue;}
   if(after!=null){after.put("reconciledReadOnly",true);if(!c.preview){c.store.verified(c.uid,key,System.currentTimeMillis(),after);if(!c.store.unresolved(c.uid,feature))c.store.record(c.uid,feature,new MaintenanceResult(MaintenanceResult.Outcome.WAITING,"Interrupted operation verified read-only; inspecting remaining work next",System.currentTimeMillis(),Collections.singletonMap("receipt",after.toString())),System.currentTimeMillis());}c.event(feature,c.preview?"Read-only recovery proof available; preview left history unchanged":"Interrupted operation verified read-only; no input repeated");resolved++;}
  }return resolved;
 }
}
