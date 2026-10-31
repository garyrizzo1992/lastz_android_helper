package dev.codex.lastzhelper;
import java.io.*;
/** Retry orchestration independent of Android; the adapter supplies fresh checks and input. */
final class RecoveryEngine {
 enum End {COMPLETE,QUARANTINED,REOPEN,DEFERRED}
 static final class Result {final End end;final MaintenanceResult outcome;Result(End end,MaintenanceResult r){this.end=end;outcome=r;}}
 interface World {
  void active()throws Exception;long now();void pause(long milliseconds)throws Exception;
  MaintenanceResult execute()throws Exception;boolean unresolved()throws Exception;boolean clear()throws Exception;
  void event(String stage,String message)throws Exception;
 }
 static Result run(RecoveryState state,String uid,String feature,boolean reopened,World world)throws Exception{
  while(true){world.active();long pending=state.step(uid,feature).getLong("nextRetryMs")-world.now();if(pending>0){world.event("retrying","Waiting to retry "+feature);world.pause(pending);world.active();}
   world.event("running",feature);MaintenanceResult r=world.execute();RecoveryPolicy.Action action=RecoveryPolicy.classify(r,world.unresolved());
   if(action==RecoveryPolicy.Action.CONTINUE){state.success(uid,feature);return new Result(End.COMPLETE,r);}
   if(action==RecoveryPolicy.Action.HALT)throw new IOException(r.reason);
   if(!world.clear())throw new IOException("Cannot establish clear game state after "+feature+": "+r.reason);
   if(action==RecoveryPolicy.Action.QUARANTINE){state.defer(uid,feature,"Read-only reconciliation required: "+r.reason,world.now());return new Result(End.QUARANTINED,r);}
   if(state.attempts(uid,feature)>=RecoveryPolicy.BACKOFF.length){if(!reopened)return new Result(End.REOPEN,r);state.defer(uid,feature,r.reason,world.now());return new Result(End.DEFERRED,r);}
   long when=state.retry(uid,feature,r.reason,world.now());world.event("retrying","Retry "+state.attempts(uid,feature)+"/3 for "+feature+" at "+when+": "+r.reason);
  }
 }
}
