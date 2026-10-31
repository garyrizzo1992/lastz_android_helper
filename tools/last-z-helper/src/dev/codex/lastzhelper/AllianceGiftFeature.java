package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Bounded Common/Rare gift collection; no level chest, delete, purchase or settings input. */
final class AllianceGiftFeature implements MaintenanceFeature {
 public String id(){return "alliance_gifts";}public int priority(){return 30;}
 public boolean permitsInput(String action,String path,boolean preview){return action.equals("ui-tap")&&AllianceGiftPolicy.allowed(path,preview);}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  AutomationController c=context.controller;String pending=null;AllianceGiftReader reader=new AllianceGiftReader(context);int claimed=0;JSONArray evidence=new JSONArray();
  try{
   if(!c.open("UIAllianceGift")){
    if(!c.open("UIAllianceMainTable")){context.base();context.input.tapControl("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/alliance_btn");c.waitWindow("UIAllianceMainTable",5000);}
    AllianceMenu.open(context,4,"Alliance Gifts");c.waitWindow("UIAllianceGift",5000);
   }
   for(int tab:new int[]{1,2}){
    selectTab(context,tab);
    AllianceGiftReader.Snapshot before=reader.read();if(before.tab!=tab)throw new IOException("Gift tab did not settle");TreeSet<String> ids=before.pending();context.event(id(),AllianceGiftPolicy.name(tab)+" gifts available: "+ids.size());evidence.put(before.json());
    if(context.preview||ids.isEmpty())continue;if(!before.claimable)return result(MaintenanceResult.Outcome.BLOCKED,"Claim All is not confirmed for "+AllianceGiftPolicy.name(tab),evidence,claimed);
    pending=context.begin(id(),before.period(),tab==1?"common":"rare",before.json());AllianceGiftReader.Snapshot fresh=reader.read();if(!fresh.claimable||!fresh.period().equals(before.period()))throw new IOException("Gift eligibility changed before input");
    context.input.action(new JSONObject().put("action","ui-tap").put("path",AllianceGiftPolicy.VIEW+"get_all_btn").put("allianceGiftGuild",fresh.guild).put("allianceGiftTab",tab));
    long until=System.currentTimeMillis()+30000;AllianceGiftReader.Snapshot after=null;boolean verified=false;
    while(System.currentTimeMillis()<until){context.input.pause(300);after=reader.read();if(after.tab!=tab||!after.guild.equals(before.guild))throw new IOException("Gift context changed");boolean all=true;for(String id:ids){AllianceGiftReader.Gift g=after.gifts.get(id);if(g==null||!AllianceGiftPolicy.received(0,g.state,g.received)){all=false;break;}}if(all&&!after.busy){verified=true;break;}}
    if(!verified)throw new IOException("Gift receipt missing for selected IDs");context.store.verified(context.uid,pending,System.currentTimeMillis(),after.json());pending=null;claimed+=ids.size();evidence.put(after.json());
   }
   return result(context.preview?MaintenanceResult.Outcome.PREVIEW:claimed>0?MaintenanceResult.Outcome.COMPLETED:MaintenanceResult.Outcome.NOTHING_TO_DO,context.preview?"Alliance Gifts preview; no claims":"Alliance gifts verified; collected "+claimed,evidence,claimed);
  }catch(InterruptedException e){throw e;}catch(Exception e){if(pending!=null){context.store.uncertain(context.uid,pending,e.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Gift attempt saved; no automatic retry: "+e.getMessage(),0);}return result(MaintenanceResult.Outcome.FAILED,"Alliance Gifts stopped after "+claimed+" verified gifts: "+e.getMessage(),evidence,claimed);}
  finally{context.active();closeKnown(context,"UIAllianceGift",AllianceGiftPolicy.VIEW+"close_btn",2);closeKnown(context,"UIAllianceMainTable",AllianceHelpPolicy.MAIN+"_closeBtn",1);}

 }
 void selectTab(MaintenanceContext context,int tab)throws Exception{
  for(int attempt=0;attempt<3;attempt++){
   if(selected(context,tab))return;context.input.tapControl(AllianceGiftPolicy.VIEW+"toogles/#"+tab);long until=System.currentTimeMillis()+2000;
   while(System.currentTimeMillis()<until){if(selected(context,tab))return;context.input.pause(150);}
  }throw new IOException("Gift tab did not settle; no claim sent for that tab");
 }
 boolean selected(MaintenanceContext context,int tab)throws Exception{context.active();try(GameMemory m=new GameMemory(context.controller.cache)){if(!m.open("UIAllianceGift")||m.state.getInt("modalWindowCount")!=2)throw new IOException("Gift navigation context changed");long view=m.path(AllianceGiftPolicy.VIEW.substring(0,AllianceGiftPolicy.VIEW.length()-1));return GameMemory.number(view,"tabIndex")==tab&&GameMemory.number(view,"toogleIndex")==tab;}}
 void closeKnown(MaintenanceContext context,String window,String path,int count)throws Exception{
  for(int attempt=0;attempt<3;attempt++){boolean open;try(GameMemory m=new GameMemory(context.controller.cache)){open=m.open(window);if(!open)return;if(m.state.getInt("modalWindowCount")!=count)return;}context.input.tapControl(path);long until=System.currentTimeMillis()+2000;while(System.currentTimeMillis()<until){if(!context.controller.open(window))return;context.input.pause(150);}}
  throw new IOException("Known alliance window did not close: "+window);
 }
 MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,JSONArray snapshots,int claimed){Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshots",snapshots.toString());evidence.put("claimed",Integer.toString(claimed));return new MaintenanceResult(outcome,reason,System.currentTimeMillis()+900000,evidence);}
}
