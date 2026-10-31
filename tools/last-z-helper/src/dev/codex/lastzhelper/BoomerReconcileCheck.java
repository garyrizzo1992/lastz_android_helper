package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Receipt-only diagnostic. Optional guarded navigation never permits activation. */
public final class BoomerReconcileCheck {
 public static void main(String[] args){JSONObject output=new JSONObject();try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length!=6&&!(args.length==7&&args[6].equals("--navigate")))throw new IOException("Expected data directory, injector, agent, stop, expected UID, preview and optional --navigate");boolean navigate=args.length==7;
  if(!args[4].matches("[0-9]{8,24}")||!(args[5].equals("true")||args[5].equals("false")))throw new IOException("Exact UID and preview flag required");
  File locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();try(RandomAccessFile file=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel channel=file.getChannel();FileLock lock=channel.tryLock()){
   if(lock==null)throw new IOException("Another controller is active");ControllerOwnership.check();RecoveryGuard.noInjector();
   try(DisplaySession display=new DisplaySession()){
    AutomationController controller=new AutomationController(new File(args[0]),new File(args[1]),new File(args[2]),new File(args[3]),Boolean.parseBoolean(args[5]),0);MaintenanceContext c=new MaintenanceContext(controller);
    if(!args[4].equals(c.uid))throw new IOException("Expected character is not active");
    // The receipt scope always uses preview-level permissions, even when recording
    // a verified receipt to the caller's ledger. Activate/Off/options remain forbidden.
    int resolved=navigate?BoomerRecoveryNavigation.inspect(c):BoomerReceiptRecovery.inspect(c.store,c.uid,c.preview,new BoomerReceiptRecovery.World(){
     public void active()throws Exception{c.active();}public long now(){return System.currentTimeMillis();}
     public JSONObject read()throws Exception{return new BoomerReader(c).read();}
    });
    output=new JSONObject().put("event","boomer-reconciliation").put("ok",true).put("accountUid",c.uid).put("resolved",resolved).put("unresolved",c.store.unresolved(c.uid,"boomer_auto_join")).put("dryRun",c.preview).put("activationSent",false).put("navigationAllowed",navigate).put("readOnlyReceipt",true);
   }
  }
 }catch(Throwable e){try{output=new JSONObject().put("event","boomer-reconciliation-error").put("ok",false).put("stopped",e instanceof InterruptedException).put("activationSent",false).put("error",e.toString());}catch(Exception ignored){}e.printStackTrace();}System.out.println(output);if(!output.optBoolean("ok",false))System.exit(1);}
}
