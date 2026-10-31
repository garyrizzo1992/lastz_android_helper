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
  try{
   new BoomerNavigator(c).open();final BoomerReader reader=new BoomerReader(c);
   MaintenanceResult result=BoomerEngine.run(new BoomerEngine.Journal(){
    public String uid(){return c.uid;}
    public boolean unresolved()throws Exception{return c.store.unresolved(c.uid,id());}
    public JSONObject previous()throws Exception{return c.store.latestVerified(c.uid,id(),"activate");}
    public String begin(String period,long now,JSONObject before)throws Exception{return c.begin(id(),period,"activate",before);}
    public void verified(String key,long now,JSONObject after)throws Exception{c.store.verified(c.uid,key,now,after);}
    public void uncertain(String key,String reason)throws Exception{c.store.uncertain(c.uid,key,reason);}
   },new BoomerEngine.World(){
    public void active()throws Exception{c.active();}
    public long now(){return System.currentTimeMillis();}
    public JSONObject read()throws Exception{return reader.read();}
    public void pause(long millis)throws Exception{c.input.pause(millis);}
    public void activate(JSONObject before)throws Exception{
     c.input.action(new JSONObject().put("action","ui-tap").put("path",BoomerReader.DIALOG+"autoJoinBtnN").put("boomerAction","activate").put("boomerExpiry",before.getLong("expiryMs")).put("boomerOption1",before.getJSONArray("options").getJSONObject(0).getBoolean("selected")).put("boomerOption2",before.getJSONArray("options").getJSONObject(1).getBoolean("selected")));
    }
   },c.preview);
   if(result.outcome==MaintenanceResult.Outcome.FAILED||result.outcome==MaintenanceResult.Outcome.UNCERTAIN)c.event(id(),result.reason);
   return result;
  }catch(InterruptedException e){throw e;}catch(Exception e){c.event(id(),"Auto Team-Up stopped: "+e.getMessage());return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"Auto Team-Up stopped: "+e.getMessage(),System.currentTimeMillis()+BoomerPolicy.RETRY);}
  finally{c.active();new BoomerNavigator(c).close();}
 }
}
