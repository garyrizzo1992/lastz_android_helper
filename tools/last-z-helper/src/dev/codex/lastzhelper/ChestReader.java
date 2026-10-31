package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Observed idle-reward popup state; opening is separate from collecting. */
final class ChestReader {
 static final String VIEW="UIManagerInstance/windows/UIStoryHangup/View/";
 final MaintenanceContext context;ChestReader(MaintenanceContext context){this.context=context;}
 JSONObject control(String name)throws Exception{return context.input.action(new JSONObject().put("action","ui-bounds").put("path",VIEW+name).put("stateOnly",true));}
 static boolean knownWindows(GameMemory m,boolean popup)throws Exception{Set<String> allowed=new HashSet<>(Arrays.asList("MainUI_SU","UIMultiLanguageFloatingBall","UIAlarm","TouchScreenEffect","UIJeepAdventureMain"));if(popup)allowed.add("UIStoryHangup");for(TruckDiscoveryProbe.Value row:GameMemory.rows(m.path("UIManagerInstance/windows")))if((row.tag&15)==5&&GameMemory.number(row.raw,"State")==2&&!allowed.contains(row.key))return false;return true;}
 static boolean routeOnly(GameMemory m)throws Exception{return m.state.getInt("modalWindowCount")==1&&m.open("UIJeepAdventureMain")&&!m.open("UIStoryHangup")&&GameMemory.string(m.path("UIManagerInstance/windowStack/#1"),"Name").equals("UIJeepAdventureMain")&&knownWindows(m,false);}

 JSONObject read()throws Exception{
  context.active();long since;int rewards=0;try(GameMemory m=new GameMemory(context.controller.cache)){if(!m.open("UIStoryHangup")||m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=1)throw new IOException("Idle reward popup context not confirmed");if(!knownWindows(m,true))throw new IOException("Unexpected active window over idle reward");long story=m.path("DataCenter/StoryManager");since=GameMemory.number(story,"hangupTime");for(TruckDiscoveryProbe.Value row:GameMemory.rows(GameMemory.f(story,"hangupReward")))if((row.tag&15)==5)rewards++;}
  JSONObject out=new JSONObject().put("hangupTime",since).put("rewardRows",rewards);for(String name:new String[]{"title_text","time_text","receive_text","receive_btn","time_desc_text","close_btn"})out.put(name,control(name));
  context.active();try(GameMemory m=new GameMemory(context.controller.cache)){if(!m.open("UIStoryHangup")||m.state.getInt("modalWindowCount")!=1||GameMemory.number(m.path("DataCenter/StoryManager"),"hangupTime")!=since)throw new IOException("Idle reward popup changed while reading");}return out;
 }
}
