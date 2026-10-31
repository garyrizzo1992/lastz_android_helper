package dev.codex.lastzhelper;
/** Pure rotation rules; elapsed visit budgets never interrupt a commit. */
final class RotationPolicy {
 static final String[] FEATURES={"vip","alliance_help","alliance_gifts","training_collection","wanted_finished_reward"};
 static boolean feature(String id){for(String known:FEATURES)if(known.equals(id))return true;return false;}
 static int minutes(int value){if(value<1||value>120)throw new IllegalArgumentException("Visit duration must be 1–120 minutes");return value;}
 static boolean halt(MaintenanceResult.Outcome outcome){return outcome==MaintenanceResult.Outcome.BLOCKED||outcome==MaintenanceResult.Outcome.FAILED||outcome==MaintenanceResult.Outcome.UNCERTAIN;}
 static long nextDue(String feature,MaintenanceResult result,long now){
  if(!feature(feature)||now<0)throw new IllegalArgumentException("Invalid rotation due policy");
  // Wanted currently returns zero after a bounded pass; prevent a busy claim loop.
  long minimum=feature.equals("wanted_finished_reward")?900000L:60000L;
  return Math.max(result.nextDueMs,Math.addExact(now,minimum));
 }
}
