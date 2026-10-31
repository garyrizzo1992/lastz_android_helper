package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
final class TrainingStartInspectionFeature implements MaintenanceFeature {
 public String id(){return "training_start_inspection";}public int priority(){return 82;}public boolean requiresInstrumentation(){return false;}
 public MaintenanceResult run(MaintenanceContext c)throws Exception{if(!c.preview)throw new IOException("Training start inspection requires dryRun:true");c.active();JSONObject snapshot=TrainingStartReader.read(c.controller.cache,c.uid);Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Training templates inspected: "+snapshot.getJSONArray("units").length()+"; starts disabled",0,evidence);}
}
