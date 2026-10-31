package dev.codex.lastzhelper;
public final class RecoveryPolicyTests {
 static int checks;static void expect(boolean v,String m){if(!v)throw new AssertionError(m);checks++;}
 static MaintenanceResult r(MaintenanceResult.Outcome o,String reason){return MaintenanceResult.of(o,reason,0);}
 public static void main(String[] args){
  for(int i=0;i<3;i++)expect(RecoveryPolicy.delay(i)==new long[]{2000,10000,30000}[i],"backoff");for(int n:new int[]{-1,3}){boolean bad=false;try{RecoveryPolicy.delay(n);}catch(IllegalArgumentException e){bad=true;}expect(bad,"bounded attempts");}
  expect(RecoveryPolicy.restartAllowed(0)&&RecoveryPolicy.restartAllowed(2)&&!RecoveryPolicy.restartAllowed(3)&&!RecoveryPolicy.restartAllowed(-1),"restart budget");
  for(MaintenanceResult.Outcome o:MaintenanceResult.Outcome.values())expect(RecoveryPolicy.classify(r(o,"Gift tab did not settle"),true)==RecoveryPolicy.Action.QUARANTINE,"unresolved blocks retry "+o);
  expect(RecoveryPolicy.classify(r(MaintenanceResult.Outcome.UNCERTAIN,"timeout"),false)==RecoveryPolicy.Action.QUARANTINE,"uncertain cannot replay");
  for(String message:new String[]{"Gift tab did not settle","VIP check stopped: UI window context changed","Alliance Help stopped: Alliance menu did not expose Help","VIP check stopped: UIVip did not open; stopped"})expect(RecoveryPolicy.classify(r(MaintenanceResult.Outcome.FAILED,message),false)==RecoveryPolicy.Action.RETRY,"known transient "+message);
  for(String message:new String[]{"Unknown modal","Game build changed","Character changed","Claim receipt not confirmed","Selected game window changed or restarted","Lua field absent: score","Unknown cost","Input cleanup unconfirmed; exit 1","Character changed; Gift tab did not settle","Different focus; Alliance menu did not expose Help"})expect(RecoveryPolicy.classify(r(MaintenanceResult.Outcome.FAILED,message),false)==RecoveryPolicy.Action.HALT,"unsafe state "+message);
  for(MaintenanceResult.Outcome o:new MaintenanceResult.Outcome[]{MaintenanceResult.Outcome.COMPLETED,MaintenanceResult.Outcome.NOTHING_TO_DO,MaintenanceResult.Outcome.WAITING,MaintenanceResult.Outcome.PREVIEW})expect(RecoveryPolicy.classify(r(o,"busy/full/normal"),false)==RecoveryPolicy.Action.CONTINUE,"normal states don't restart");
  expect(RecoveryPolicy.sessionAllowed(true,false,"boot-A","boot-A"),"active user request");expect(!RecoveryPolicy.sessionAllowed(false,false,"boot-A","boot-A"),"stopped request");expect(!RecoveryPolicy.sessionAllowed(true,true,"boot-A","boot-A"),"STOP cancels recovery");expect(!RecoveryPolicy.sessionAllowed(true,false,"boot-A","boot-B"),"reboot not consent");expect(!RecoveryPolicy.sessionAllowed(true,false,null,"boot-A"),"missing boot rejected");
  System.out.println("Recovery policy: "+checks+" checks passed");
 }
}
