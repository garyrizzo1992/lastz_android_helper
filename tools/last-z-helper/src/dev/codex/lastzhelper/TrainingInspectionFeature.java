package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Memory-only preview: cannot inject, collect, heal, train or dispatch. */
final class TrainingInspectionFeature implements MaintenanceFeature {
 public String id(){return "training_inspection";}public int priority(){return 60;}public boolean requiresInstrumentation(){return false;}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{context.active();JSONObject snapshot=TrainingReader.read(context.controller.cache);int ready=0;JSONArray rows=snapshot.getJSONArray("queues");for(int i=0;i<rows.length();i++)if(rows.getJSONObject(i).getString("decision").equals("READY_TO_COLLECT"))ready++;Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Memory-only training inspection: "+ready+" completed queues; no collection",0,evidence);}
}
