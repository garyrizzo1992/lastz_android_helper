package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Inspect the already-open personal Wanted panel; no injection or navigation. */
final class WantedReader {
 static JSONObject hiddenShortcutStatus(String cache)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=0||!knownWindows(m,false))throw new IOException("Clear base required to inspect hidden Wanted shortcut");
   if(GameMemory.bool(m.path(WantedFeature.ENTRY),"activeSelf"))return null;
   long manager=m.path("DataCenter/ActDispatchTaskDataManager");if(!GameMemory.bool(manager,"actViewOpened"))return deferred(false,"Personal cache has not been loaded");
   JSONArray tasks=new JSONArray();List<String> decisions=new ArrayList<>();
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(GameMemory.f(manager,"singleTask"))){
    if((row.tag&15)!=5||tasks.length()>=64)throw new IOException("Personal task cache bound/type");long t=row.raw,id=GameMemory.number(t,"uuid");if(GameMemory.number(t,"cfgId")<=0)throw new IOException("Wanted config identity invalid");if(id<=0||!row.key.equals("#"+id))throw new IOException("Personal task identity invalid");
    String decision=WantedPolicy.classify(id,GameMemory.number(t,"rewarded"),GameMemory.number(t,"startTime"),GameMemory.number(t,"completionTime"),m.state.getLong("timestampMs"),GameMemory.bool(t,"isstealtask"),GameMemory.string(t,"uid"),GameMemory.number(t,"pointId"));
    decisions.add(decision);
    tasks.put(new JSONObject().put("uuid",Long.toString(id)).put("decision",decision));
   }
   if(tasks.length()==0)return deferred(true,"Personal cache is empty");
   return new JSONObject().put("readOnly",true).put("shortcutHidden",true).put("cachePreviouslyLoaded",true).put("noReadyInLoadedRecords",WantedCachePolicy.classify(true,true,decisions)==WantedCachePolicy.Decision.NO_READY_IN_LOADED_CACHE).put("serverCompletenessProven",false).put("tasks",tasks);
  }
 }
 static JSONObject deferred(boolean loaded,String reason)throws Exception{return new JSONObject().put("readOnly",true).put("shortcutHidden",true).put("cachePreviouslyLoaded",loaded).put("inspectionDeferred",true).put("reason",reason).put("serverCompletenessProven",false).put("noReadyInLoadedRecords",false).put("tasks",new JSONArray());}
 static boolean knownWindows(GameMemory m,boolean reward)throws Exception{Set<String> allowed=new HashSet<>(Arrays.asList("MainUI_SU","UIMultiLanguageFloatingBall","UIAlarm","TouchScreenEffect","UIActivityCenterTable"));if(reward)allowed.add("UIDispatchRewardGet");for(TruckDiscoveryProbe.Value row:GameMemory.rows(m.path("UIManagerInstance/windows")))if((row.tag&15)==5&&GameMemory.number(row.raw,"State")==2&&!allowed.contains(row.key)){
   // The game's nonmodal message banner can remain open over a clear base.
   // Recognize its exact prefab only; a modal or any other window still blocks.
   if(!row.key.equals("UICommonMessageBar"))return false;
   long stack=m.path("UIManagerInstance/windowStack"),length=GameMemory.number(stack,"length");if(length<0||length>32)throw new IOException("Wanted window stack bound");boolean modal=false;for(int i=1;i<=length;i++)if("UICommonMessageBar".equals(GameMemory.string(GameMemory.f(stack,"#"+i),"Name")))modal=true;
   if(!WantedWindowPolicy.passiveNotice(row.key,GameMemory.string(row.raw,"PrefabPath"),modal))return false;
  }return true;}
 static JSONObject read(String cache)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=1||!m.open("UIActivityCenterTable")||!knownWindows(m,false))throw new IOException("Open personal Wanted panel without overlays required; missions remain uninspected");
   long view=m.path(WantedPolicy.VIEW.substring(0,WantedPolicy.VIEW.length()-1)),panel=m.path(WantedPolicy.PANEL);
   if(!"400001".equals(GameMemory.string(panel,"activityId"))||!"DispatchTask".equals(GameMemory.string(GameMemory.f(panel,"_class_type"),"__cname"))||GameMemory.number(panel,"tab")!=1||!"400001".equals(GameMemory.string(view,"lastActivityId"))||GameMemory.number(view,"goID")!=400001||!GameMemory.bool(panel,"activeSelf"))throw new IOException("Wanted activity/class/personal-tab identity differs");
   long tasks=m.path("DataCenter/ActDispatchTaskDataManager/singleTask"),shown=GameMemory.f(panel,"showDatalist");JSONArray rows=new JSONArray();Set<Long> personalIds=new HashSet<>(),shownIds=new HashSet<>();for(TruckDiscoveryProbe.Value row:GameMemory.rows(tasks)){if((row.tag&15)!=5)throw new IOException("Invalid personal task cache");long id=GameMemory.number(row.raw,"uuid");if(id<=0||!row.key.equals("#"+id)||!personalIds.add(id))throw new IOException("Invalid or duplicate personal task identity");}if(personalIds.isEmpty())throw new IOException("Personal task cache is empty; loading/completeness unproven");int ready=0,excluded=0;
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(shown)){
    if((row.tag&15)!=5||!row.key.matches("#[1-9][0-9]?"))throw new IOException("Unexpected Wanted display row");
    if(rows.length()>=64)throw new IOException("Wanted row bound exceeded");long task=row.raw,uuid=GameMemory.number(task,"uuid"),rewarded=GameMemory.number(task,"rewarded"),start=GameMemory.number(task,"startTime"),end=GameMemory.number(task,"completionTime");
    if(GameMemory.number(task,"cfgId")<=0)throw new IOException("Wanted config identity invalid");String decision=WantedPolicy.classify(uuid,rewarded,start,end,m.state.getLong("timestampMs"),GameMemory.bool(task,"isstealtask"),GameMemory.string(task,"uid"),GameMemory.number(task,"pointId"));
    boolean linked=false,rendered=false,receive=false,go=false;
    if(!decision.equals("EXCLUDED")){
     linked=uuid>0&&GameMemory.f(tasks,"#"+uuid)==task;
     if(!linked||!shownIds.add(uuid))throw new IOException("Wanted display row does not match exact personal task UUID");
     long cells=GameMemory.f(panel,"cellList"),cell=GameMemory.optional(cells,row.key);
     if(cell!=0){if(GameMemory.number(cell,"tab")!=1||!row.key.substring(1).equals(GameMemory.string(cell,"__name")))throw new IOException("Wanted cell index/tab differs");rendered=GameMemory.bool(cell,"activeSelf");receive=GameMemory.bool(GameMemory.f(cell,"receive_btn"),"activeSelf");go=GameMemory.bool(GameMemory.f(cell,"go_btn"),"activeSelf");}
     if(decision.equals("READY_INSPECTION_ONLY")){if(!rendered||!receive||go)decision="BLOCKED";else ready++;}
    }else excluded++;
    rows.put(new JSONObject().put("index",row.key.substring(1)).put("uuid",Long.toString(uuid)).put("configId",GameMemory.number(task,"cfgId")).put("rewarded",rewarded).put("startTime",start).put("completionTime",end).put("personalRecordLinked",linked).put("rendered",rendered).put("receiveActive",receive).put("goActive",go).put("decision",decision));
   }
   if(!personalIds.equals(shownIds))throw new IOException("Displayed Wanted list does not cover the personal task cache");
   return new JSONObject().put("personalCacheCoverage",true).put("viewportId",GameMemory.number(GameMemory.f(panel,"scroll_view"),"instanceId")).put("accountUid",m.state.getString("accountUid")).put("activityId","400001").put("tab",1).put("readOnly",true).put("claimEnabled",false).put("readyInspectionOnly",ready).put("excludedRows",excluded).put("rows",rows);
  }
 }
}
