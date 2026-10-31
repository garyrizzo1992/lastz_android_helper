package dev.codex.lastzhelper;
/** Recovery is conservative: only recognized transient, non-consuming failures retry. */
final class RecoveryPolicy {
 static final long STALL_LIMIT=300000,DETACH_LIMIT=20000;
 static final long[] BACKOFF={2000,10000,30000};static final long COOLDOWN=900000,WINDOW=1800000;static final int MAX_RESTARTS=3;
 enum Action {CONTINUE,RETRY,QUARANTINE,HALT}
 static Action classify(MaintenanceResult result,boolean unresolved){
  if(unresolved||result.outcome==MaintenanceResult.Outcome.UNCERTAIN)return Action.QUARANTINE;
  if(result.outcome!=MaintenanceResult.Outcome.FAILED&&result.outcome!=MaintenanceResult.Outcome.BLOCKED)return Action.CONTINUE;
  String r=result.reason;
  for(String fatal:new String[]{"identity","character","account","focus","game build","unknown","unexpected","unconfirmed","not confirmed","detach","receipt","cost","lua field absent"})if(r.toLowerCase(java.util.Locale.ROOT).contains(fatal))return Action.HALT;
  // These describe bounded navigation/readiness, not unknown account/build/modal/cost.
  if(r.contains("UI window context changed")||r.matches(".*(?:UIVip|UIAllianceHelp|UIAllianceGift|UIAllianceMainTable) did not open; stopped.*")||r.contains("Gift tab did not settle")||r.contains("Alliance menu did not expose ")||r.contains("Bounded discovery exhausted. Retry while the game is fully loaded."))return Action.RETRY;
  return Action.HALT;
 }
 static long delay(int attempt){if(attempt<0||attempt>=BACKOFF.length)throw new IllegalArgumentException("Retry bound");return BACKOFF[attempt];}
 static boolean restartAllowed(int recent){return recent>=0&&recent<MAX_RESTARTS;}
 static boolean sessionAllowed(boolean running,boolean stop,String savedBoot,String currentBoot){return running&&!stop&&savedBoot!=null&&savedBoot.equals(currentBoot);}
}
