package dev.codex.lastzhelper;

import java.io.*;
import java.util.*;
import org.json.*;

/** Preview only: already-open Mail, memory reads, no injection/navigation/store writes. */
final class MailCoverageInspectionFeature implements MaintenanceFeature {
 public String id(){return "mail_coverage_inspection";}
 public int priority(){return 41;}
 public boolean requiresInstrumentation(){return false;}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  if(!context.preview)throw new IOException("Mail coverage inspection requires dryRun:true; no outcome will be persisted");
  context.active();JSONObject snapshot=MailCoverageReader.read(context.controller.cache,context.uid);context.active();
  Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.toString());
  return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Memory-only Mail coverage: "+snapshot.getString("coverageState")+"; no claims or mailbox completion",0,evidence);
 }
}
