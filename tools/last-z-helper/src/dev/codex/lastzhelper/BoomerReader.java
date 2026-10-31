package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Already-open dialog inspection, with exact event, timer and selected-type joins. */
final class BoomerReader {
 static final String EVENT="UIManagerInstance/windows/UIActivityCenterTable/View/",DIALOG="UIManagerInstance/windows/UIAllianceAutoJoinRally/View/",PANEL=EVENT+"panelComponentList/40005/";
 final MaintenanceContext c;BoomerReader(MaintenanceContext c){this.c=c;}
 JSONObject control(String key)throws Exception{return c.input.action(new JSONObject().put("action","ui-bounds").put("path",DIALOG+key).put("stateOnly",true));}
 static long identity(GameMemory m)throws Exception{
  if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=2||!m.open("UIActivityCenterTable")||!m.open("UIAllianceAutoJoinRally")||!"40005".equals(GameMemory.string(m.path(EVENT.substring(0,EVENT.length()-1)),"lastActivityId")))throw new IOException("Open Danger Lurks Auto Team-Up dialog without other menus");
  long p=m.path(PANEL.substring(0,PANEL.length()-1)),data=GameMemory.f(p,"data");if(!"40005".equals(GameMemory.string(p,"activityId"))||GameMemory.number(data,"type")!=21||!"40005".equals(GameMemory.string(data,"id"))||!GameMemory.bool(p,"activeSelf"))throw new IOException("Danger Lurks panel identity changed");
  return GameMemory.number(m.path(DIALOG.substring(0,DIALOG.length()-1)),"endTime");
 }
 static boolean exactBoolean(long table,String key)throws Exception{int tag=StateProbe.u8(StateProbe.findField(table,key)+8);if(tag!=1&&tag!=17)throw new IOException("Auto Team-Up option is not a boolean");return tag==17;}
 JSONObject read()throws Exception{
  c.active();long expiry,observed;JSONArray choices=new JSONArray();try(GameMemory m=new GameMemory(c.controller.cache)){
   expiry=identity(m);observed=m.state.getLong("timestampMs");for(String name:new String[]{"eventItem1","eventItem2"}){long item=m.path(DIALOG+name);int type=(int)GameMemory.number(item,"type");if(type!=(choices.length()+1)||!GameMemory.bool(item,"activeSelf"))throw new IOException("Auto Team-Up event option identity changed");choices.put(new JSONObject().put("type",type).put("selected",exactBoolean(item,"isImgYes")));}
   if(choices.getJSONObject(0).getInt("type")==choices.getJSONObject(1).getInt("type"))throw new IOException("Duplicate auto-rally type");
  }
  JSONObject title=control("titleN"),timer=control("leftTimeN"),info=control("autoInfoN"),off=control("stopBtn"),label=control("autoJoinBtnTxtN"),activate=control("autoJoinBtnN");
  try(GameMemory m=new GameMemory(c.controller.cache)){if(identity(m)!=expiry)throw new IOException("Auto Team-Up expiry changed during inspection");}
  long seconds=BoomerPolicy.seconds(timer.optString("text",null));BoomerPolicy.State state=BoomerPolicy.state(timer.getLong("timestampMs"),expiry,seconds,timer.getBoolean("active"),info.getBoolean("active"),off.getBoolean("active"),title.optString("text"),label.optString("text"),activate.getBoolean("active"),activate.getBoolean("interactable"));
  return new JSONObject().put("accountUid",c.uid).put("activityId","40005").put("state",state.name()).put("expiryMs",expiry).put("observedMs",timer.getLong("timestampMs")).put("timerSeconds",seconds).put("options",choices).put("readOnly",true).put("activateEnabled",state==BoomerPolicy.State.INACTIVE).put("nextDueMs",state==BoomerPolicy.State.ACTIVE?BoomerPolicy.nextCheck(timer.getLong("timestampMs"),expiry):timer.getLong("timestampMs")+BoomerPolicy.RETRY);
 }
}
