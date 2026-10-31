package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.concurrent.*;import org.json.*;
/** Python shell inputs execute while this process holds the same lock as native workers. */
public final class LegacyLease {
 public static void main(String[] args){try{
  if(args.length!=1)throw new IOException("Ownership token required");
  RecoveryGuard.noInjector();LegacyOwnershipSession.run(ControllerOwnership.MARKER.getParentFile(),args[0],new BufferedReader(new InputStreamReader(System.in,"UTF-8")),System.out,command->DeviceInput.exec(10,"su","2000","-c",command),()->android.os.SystemClock.elapsedRealtime());
 }catch(Throwable e){try{System.out.println(new JSONObject().put("event","ownership").put("ok",false).put("error",e.toString()));}catch(Exception ignored){}System.exit(1);}}
}
