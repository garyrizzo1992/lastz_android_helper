package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Durable retry budgets; controller restarts never reset a failing step. */
final class RecoveryState {
 final File file;final JSONObject data;
 RecoveryState(File file)throws Exception{this.file=file;data=file.exists()?new JSONObject(StateProbe.text(file.getPath())):new JSONObject().put("schema",1).put("steps",new JSONObject()).put("restarts",new JSONObject());if(data.getInt("schema")!=1)throw new IOException("Unknown recovery schema");data.getJSONObject("steps");data.getJSONObject("restarts");}
 JSONObject step(String uid,String feature)throws Exception{MaintenanceSchedule.uid(uid);MaintenanceSchedule.feature(feature);String key=uid+":"+feature;JSONObject all=data.getJSONObject("steps");if(!all.has(key))all.put(key,new JSONObject().put("attempts",0).put("nextRetryMs",0).put("deferredUntilMs",0));return all.getJSONObject(key);}
 int attempts(String uid,String f)throws Exception{return step(uid,f).getInt("attempts");}
 long deferred(String uid,String f)throws Exception{return step(uid,f).getLong("deferredUntilMs");}
 long retry(String uid,String f,String reason,long now)throws Exception{JSONObject s=step(uid,f);int n=s.getInt("attempts");long due=Math.max(s.getLong("nextRetryMs"),Math.addExact(now,RecoveryPolicy.delay(n)));s.put("attempts",n+1).put("reason",reason).put("nextRetryMs",due);save();return due;}
 void defer(String uid,String f,String reason,long now)throws Exception{step(uid,f).put("reason",reason).put("deferredUntilMs",Math.addExact(now,RecoveryPolicy.COOLDOWN));save();}
 void allowEpisode(String uid,String f,long now)throws Exception{JSONObject s=step(uid,f);long due=s.getLong("deferredUntilMs");if(due>0&&now>=due){s.put("attempts",0).put("nextRetryMs",0).put("deferredUntilMs",0);save();}}
 void success(String uid,String f)throws Exception{step(uid,f).put("attempts",0).put("nextRetryMs",0).put("deferredUntilMs",0).remove("reason");save();}
 long accountUntil(String uid)throws Exception{JSONObject row=data.optJSONObject("accountCooldowns");return row==null?0:row.optLong(uid,0);}
 void deferAccount(String uid,long now)throws Exception{JSONObject all=data.optJSONObject("accountCooldowns");if(all==null){all=new JSONObject();data.put("accountCooldowns",all);}all.put(uid,Math.addExact(now,RecoveryPolicy.COOLDOWN));save();}
 boolean restart(String uid,long now)throws Exception{MaintenanceSchedule.uid(uid);JSONObject all=data.getJSONObject("restarts");JSONArray old=all.optJSONArray(uid),recent=new JSONArray();if(old!=null)for(int i=0;i<old.length();i++){long t=old.getLong(i);if(t>now||now-t<RecoveryPolicy.WINDOW)recent.put(t);}if(!RecoveryPolicy.restartAllowed(recent.length()))return false;recent.put(now);all.put(uid,recent);save();return true;}
 void save()throws Exception{RotationFiles.write(file,data);}
}
