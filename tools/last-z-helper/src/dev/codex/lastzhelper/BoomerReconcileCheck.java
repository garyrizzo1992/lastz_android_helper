package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Bounded diagnostic reconciliation; native getters only, no navigation or activation. */
public final class BoomerReconcileCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length!=6)throw new IOException("Expected data directory, injector, agent, stop, expected UID and preview");
  if(!args[4].matches("[0-9]{8,24}")||!(args[5].equals("true")||args[5].equals("false")))throw new IOException("Exact UID and preview flag required");
  File locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();try(RandomAccessFile file=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel channel=file.getChannel();FileLock lock=channel.tryLock()){
   if(lock==null)throw new IOException("Another controller is active");ControllerOwnership.check();RecoveryGuard.noInjector();
   try(DisplaySession display=new DisplaySession()){
    AutomationController controller=new AutomationController(new File(args[0]),new File(args[1]),new File(args[2]),new File(args[3]),Boolean.parseBoolean(args[5]),0);MaintenanceContext c=new MaintenanceContext(controller);
    if(!args[4].equals(c.uid))throw new IOException("Expected character is not active");
    // No consuming feature is installed as activeFeature; MaintenanceContext rejects all input.
    JSONObject after=new BoomerReader(c).read(),operations=c.store.account(c.uid).getJSONObject("operations");int resolved=0;java.util.Iterator<String> keys=operations.keys();
    while(keys.hasNext()){String key=keys.next();JSONObject op=operations.getJSONObject(key);if(!"boomer_auto_join".equals(op.optString("feature"))||!"activate".equals(op.optString("target"))||!(op.optString("status").equals("pending")||op.optString("status").equals("uncertain")))continue;
     boolean proof=false;try{proof=BoomerReconciliationPolicy.receipt(op.getJSONObject("before"),after);}catch(JSONException missing){/* Old attempts without a request timestamp remain fenced. */}
     if(proof){resolved++;if(!c.preview){after.put("reconciledReadOnly",true);c.store.verified(c.uid,key,System.currentTimeMillis(),after);}}
    }
    if(resolved>0&&!c.preview&&!c.store.unresolved(c.uid,"boomer_auto_join"))c.store.record(c.uid,"boomer_auto_join",new MaintenanceResult(MaintenanceResult.Outcome.NOTHING_TO_DO,"Interrupted Auto Team-Up activation verified read-only; existing expiry retained",after.getLong("nextDueMs"),java.util.Collections.singletonMap("snapshot",after.toString())),System.currentTimeMillis());
    System.out.println(new JSONObject().put("event","boomer-reconciliation").put("accountUid",c.uid).put("resolved",resolved).put("unresolved",c.store.unresolved(c.uid,"boomer_auto_join")).put("dryRun",c.preview).put("inputSent",false));
   }
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
