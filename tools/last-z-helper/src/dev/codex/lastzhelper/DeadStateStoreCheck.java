package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Synthetic fixture storage and zero-input navigation-skip verification. Not real dead-state evidence. */
public final class DeadStateStoreCheck {
 static int checks;static void check(boolean value)throws Exception{checks++;if(!value)throw new IOException("Dead state fixture check"+checks);}
 public static void main(String[] args)throws Exception{
  File dir=new File(args[0]);if(!dir.getCanonicalPath().startsWith("/data/local/tmp/lastz-deadstate-test-")||!dir.isDirectory())throw new IOException("Isolated fixture directory required");
  File file=new File(dir,"dead-states.json");if(file.exists())throw new IOException("Fresh fixture directory required");
  DeadStateStore store=new DeadStateStore(file);check(!store.contains(40));check(!store.record(41,"This server is unavailable",100));check(!file.exists());
  check(store.record(40,"The State you are searching for does not exist.",123));check(file.exists());check(new DeadStateStore(file).contains(40));
  check(!store.record(40,"The State you are searching for does not exist.",456));check(new DeadStateStore(file).states.getJSONObject("40").getLong("confirmedAtMs")==123);
  check(!store.contains(41));check(!store.record(41,"State 41 is not yet open.",789));check(!new DeadStateStore(file).contains(41));
  File bad=new File(dir,"invalid.json");try(FileOutputStream out=new FileOutputStream(bad)){out.write("{invalid".getBytes("UTF-8"));}boolean rejected=false;try{new DeadStateStore(bad);}catch(Exception expected){rejected=true;}check(rejected);
  try(RandomAccessFile lock=new RandomAccessFile("/data/local/tmp/codex-lastz-helper/control.lock","rw");FileChannel channel=lock.getChannel();FileLock lease=channel.tryLock();DeviceInput.Scope scope=new DeviceInput.Scope()){
   if(lease==null)throw new IOException("Controller active");AutomationController c=new AutomationController(dir,new File(dir,"NONEXISTENT-injector"),new File(dir,"NONEXISTENT-agent"),new File(dir,"stop-request"),true,0);
   c.input.requestGuard=request->{throw new IOException("Fixture must never request native actions");};c.mode="dead-state-fixture";
   check(!c.go(40,500,500));check(c.input.session==null);
   for(boolean group:new boolean[]{false,true}){c.configureBounties(group);c.bountyRun(40,40,false,1);JSONObject progress=new JSONObject(StateProbe.text(c.progress.getPath()));check(progress.getBoolean("complete")&&progress.getInt("nextState")==41);check(c.input.session==null&&c.sent==0&&c.scanned==0);}
  }
  System.out.println(new JSONObject().put("ok",true).put("fixtureChecks",checks).put("syntheticState",40).put("realGameStatesLearned",0).put("nativeInputRequested",false));
 }
}
