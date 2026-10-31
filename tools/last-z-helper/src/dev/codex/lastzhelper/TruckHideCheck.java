package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Bounded setting-only check; never scans, shares, refreshes or attacks trucks. */
public final class TruckHideCheck {
 public static void main(String[] args)throws Exception{File assets=new File(args[0]);
  try(RandomAccessFile f=new RandomAccessFile("/data/local/tmp/codex-lastz-helper/control.lock","rw");FileChannel channel=f.getChannel();FileLock lease=channel.tryLock();DeviceInput.Scope scope=new DeviceInput.Scope()){
   if(lease==null)throw new IOException("Controller active");
   AutomationController c=new AutomationController(new File("/data/user/0/dev.codex.lastzhelper/files"),new File(assets,"injector"),new File(assets,"input-agent.js"),new File(assets,"stop-request"),true,0);
   if(!args[1].equals(StateProbe.pinnedUid))throw new IOException("Expected bot account required");c.mode="truck-hide-check";
   final int[] taps={0};c.input.requestGuard=request->{String action=request.optString("action");if(!action.equals("inspect")&&!action.equals("ui-bounds")&&!action.equals("ui-tap"))throw new IOException("Only filter control inspection/click allowed");if(!action.equals("inspect")&&!request.optString("path").equals(TruckHidePolicy.PATH))throw new IOException("Only filter checkbox allowed");if(action.equals("ui-tap"))taps[0]++;};
   boolean before=c.trucksHideEnabled();c.ensureTrucks();int first=taps[0];c.ensureTrucks();
   if(!c.trucksHideEnabled()||taps[0]!=first)throw new IOException("Filter not idempotent");
   System.out.println(new JSONObject().put("ok",true).put("enabledBefore",before).put("enabledAfter",c.trucksHideEnabled()).put("enableClicks",first).put("repeatExtraClicks",taps[0]-first).put("shared",0).put("attacked",0));
  }
 }
}
