package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Independent per-UID maintenance state. Existing game/share ledgers are untouched. */
final class MaintenanceStore {
 final File file;final JSONObject data;
 MaintenanceStore(File file)throws Exception{
  this.file=file;data=file.exists()?new JSONObject(StateProbe.text(file.getPath())):new JSONObject().put("schema",1).put("accounts",new JSONObject());
  if(data.getInt("schema")!=1||!(data.get("accounts") instanceof JSONObject))throw new IOException("Unsupported maintenance state schema");
 }
 JSONObject account(String uid)throws Exception{MaintenanceSchedule.uid(uid);JSONObject accounts=data.getJSONObject("accounts");if(!accounts.has(uid))accounts.put(uid,new JSONObject().put("features",new JSONObject()).put("operations",new JSONObject()));return accounts.getJSONObject(uid);}
 JSONObject feature(String uid,String feature)throws Exception{MaintenanceSchedule.feature(feature);JSONObject all=account(uid).getJSONObject("features");if(!all.has(feature))all.put(feature,new JSONObject().put("enabled",false).put("nextDueMs",0).put("failures",0));return all.getJSONObject(feature);}
 void enabled(String uid,String feature,boolean enabled)throws Exception{feature(uid,feature).put("enabled",enabled);save();}
 boolean enabled(String uid,String feature)throws Exception{return feature(uid,feature).getBoolean("enabled");}
 JSONObject operation(String uid,String key)throws Exception{return account(uid).getJSONObject("operations").optJSONObject(key);}
 boolean unresolved(String uid,String feature)throws Exception{
  MaintenanceSchedule.feature(feature);JSONObject ops=account(uid).getJSONObject("operations");java.util.Iterator<String> keys=ops.keys();while(keys.hasNext()){JSONObject op=ops.getJSONObject(keys.next());if(feature.equals(op.getString("feature"))&&!"verified".equals(op.getString("status"))&&!"cancelled_before_input".equals(op.getString("status")))return true;}return false;
 }
 JSONObject latestVerified(String uid,String feature,String target)throws Exception{JSONObject best=null,ops=account(uid).getJSONObject("operations");java.util.Iterator<String> keys=ops.keys();while(keys.hasNext()){JSONObject op=ops.getJSONObject(keys.next());if(feature.equals(op.optString("feature"))&&target.equals(op.optString("target"))&&"verified".equals(op.optString("status"))&&(best==null||op.optLong("verifiedMs")>best.optLong("verifiedMs")))best=op;}return best;}
 String begin(String uid,String feature,String period,String target,long nowMs,JSONObject before)throws Exception{
  if(nowMs<0)throw new IOException("Invalid attempt time");String key=MaintenanceSchedule.operation(feature,period,target);JSONObject ops=account(uid).getJSONObject("operations");
  String base=key;int retry=1;while(ops.has(key)){if(!"cancelled_before_input".equals(ops.getJSONObject(key).optString("status"))||retry>=1000)throw new IOException("Maintenance operation already attempted: "+key);key=base+"_retry_"+(++retry);}
  if(unresolved(uid,feature))throw new IOException("Another maintenance commit is unresolved");
  ops.put(key,new JSONObject().put("feature",feature).put("period",period).put("target",target).put("status","pending").put("attemptMs",nowMs).put("before",new JSONObject(before.toString())));save();return key;
 }
 void verified(String uid,String key,long nowMs,JSONObject after)throws Exception{
  JSONObject op=operation(uid,key);if(op==null||"verified".equals(op.optString("status")))throw new IOException("No unresolved maintenance operation");
  op.put("status","verified").put("verifiedMs",nowMs).put("after",new JSONObject(after.toString()));save();
 }
 void cancelBeforeInput(String uid,String key,JSONObject proof)throws Exception{
  JSONObject op=operation(uid,key);if(op==null||!(op.optString("status").equals("pending")||op.optString("status").equals("uncertain")))throw new IOException("No unresolved attempt to cancel");
  JSONObject receipt=proof.optJSONObject("receipt");if(receipt==null||receipt.optBoolean("inputDispatched",true)||!receipt.optString("phase").equals("native_pre_dispatch")||!(receipt.optString("requestAction").equals("ui-tap")||receipt.optString("requestAction").equals("training-collect"))||receipt.optBoolean("ok",true)||!proof.optBoolean("gameTimestampUnchanged"))throw new IOException("Cancellation requires no-dispatch receipt and fresh unchanged game timestamp");
  op.put("status","cancelled_before_input").put("cancellationProof",new JSONObject(proof.toString())).put("cancelledMs",System.currentTimeMillis());save();
 }
 void uncertain(String uid,String key,String reason)throws Exception{JSONObject op=operation(uid,key);if(op==null||"verified".equals(op.optString("status")))throw new IOException("No unresolved maintenance operation");op.put("status","uncertain").put("reason",reason);save();}
 void record(String uid,String feature,MaintenanceResult result,long nowMs)throws Exception{
  if(result.outcome==MaintenanceResult.Outcome.PREVIEW)return;
  JSONObject f=feature(uid,feature);f.put("lastOutcome",result.outcome.name()).put("reason",result.reason).put("lastAttemptMs",nowMs).put("nextDueMs",result.nextDueMs).put("evidence",new JSONObject(result.evidence));
  if(result.outcome==MaintenanceResult.Outcome.COMPLETED){f.put("lastSuccessMs",nowMs).put("failures",0);}else if(result.outcome==MaintenanceResult.Outcome.FAILED)f.put("failures",f.getInt("failures")+1);
  save();
 }
 boolean due(String uid,String feature,long nowMs)throws Exception{JSONObject f=feature(uid,feature);return MaintenanceSchedule.due(nowMs,f.getLong("nextDueMs"),unresolved(uid,feature)||"UNCERTAIN".equals(f.optString("lastOutcome")));}
 void save()throws Exception{ShareLedger.atomic(file,data);}
}
