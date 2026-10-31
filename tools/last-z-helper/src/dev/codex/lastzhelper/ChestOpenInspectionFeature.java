package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Diagnostic one-open probe, journaled before input. Never presses a popup claim. */
final class ChestOpenInspectionFeature implements MaintenanceFeature {
 public String id(){return "chest_open_probe";}public int priority(){return 50;}
 public boolean permitsInput(String action,String path,boolean preview){return path.isEmpty()&&(action.equals("chest-preview")||(!preview&&action.equals("chest-open")));}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  if(context.preview)return new ChestInspectionFeature().run(context);String pending=null;
  try{
   long since,now;Set<String> before;try(GameMemory m=new GameMemory(context.controller.cache)){if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=0)throw new IOException("Open probe requires base without dialogs");since=GameMemory.number(m.path("DataCenter/StoryManager"),"hangupTime");now=m.state.getLong("timestampMs");before=windows(m);}
   JSONObject geometry=context.input.action(new JSONObject().put("action","chest-preview"));if(!ChestPolicy.inspect(now,since,geometry.optString("observedTime"),geometry.getJSONObject("collider").optBoolean("matches")).equals("FULL_INSPECTION_ONLY"))throw new IOException("Full chest inspection not confirmed");
   pending=context.begin(id(),ChestPolicy.period(since),"open_only",new JSONObject().put("hangupTime",since).put("geometry",geometry));
   context.input.action(new JSONObject().put("action","chest-open").put("chestSince",since));long until=System.currentTimeMillis()+6000;JSONObject after=null;
   while(System.currentTimeMillis()<until){context.input.pause(150);try(GameMemory m=new GameMemory(context.controller.cache)){if(GameMemory.number(m.path("DataCenter/StoryManager"),"hangupTime")!=since)throw new IOException("Accumulation changed during opening; reconcile before further actions");Set<String> added=windows(m);added.removeAll(before);if(m.state.getInt("sceneId")==1&&m.state.getInt("modalWindowCount")==1&&m.open("UIStoryHangup")&&!before.contains("UIStoryHangup")){after=new JSONObject().put("window","UIStoryHangup").put("hangupTime",since).put("claimPressed",false);break;}}}
   if(after==null)throw new IOException("Single chest inspection window not confirmed");context.store.verified(context.uid,pending,System.currentTimeMillis(),after);pending=null;Map<String,String> evidence=new LinkedHashMap<>();evidence.put("after",after.toString());return new MaintenanceResult(MaintenanceResult.Outcome.BLOCKED,"Opened "+after.getString("window")+" for metadata inspection; no claim pressed",0,evidence);
  }catch(InterruptedException e){throw e;}catch(Exception e){if(pending!=null){context.store.uncertain(context.uid,pending,e.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Chest opening requires review; no automatic retry: "+e.getMessage(),0);}return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"Chest open check stopped: "+e.getMessage(),0);}
 }
 Set<String> windows(GameMemory m)throws Exception{Set<String> out=new TreeSet<>();for(TruckDiscoveryProbe.Value row:GameMemory.rows(m.path("UIManagerInstance/windows")))if((row.tag&15)==5&&GameMemory.number(row.raw,"State")==2)out.add(row.key);return out;}
}
