package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Bounded personal finished-reward pass. Never starts missions or assists/steals. */
final class WantedFeature implements MaintenanceFeature {
 static final String ENTRY="UIManagerInstance/windows/MainUI_SU/View/bottomLayer/dispatchBtn",CLOSE=WantedPolicy.VIEW+"bottomCloseBtn",REWARD="UIManagerInstance/windows/UIDispatchRewardGet/View/btn";
 public String id(){return "wanted_finished_reward";}public int priority(){return 71;}
 public boolean deferInstrumentationUntilAction(){return true;}
 public boolean permitsInput(String action,String path,boolean preview){return action.equals("ui-tap")&&(path.equals(ENTRY)||path.equals(CLOSE)||path.equals("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn")||(!preview&&path.equals(REWARD))||new WantedClaimCheckFeature().permitsInput(action,path,preview));}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  int claimed=0;JSONArray receipts=new JSONArray();try{
   context.active();try(GameMemory m=new GameMemory(context.controller.cache)){if(!WantedReader.knownWindows(m,false))return result(MaintenanceResult.Outcome.BLOCKED,"Close unrelated menus before Wanted rewards",claimed,receipts);}
   if(!context.controller.open("UIActivityCenterTable")){context.base();JSONObject hidden=WantedReader.hiddenShortcutStatus(context.controller.cache);if(hidden!=null){receipts.put(hidden);if(hidden.optBoolean("inspectionDeferred")){Map<String,String> evidence=new LinkedHashMap<>();evidence.put("verifiedClaims","0");evidence.put("steps",receipts.toString());return new MaintenanceResult(context.preview?MaintenanceResult.Outcome.PREVIEW:MaintenanceResult.Outcome.WAITING,"Wanted shortcut hidden; rewards remain uninspected, retry in 15 minutes",System.currentTimeMillis()+900000,evidence);}return result(hidden.getBoolean("noReadyInLoadedRecords")?MaintenanceResult.Outcome.NOTHING_TO_DO:MaintenanceResult.Outcome.BLOCKED,hidden.getBoolean("noReadyInLoadedRecords")?"Wanted shortcut hidden; no completed unreceived reward in loaded personal records":"Wanted shortcut hidden despite an unconfirmed/pending personal task",0,receipts);}route(context,ENTRY,"entry");context.controller.waitWindow("UIActivityCenterTable",5000);}
   for(int pass=0;pass<10;pass++){
    MaintenanceResult step=new WantedClaimCheckFeature().run(context);receipts.put(new JSONObject().put("outcome",step.outcome.name()).put("reason",step.reason).put("evidence",new JSONObject(step.evidence)));
    if(step.outcome==MaintenanceResult.Outcome.COMPLETED){claimed++;dismissReward(context);continue;}
    if(step.outcome==MaintenanceResult.Outcome.NOTHING_TO_DO)return result(claimed>0?MaintenanceResult.Outcome.COMPLETED:MaintenanceResult.Outcome.NOTHING_TO_DO,"Wanted finished rewards collected: "+claimed+"; no missions dispatched",claimed,receipts);
    return result(step.outcome,step.reason,claimed,receipts);
   }
   return result(MaintenanceResult.Outcome.BLOCKED,"Wanted bounded pass ended after ten verified rewards; run again to inspect remaining tasks",claimed,receipts);
  }catch(InterruptedException e){throw e;}catch(Exception e){return result(MaintenanceResult.Outcome.BLOCKED,"Wanted stopped after "+claimed+" verified rewards: "+e.getMessage(),claimed,receipts);}
  finally{context.active();closePanel(context);}
 }
 void route(MaintenanceContext context,String path,String route)throws Exception{context.input.action(new JSONObject().put("action","ui-tap").put("path",path).put("wantedRoute",route));context.input.pause(450);}
 void dismissReward(MaintenanceContext context)throws Exception{
  long deadline=System.currentTimeMillis()+5000;while(!context.controller.open("UIDispatchRewardGet")&&System.currentTimeMillis()<deadline){context.active();context.input.pause(150);}if(!context.controller.open("UIDispatchRewardGet"))throw new IOException("Verified reward popup did not appear; stopped before another claim");
  for(int attempt=0;attempt<2;attempt++){
   try(GameMemory m=new GameMemory(context.controller.cache)){if(!m.open("UIDispatchRewardGet"))return;if(!WantedReader.knownWindows(m,true)||!"Congratulations!".equals(GameMemory.string(m.path("UIManagerInstance/windows/UIDispatchRewardGet/View"),"nameText")))throw new IOException("Unexpected Wanted reward overlay");}
   route(context,REWARD,"reward");context.input.pause(300);
  }
  if(context.controller.open("UIDispatchRewardGet"))throw new IOException("Wanted reward overlay did not close");
 }
 void closePanel(MaintenanceContext context)throws Exception{
  for(int attempt=0;attempt<2;attempt++){
   try(GameMemory m=new GameMemory(context.controller.cache)){if(!m.open("UIActivityCenterTable"))return;if(m.state.getInt("modalWindowCount")!=1||!WantedReader.knownWindows(m,false))return;if(!"400001".equals(GameMemory.string(m.path(WantedPolicy.VIEW.substring(0,WantedPolicy.VIEW.length()-1)),"lastActivityId")))return;}
   route(context,CLOSE,"close");context.input.pause(300);
  }
  if(context.controller.open("UIActivityCenterTable"))throw new IOException("Wanted panel did not close");
 }
 MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,int claimed,JSONArray receipts){Map<String,String> evidence=new LinkedHashMap<>();evidence.put("verifiedClaims",Integer.toString(claimed));evidence.put("steps",receipts.toString());return new MaintenanceResult(outcome,reason,0,evidence);}
}
