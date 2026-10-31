package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Native geometry preview for completed queues; collection permission remains absent. */
final class TrainingGeometryInspectionFeature implements MaintenanceFeature {
 public String id(){return "training_geometry";}public int priority(){return 61;}
 public boolean permitsInput(String action,String path,boolean preview){return action.equals("training-geometry-preview")&&path.isEmpty();}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  context.active();JSONObject snapshot=TrainingReader.read(context.controller.cache);JSONArray rows=snapshot.getJSONArray("queues"),geometry=new JSONArray();int failed=0;
  for(int i=0;i<rows.length();i++){JSONObject q=rows.getJSONObject(i);if(!q.getString("decision").equals("READY_TO_COLLECT"))continue;try{geometry.put(context.input.action(new JSONObject().put("action","training-geometry-preview").put("trainingQueueId",q.getString("queueId")).put("trainingBuildingUid",q.getString("buildingUid")).put("trainingEnd",q.getLong("endTime"))));}catch(Exception e){if(e instanceof InterruptedException)throw e;failed++;geometry.put(new JSONObject().put("queueId",q.getString("queueId")).put("error",e.toString()));}}
  Map<String,String> evidence=new LinkedHashMap<>();evidence.put("queues",snapshot.toString());evidence.put("geometry",geometry.toString());return new MaintenanceResult(failed>0?MaintenanceResult.Outcome.BLOCKED:MaintenanceResult.Outcome.PREVIEW,"Training geometry verified for "+(geometry.length()-failed)+" queues, failed "+failed+"; collection disabled",0,evidence);
 }
}
