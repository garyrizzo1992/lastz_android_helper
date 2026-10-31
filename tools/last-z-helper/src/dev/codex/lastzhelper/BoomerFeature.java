package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Free Auto Team-Up only; never Off, options, attacks, rewards or premium offers. */
final class BoomerFeature implements MaintenanceFeature {
 public String id(){return "boomer_auto_join";}public int priority(){return 90;}
 public boolean permitsInput(String action,String path,boolean preview){return BoomerNavigationPolicy.permits(action,path,preview);}
 public boolean permitsRequest(JSONObject request,boolean preview){
  if(request.has("label")||request.has("parent"))return false;
  if(request.has("child"))return BoomerNavigationPolicy.card(request.optString("eventCardPath"))&&BoomerNavigationPolicy.carousel(request.optString("action"),request.optString("path"),request.optString("child"),request.optString("direction"),request.optBoolean("eventCarousel"));
  return permitsInput(request.optString("action"),request.optString("path"),preview);
 }
 public MaintenanceResult run(MaintenanceContext c)throws Exception{
  String pending=null;JSONObject before=null;try{
   new BoomerNavigator(c).open();
   BoomerReader reader=new BoomerReader(c);before=reader.read();String state=before.getString("state");
   if(state.equals("BLOCKED"))return result(MaintenanceResult.Outcome.BLOCKED,"Auto Team-Up state is ambiguous; no activation",System.currentTimeMillis()+BoomerPolicy.RETRY,before);
   if(c.preview)return result(MaintenanceResult.Outcome.PREVIEW,"Auto Boomer preview: "+state+"; no activation",before.getLong("nextDueMs"),before);
   if(state.equals("ACTIVE"))return result(MaintenanceResult.Outcome.NOTHING_TO_DO,"Auto Team-Up already active; existing expiry retained",before.getLong("nextDueMs"),before);
   boolean selected=false;for(int i=0;i<before.getJSONArray("options").length();i++)selected|=before.getJSONArray("options").getJSONObject(i).getBoolean("selected");
   if(!selected)return result(MaintenanceResult.Outcome.BLOCKED,"Choose at least one join option in the game",System.currentTimeMillis()+BoomerPolicy.RETRY,before);
   JSONObject previous=c.store.latestVerified(c.uid,id(),"activate");String period=previous==null?"initial":"after_"+previous.getJSONObject("after").getLong("expiryMs");
   JSONObject fresh=reader.read();if(!fresh.getString("state").equals("INACTIVE")||!fresh.getJSONArray("options").toString().equals(before.getJSONArray("options").toString()))throw new IOException("Auto Team-Up state/options changed before activation");
   long sent=System.currentTimeMillis();fresh.put("activationRequestedMs",sent);
   pending=c.begin(id(),period,"activate",fresh);c.active();
   c.input.action(new JSONObject().put("action","ui-tap").put("path",BoomerReader.DIALOG+"autoJoinBtnN").put("boomerAction","activate").put("boomerExpiry",fresh.getLong("expiryMs")).put("boomerOption1",fresh.getJSONArray("options").getJSONObject(0).getBoolean("selected")).put("boomerOption2",fresh.getJSONArray("options").getJSONObject(1).getBoolean("selected")));
   c.input.pause(500);JSONObject after=reader.read();long receiptDeadline=sent+12000;
   while(after.getString("state").equals("INACTIVE")&&after.getJSONArray("options").toString().equals(before.getJSONArray("options").toString())&&System.currentTimeMillis()<receiptDeadline){c.input.pause(250);after=reader.read();}
   if(!after.getString("state").equals("ACTIVE")||!after.getJSONArray("options").toString().equals(before.getJSONArray("options").toString())||!BoomerPolicy.activated(before.getLong("expiryMs"),after.getLong("expiryMs"),sent,after.getLong("observedMs"))||!BoomerReconciliationPolicy.receipt(fresh,after))throw new IOException("Auto Team-Up activation expiry/options receipt not confirmed");
   after.put("activationSentMs",sent);c.store.verified(c.uid,pending,System.currentTimeMillis(),after);pending=null;return result(MaintenanceResult.Outcome.COMPLETED,"Auto Team-Up activated; 12-hour expiry verified, join choices preserved",after.getLong("nextDueMs"),after);
  }catch(InterruptedException e){throw e;}catch(Exception e){if(pending!=null){c.store.uncertain(c.uid,pending,e.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Auto Team-Up attempt retained; no repeat: "+e.getMessage(),0);}return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"Auto Team-Up stopped: "+e.getMessage(),System.currentTimeMillis()+BoomerPolicy.RETRY);}
  finally{c.active();new BoomerNavigator(c).close();}
 }
 MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,long due,JSONObject snapshot){return new MaintenanceResult(outcome,reason,due,Collections.singletonMap("snapshot",snapshot.toString()));}
}
