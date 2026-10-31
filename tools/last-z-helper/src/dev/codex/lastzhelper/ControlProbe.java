package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
public final class ControlProbe {
 static void navigate(DeviceInput input,int target)throws Exception{
  JSONObject before=StateProbe.snapshot(input.cache);int scene=before.getInt("sceneId");if(scene==target)return;
  if((scene!=1&&scene!=2)||before.getInt("modalWindowCount")!=0)throw new IOException("Close in-game menus before navigation");
  input.tapControl("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn");for(int i=0;i<6;i++){JSONObject after=StateProbe.snapshot(input.cache);if(after.getInt("sceneId")==target)return;input.pause(300);}throw new IOException("Navigation result not confirmed");
 }
 public static void main(String[] a){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(a.length!=5)throw new IOException("Expected mode, cache, injector, agent, stop");File dir=new File("/data/local/tmp/codex-lastz-helper");dir.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(dir,"control.lock"),"rw");FileChannel channel=f.getChannel();FileLock lock=channel.tryLock()){
   if(lock==null)throw new IOException("Another controller is active");ControllerOwnership.check();RecoveryGuard.noInjector();try(DisplaySession display=new DisplaySession()){DeviceInput d=new DeviceInput(a[1],new File(a[4]),new File(a[2]),new File(a[3]),dir);d.foreground();int original=StateProbe.snapshot(a[1]).getInt("sceneId");
   if(a[0].equals("roundtrip")){navigate(d,original==1?2:1);navigate(d,original);}else if(a[0].equals("world")||a[0].equals("base"))navigate(d,a[0].equals("world")?2:1);else throw new IOException("Unknown navigation mode");
   System.out.println(new JSONObject().put("ok",true).put("state",StateProbe.snapshot(a[1])));}
  }
 }catch(Throwable e){System.out.println(e.toString());System.exit(1);}}
}
