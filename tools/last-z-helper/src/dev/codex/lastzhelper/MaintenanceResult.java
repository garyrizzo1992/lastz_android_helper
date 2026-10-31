package dev.codex.lastzhelper;
import java.util.*;
/** A verified outcome is distinct from a tap, a cooldown, or an uncertain commit. */
final class MaintenanceResult {
 enum Outcome {COMPLETED,NOTHING_TO_DO,WAITING,BLOCKED,FAILED,UNCERTAIN,PREVIEW}
 final Outcome outcome;final String reason;final long nextDueMs;final Map<String,String> evidence;
 MaintenanceResult(Outcome outcome,String reason,long nextDueMs,Map<String,String> evidence){
  if(outcome==null||reason==null||reason.length()>2000||nextDueMs<0)throw new IllegalArgumentException("Invalid maintenance outcome");
  this.outcome=outcome;this.reason=reason;this.nextDueMs=nextDueMs;this.evidence=Collections.unmodifiableMap(new LinkedHashMap<>(evidence));
 }
 static MaintenanceResult of(Outcome outcome,String reason,long nextDueMs){return new MaintenanceResult(outcome,reason,nextDueMs,Collections.emptyMap());}
 boolean uncertain(){return outcome==Outcome.UNCERTAIN;}
}
