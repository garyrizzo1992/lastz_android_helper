package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
final class BaseBubbleInspectionFeature implements MaintenanceFeature {
 public String id(){return "base_bubble_inspection";}public int priority(){return 80;}public boolean requiresInstrumentation(){return false;}
 public MaintenanceResult run(MaintenanceContext c)throws Exception{if(!c.preview)throw new IOException("Base bubble inventory requires dryRun:true");c.active();JSONObject snapshot=BaseBubbleReader.read(c.controller.cache,c.uid);Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Own-base bubble inventory only: "+snapshot.getJSONArray("bubbles").length()+" unclassified; no collection",0,evidence);}
}
