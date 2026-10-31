package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import java.util.regex.*;import org.json.*;
/** Recovery never dismisses unknown windows or fights manual navigation. */
final class RecoveryGuard {
 static boolean clear(String cache)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   int scene=m.state.getInt("sceneId");if((scene!=1&&scene!=2)||m.state.getInt("modalWindowCount")!=0)return false;
   Set<String> base=new HashSet<>(Arrays.asList("MainUI_SU","UIMultiLanguageFloatingBall","UIAlarm","TouchScreenEffect"));
   for(TruckDiscoveryProbe.Value w:GameMemory.rows(m.path("UIManagerInstance/windows")))if((w.tag&15)==5&&GameMemory.number(w.raw,"State")==2&&!base.contains(w.key)){
    if(!WantedWindowPolicy.passiveNotice(w.key,GameMemory.string(w.raw,"PrefabPath"),false))return false;
   }return true;
  }
 }
 static boolean resumable(String cache,String feature)throws Exception{
  if(clear(cache))return true;
  try(GameMemory m=new GameMemory(cache)){
   int count=m.state.getInt("modalWindowCount");if(m.state.getInt("sceneId")!=1||count<1||count>2)return false;
   Set<String> allowed=new HashSet<>(Arrays.asList("MainUI_SU","UIMultiLanguageFloatingBall","UIAlarm","TouchScreenEffect"));
   if(feature.equals("vip")&&count==1&&m.open("UIVip"))allowed.add("UIVip");
   else if(feature.equals("alliance_help")&&m.open("UIAllianceMainTable")&&((count==1&&!m.open("UIAllianceHelp"))||(count==2&&m.open("UIAllianceHelp")))){allowed.add("UIAllianceMainTable");allowed.add("UIAllianceHelp");}
   else if(feature.equals("alliance_gifts")&&m.open("UIAllianceMainTable")&&((count==1&&!m.open("UIAllianceGift"))||(count==2&&m.open("UIAllianceGift")))){allowed.add("UIAllianceMainTable");allowed.add("UIAllianceGift");}
   else if(feature.equals("wanted_finished_reward")&&count==1&&m.open("UIActivityCenterTable")&&"400001".equals(GameMemory.string(m.path("UIManagerInstance/windows/UIActivityCenterTable/View"),"lastActivityId")))allowed.add("UIActivityCenterTable");
   else return false;
   for(TruckDiscoveryProbe.Value w:GameMemory.rows(m.path("UIManagerInstance/windows")))if((w.tag&15)==5&&GameMemory.number(w.raw,"State")==2&&!allowed.contains(w.key)){if(!WantedWindowPolicy.passiveNotice(w.key,GameMemory.string(w.raw,"PrefabPath"),false))return false;}
   return true;
  }
 }
 static boolean gone(String pid,String start)throws Exception{return pid!=null&&(!new File("/proc/"+pid).exists()||!start.equals(StateProbe.start(pid)));}
 static boolean home()throws Exception{
  String resolved=DeviceInput.exec(5,"/system/bin/cmd","package","resolve-activity","--brief","-a","android.intent.action.MAIN","-c","android.intent.category.HOME");String pkg=null;
  for(String line:resolved.split("\n"))if(line.trim().matches("[A-Za-z0-9_.]+/[A-Za-z0-9_.$]+"))pkg=line.trim().split("/")[0];if(pkg==null)return false;
  String windows=DeviceInput.exec(5,"/system/bin/dumpsys","window");return Pattern.compile("mCurrentFocus=Window\\{[^\\r\\n]*\\s"+Pattern.quote(pkg)+"/").matcher(windows).find();
 }
 static void noInjector()throws Exception{
  File[] all=new File("/proc").listFiles();if(all==null)throw new IOException("Cannot inspect old input sessions");
  for(File p:all)if(p.getName().matches("[0-9]+"))try{String name=new File(StateProbe.cmdline(p.getName())).getName();if(name.equals("injector-arm64-17.24.3")||name.equals("injector-17.24.3"))throw new ActiveInjector();}catch(ActiveInjector e){throw new IOException("Previous input session remains; restart blocked until detach is confirmed");}catch(FileNotFoundException ignored){}
 }
 static final class ActiveInjector extends IOException{}
 static void resume(File checkpoint,String cache)throws Exception{
  noInjector();if(!checkpoint.exists()){if(!home())throw new IOException("Worker recovery requires the expected game or launcher");return;}
  JSONObject p=new JSONObject(StateProbe.text(checkpoint.getPath()));String pid=p.optString("gamePid"),start=p.optString("gameStart"),uid=p.optString("lastAccountUid");
  if(pid.isEmpty()||uid.isEmpty()){if(pid.isEmpty()&&uid.isEmpty()&&p.optString("stage").equals("waiting")&&p.optInt("completedChecks",0)==0)return;if(!home())throw new IOException("Previous game identity unavailable; recovery needs attention");return;}
  if(gone(pid,start)){if(!home())throw new IOException("Game ended but another app is focused; recovery stopped");return;}
  StateProbe.pinForeground();JSONObject state=StateProbe.snapshot(cache);if(!uid.equals(state.getString("accountUid"))||!pid.equals(StateProbe.pinnedPid)||!start.equals(StateProbe.pinnedStart)||!resumable(cache,p.optString("feature")))throw new IOException("Previous game/focus/UI changed; automatic worker recovery stopped");
 }
}
