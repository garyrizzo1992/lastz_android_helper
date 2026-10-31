package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Bounded diagnostic: at most one completed own reward, already-open panel only. */
final class WantedClaimCheckFeature implements MaintenanceFeature {
 public String id(){return "wanted_finished_reward";}public int priority(){return 71;}
 public boolean permitsInput(String action,String path,boolean preview){return !preview&&action.equals("ui-tap")&&path.matches(java.util.regex.Pattern.quote(WantedPolicy.PANEL)+"/cellList/#[1-9][0-9]?/receive_btn");}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  String pending=null;try{
   context.active();JSONObject before=WantedReader.read(context.controller.cache);JSONArray rows=before.getJSONArray("rows");JSONObject chosen=null;
   for(int i=0;i<rows.length();i++)if(rows.getJSONObject(i).getString("decision").equals("READY_INSPECTION_ONLY")){chosen=rows.getJSONObject(i);break;}
   if(chosen==null){for(int i=0;i<rows.length();i++)if(rows.getJSONObject(i).getString("decision").equals("BLOCKED"))return result(MaintenanceResult.Outcome.BLOCKED,"Wanted row eligibility or visibility is unconfirmed",before);return result(MaintenanceResult.Outcome.NOTHING_TO_DO,"No rendered completed own Wanted reward; no GO or dispatch",before); }
   String path=WantedPolicy.PANEL+"/cellList/#"+chosen.getString("index")+"/receive_btn";
   JSONObject label=context.input.action(new JSONObject().put("action","ui-bounds").put("path",path+"_txt").put("stateOnly",true)),button=context.input.action(new JSONObject().put("action","ui-bounds").put("path",path).put("stateOnly",true));
   if(!label.optBoolean("active")||!"Claim".equals(label.optString("text"))||!button.optBoolean("active")||!button.optBoolean("interactable"))return result(MaintenanceResult.Outcome.BLOCKED,"Exact active free Claim control not confirmed",before);
   context.input.action(new JSONObject().put("action","ui-bounds").put("path",path).put("wantedUuid",chosen.getString("uuid")).put("wantedViewportId",before.getInt("viewportId")));
   if(context.preview)return result(MaintenanceResult.Outcome.PREVIEW,"One completed own Wanted Claim inspected; no input",before);
   String uuid=chosen.getString("uuid");long start=chosen.getLong("startTime"),end=chosen.getLong("completionTime"),config=chosen.getLong("configId");
   pending=context.begin(id(),"task_"+uuid,"finished_reward",chosen);
   context.input.action(new JSONObject().put("action","ui-tap").put("path",path).put("wantedIndex","#"+chosen.getString("index")).put("wantedUuid",uuid).put("wantedViewportId",before.getInt("viewportId")).put("wantedStart",start).put("wantedEnd",end).put("wantedConfig",config));
   long until=System.currentTimeMillis()+12000;JSONObject receipt=null;
   while(System.currentTimeMillis()<until){context.input.pause(200);try(GameMemory m=new GameMemory(context.controller.cache)){
    long task=m.path("DataCenter/ActDispatchTaskDataManager/singleTask/#"+uuid);
    if(GameMemory.number(task,"uuid")==Long.parseLong(uuid)&&GameMemory.number(task,"cfgId")==config&&GameMemory.number(task,"startTime")==start&&GameMemory.number(task,"completionTime")==end&&GameMemory.number(task,"rewarded")==1){receipt=new JSONObject().put("uuid",uuid).put("rewarded",1).put("startTime",start).put("completionTime",end).put("configId",config);break;}
   }}
   if(receipt==null)throw new IOException("Exact Wanted task rewarded transition not confirmed");
   context.store.verified(context.uid,pending,System.currentTimeMillis(),receipt);pending=null;
   return result(MaintenanceResult.Outcome.COMPLETED,"One own Wanted reward verified by exact task rewarded 0 to 1; stopped without dispatch",receipt);
  }catch(InterruptedException e){throw e;}catch(Exception e){if(pending!=null){context.store.uncertain(context.uid,pending,e.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Wanted attempt preserved; no retry: "+e.getMessage(),0);}return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"Wanted inspection stopped: "+e.getMessage(),0);}
 }
 MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,JSONObject snapshot){Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.toString());return new MaintenanceResult(outcome,reason,0,evidence);}
}
