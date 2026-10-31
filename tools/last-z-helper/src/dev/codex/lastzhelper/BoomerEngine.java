package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Activation transaction. Navigation and native permissions remain in the phone adapter. */
final class BoomerEngine {
 interface World {
  void active()throws Exception;
  long now();
  JSONObject read()throws Exception;
  void activate(JSONObject before)throws Exception;
  void pause(long millis)throws Exception;
 }
 interface Journal {
  String uid();
  boolean unresolved()throws Exception;
  JSONObject previous()throws Exception;
  String begin(String period,long now,JSONObject before)throws Exception;
  void verified(String key,long now,JSONObject after)throws Exception;
  void uncertain(String key,String reason)throws Exception;
 }
 static int options(JSONObject snapshot)throws Exception{
  JSONArray rows=snapshot.getJSONArray("options");if(rows.length()!=2)throw new IOException("Auto Team-Up join options are incomplete");int mask=0;
  for(int i=0;i<2;i++){JSONObject row=rows.getJSONObject(i);if(row.getInt("type")!=i+1||!(row.get("selected") instanceof Boolean))throw new IOException("Auto Team-Up join option identity changed");if(row.getBoolean("selected"))mask|=1<<i;}
  return mask;
 }
 static JSONObject read(World world,String uid)throws Exception{
  world.active();JSONObject snapshot=world.read();long now=world.now(),observed=snapshot.getLong("observedMs");
  if(!uid.equals(snapshot.getString("accountUid"))||!"40005".equals(snapshot.getString("activityId"))||observed<=0||observed>now||now-observed>15000)throw new IOException("Auto Team-Up account/event or observation changed");
  options(snapshot);String state=snapshot.getString("state");long expiry=snapshot.getLong("expiryMs"),timer=snapshot.getLong("timerSeconds");
  if(state.equals("INACTIVE")){if(expiry!=0||timer!=-2)throw new IOException("Auto Team-Up inactive proof changed");}
  else if(state.equals("ACTIVE")){if(expiry<=now||expiry-observed>BoomerPolicy.DURATION+5000||timer<0||Math.abs((expiry-observed)/1000-timer)>5)throw new IOException("Auto Team-Up active expiry proof changed");}
  else if(!state.equals("BLOCKED"))throw new IOException("Unknown Auto Team-Up state");
  return snapshot;
 }
 static MaintenanceResult run(Journal journal,World world,boolean preview)throws Exception{
  String pending=null;
  try{
   world.active();String uid=MaintenanceSchedule.uid(journal.uid());
   // Defense in depth: a direct caller must not bypass MaintenanceRunner's barrier.
   if(journal.unresolved())return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Previous Auto Team-Up operation requires receipt reconciliation; no activation",0);
   JSONObject before=read(world,uid);String state=before.getString("state");
   if(state.equals("BLOCKED"))return result(MaintenanceResult.Outcome.BLOCKED,"Auto Team-Up state is ambiguous; no activation",world.now()+BoomerPolicy.RETRY,before);
   if(preview)return result(MaintenanceResult.Outcome.PREVIEW,"Auto Boomer preview: "+state+"; no activation",state.equals("ACTIVE")?before.getLong("expiryMs"):world.now()+BoomerPolicy.RETRY,before);
   if(state.equals("ACTIVE"))return result(MaintenanceResult.Outcome.NOTHING_TO_DO,"Auto Team-Up already active; existing expiry retained",before.getLong("expiryMs"),before);
   int choices=options(before);if(choices==0)return result(MaintenanceResult.Outcome.BLOCKED,"Choose at least one join option in the game",world.now()+BoomerPolicy.RETRY,before);
   JSONObject previous=journal.previous();String period=previous==null?"initial":"after_"+previous.getJSONObject("after").getLong("expiryMs");
   JSONObject fresh=read(world,uid);if(!fresh.getString("state").equals("INACTIVE")||options(fresh)!=choices)throw new IOException("Auto Team-Up state/options changed before activation");
   world.active();long sent=world.now();fresh.put("activationRequestedMs",sent);
   pending=journal.begin(period,sent,fresh);world.active();world.activate(fresh);
   world.pause(500);JSONObject after=read(world,uid);long deadline=sent+12000;
   while(after.getString("state").equals("INACTIVE")&&options(after)==choices&&world.now()<deadline){world.pause(250);after=read(world,uid);}
   if(!after.getString("state").equals("ACTIVE")||options(after)!=choices||!BoomerPolicy.activated(before.getLong("expiryMs"),after.getLong("expiryMs"),sent,after.getLong("observedMs"))||!BoomerReconciliationPolicy.receipt(fresh,after))throw new IOException("Auto Team-Up activation expiry/options receipt not confirmed");
   // Save conclusive proof even if STOP arrives just after the read. No further
   // game input follows; the caller still checks STOP before UI cleanup.
   after.put("activationSentMs",sent);journal.verified(pending,world.now(),after);pending=null;
   return result(MaintenanceResult.Outcome.COMPLETED,"Auto Team-Up activated; 12-hour expiry verified, join choices preserved",after.getLong("expiryMs"),after);
  }catch(InterruptedException stopped){throw stopped;}
  catch(Exception failure){
   if(pending!=null){journal.uncertain(pending,failure.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Auto Team-Up attempt retained; no repeat: "+failure.getMessage(),0);}
   return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"Auto Team-Up stopped: "+failure.getMessage(),world.now()+BoomerPolicy.RETRY);
  }
 }
 static MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,long due,JSONObject snapshot){return new MaintenanceResult(outcome,reason,due,Collections.singletonMap("snapshot",snapshot.toString()));}
}
