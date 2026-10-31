package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** One known own production bubble's geometry; no input capability exists. */
final class BaseResourceGeometryFeature implements MaintenanceFeature {
 public String id(){return "base_resource_geometry";}public int priority(){return 81;}
 public boolean permitsInput(String action,String path,boolean preview){return preview&&path.isEmpty()&&action.equals("base-resource-geometry-preview");}
 public MaintenanceResult run(MaintenanceContext c)throws Exception{
  if(!c.preview)throw new IOException("Resource geometry requires dryRun:true");c.active();JSONObject snapshot=BaseBubbleReader.read(c.controller.cache,c.uid);JSONArray rows=snapshot.getJSONArray("bubbles"),misses=new JSONArray();int checked=0;
  for(int i=0;i<rows.length();i++){
   JSONObject row=rows.getJSONObject(i),counter=row.getJSONObject("ownInventoryObservation");if(row.getLong("buildingItemId")!=731000||!counter.optString("status").equals("EXACT_OWN_COUNTER_OBSERVED")||!counter.optString("itemId").equals("200394"))continue;
   if(checked>=4)break;checked++;long since=Long.parseLong(row.getJSONObject("buildingVersionObservation").getString("lastCollectTimeText"));
   try{JSONObject geometry=c.input.action(new JSONObject().put("action","base-resource-geometry-preview").put("resourceBuildingUid",row.getString("buildingUid")).put("resourceSince",since));Map<String,String> evidence=new LinkedHashMap<>();evidence.put("geometry",geometry.toString());evidence.put("building",row.toString());evidence.put("visibilityMisses",misses.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Known own production-bubble geometry inspected; no collection",0,evidence);}
   catch(InterruptedException e){throw e;}catch(Exception e){String error=e.getMessage();if(error!=null&&(error.endsWith("Collider clipped or outside camera")||error.endsWith("Scene candidate covered by UI")||error.endsWith("Resource collider raycast mismatch"))){misses.put(new JSONObject().put("buildingUid",row.getString("buildingUid")).put("reason",error));continue;}return MaintenanceResult.of(MaintenanceResult.Outcome.BLOCKED,"Resource geometry not verified; no input: "+error,0);}
  }
  return MaintenanceResult.of(MaintenanceResult.Outcome.BLOCKED,"No known production bubble passed visible geometry; checked "+checked+"; no input",0);
 }
}
