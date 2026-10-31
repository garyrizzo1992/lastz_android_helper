package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Read-only comparison of reused and fully revalidated runtime state. No input. */
public final class RuntimeBindingTests {
 static int passed;static void expect(boolean value)throws Exception{if(!value)throw new IOException("Runtime binding check "+(passed+1)+" failed");passed++;}
 static void same(JSONObject a,JSONObject b)throws Exception{for(String key:new String[]{"pid","processStart","accountUid","sceneId","levelId","viewMode","modalWindowCount","gameStarted"})expect(a.get(key).equals(b.get(key)));}
 public static void main(String[] args){try{
  JSONObject full=StateProbe.snapshot(args[0]),fast=StateProbe.snapshot(args[0]);expect("validated runtime".equals(fast.getString("discovery")));same(full,fast);
  StateProbe.pinnedManagerClass=0;JSONObject rediscovered=StateProbe.snapshot(args[0]);expect(!"validated runtime".equals(rediscovered.getString("discovery")));same(fast,rediscovered);
  StateProbe.lastFocusPid="not-the-selected-pid";StateProbe.lastFocusNanos=System.nanoTime();boolean rejected=false;try{StateProbe.findPinnedProcess(false);}catch(IOException e){rejected=true;}expect(rejected);
  Perf.enabled=true;Perf.reset();StateProbe.verifyPinned();expect(Perf.report().getJSONObject("timings").getJSONObject("focusCheck").getLong("count")==1);expect(StateProbe.pinnedPid.equals(StateProbe.lastFocusPid));Perf.enabled=false;
  System.out.println("Passed "+passed+" live runtime binding/focus checks; no input sent");
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
