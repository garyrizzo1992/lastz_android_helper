package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Bounded chest inspection. No scene touch, popup claim or completion journal permission. */
final class ChestInspectionFeature implements MaintenanceFeature {
 public String id(){return "chest_inspection";}public int priority(){return 50;}
 public boolean permitsInput(String action,String path,boolean preview){return action.equals("chest-preview")&&path.isEmpty();}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  context.active();if(context.controller.open("UIStoryHangup")){JSONObject popup=new ChestReader(context).read();Map<String,String> evidence=new LinkedHashMap<>();evidence.put("popup",popup.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Idle reward popup inspected; no claim pressed",0,evidence);}long before;try(GameMemory m=new GameMemory(context.controller.cache)){if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=0)throw new IOException("Chest inspection requires base without dialogs");before=GameMemory.number(m.path("DataCenter/StoryManager"),"hangupTime");}
  JSONObject geometry=context.input.action(new JSONObject().put("action","chest-preview"));context.active();long now,after;
  try(GameMemory m=new GameMemory(context.controller.cache)){if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=0)throw new IOException("Chest context changed");after=GameMemory.number(m.path("DataCenter/StoryManager"),"hangupTime");now=m.state.getLong("timestampMs");}
  if(before!=after)throw new IOException("Chest accumulation changed during inspection");String status=ChestPolicy.inspect(now,after,geometry.optString("observedTime"),geometry.getJSONObject("collider").optBoolean("matches")&&!geometry.optBoolean("claimEnabled",true));
  Map<String,String> evidence=new LinkedHashMap<>();evidence.put("geometry",geometry.toString());evidence.put("hangupTime",Long.toString(after));evidence.put("inspectionStatus",status);evidence.put("claimEnabled","false");
  return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Chest "+status+"; collection remains disabled",0,evidence);
 }
}
