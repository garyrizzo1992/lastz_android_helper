package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Receipt persistence only. This engine has no activation or cancellation capability. */
final class BoomerReceiptRecovery {
 static final String ID="boomer_auto_join";
 interface World {void active()throws Exception;long now();JSONObject read()throws Exception;}
 static int inspect(MaintenanceStore store,String uid,boolean preview,World world)throws Exception{
  MaintenanceSchedule.uid(uid);world.active();if(!store.unresolved(uid,ID))return 0;
  JSONObject after=world.read();long now=world.now(),observed=after.getLong("observedMs");
  if(!uid.equals(after.getString("accountUid"))||observed<=0||observed>now||now-observed>15000)throw new IOException("Auto Team-Up recovery identity or observation changed");
  int resolved=0;JSONObject operations=store.account(uid).getJSONObject("operations");Iterator<String> keys=operations.keys();
  while(keys.hasNext()){
   String key=keys.next();JSONObject op=operations.getJSONObject(key);
   if(!ID.equals(op.optString("feature"))||!"activate".equals(op.optString("target"))||!("pending".equals(op.optString("status"))||"uncertain".equals(op.optString("status"))))continue;
   boolean proof=false;try{proof=BoomerReconciliationPolicy.receipt(op.getJSONObject("before"),after);}catch(JSONException missing){/* Legacy incomplete attempts remain fenced. */}
   if(proof){if(!preview)store.verifiedResult(uid,key,ID,now,new JSONObject(after.toString()).put("reconciledReadOnly",true),new MaintenanceResult(MaintenanceResult.Outcome.NOTHING_TO_DO,"Interrupted Auto Team-Up activation verified read-only; existing expiry retained",after.getLong("expiryMs"),Collections.singletonMap("snapshot",after.toString())));resolved++;}
  }
  return resolved;
 }
}
