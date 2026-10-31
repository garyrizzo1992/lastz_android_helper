package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Memory-only diagnostic: requires an already-open Wanted panel and cannot claim. */
final class WantedInspectionFeature implements MaintenanceFeature {
 public String id(){return "wanted_inspection";}public int priority(){return 70;}public boolean requiresInstrumentation(){return false;}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{context.active();JSONObject snapshot=WantedReader.read(context.controller.cache);Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Memory-only personal Wanted inspection: "+snapshot.getInt("readyInspectionOnly")+" finished rewards; no claim or dispatch",0,evidence);}
}
