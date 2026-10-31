package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** One bounded free Help All operation with a durable pre-commit barrier. */
final class AllianceHelpFeature implements MaintenanceFeature {
 public String id(){return "alliance_help";}public int priority(){return 20;}
 public boolean permitsInput(String action,String path,boolean preview){return action.equals("ui-tap")&&AllianceHelpPolicy.allowed(path,preview);}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  AutomationController c=context.controller;String pending=null;AllianceHelpReader reader=new AllianceHelpReader(context);
  try{
   if(!c.open("UIAllianceHelp")){
    if(!c.open("UIAllianceMainTable")){context.base();context.input.tapControl("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/alliance_btn");c.waitWindow("UIAllianceMainTable",5000);}
    AllianceMenu.open(context,3,"Help");c.waitWindow("UIAllianceHelp",5000);
   }
   AllianceHelpReader.Snapshot before=reader.read();context.event(id(),"Alliance pending help: "+before.count+"; points: "+before.points);
   if(context.preview)return result(MaintenanceResult.Outcome.PREVIEW,"Alliance Help preview; pending "+before.count,before);
   if(before.count==0)return result(MaintenanceResult.Outcome.NOTHING_TO_DO,"No pending alliance help",before);
   if(!before.claimable)return result(MaintenanceResult.Outcome.BLOCKED,"Free Help All control is not confirmed",before);
   pending=context.begin(id(),before.period(),"help_all",before.json());AllianceHelpReader.Snapshot fresh=reader.read();
   if(!fresh.claimable||!fresh.period().equals(before.period())||fresh.count!=before.count)throw new IOException("Alliance help changed before input");
   context.input.action(new JSONObject().put("action","ui-tap").put("path",AllianceHelpPolicy.VIEW+"help_btn").put("allianceHelpGuild",fresh.guild).put("allianceHelpCount",fresh.count).put("allianceHelpReset",fresh.reset));long until=System.currentTimeMillis()+12000;AllianceHelpReader.Snapshot after=null;boolean verified=false;
   while(System.currentTimeMillis()<until){context.input.pause(300);after=reader.read();Set<String> added=new HashSet<>(after.handled);added.removeAll(before.handled);if(after.guild.equals(before.guild)&&AllianceHelpPolicy.verified(before.count,after.count,before.points,after.points,added.size())){verified=true;break;}}
   if(!verified)throw new IOException("Alliance help outcome not confirmed");context.store.verified(context.uid,pending,System.currentTimeMillis(),after.json());pending=null;
   return result(MaintenanceResult.Outcome.COMPLETED,"Free Help All verified; pending "+before.count+" -> "+after.count+", points "+before.points+" -> "+after.points,after);
  }catch(InterruptedException e){throw e;}catch(Exception e){if(pending!=null){context.store.uncertain(context.uid,pending,e.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Alliance help saved; no automatic retry: "+e.getMessage(),0);}return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"Alliance help stopped: "+e.getMessage(),System.currentTimeMillis()+900000);}
  finally{context.active();closeKnown(context,"UIAllianceHelp",AllianceHelpPolicy.VIEW+"close_btn",2);closeKnown(context,"UIAllianceMainTable",AllianceHelpPolicy.MAIN+"_closeBtn",1);}

 }
 void closeKnown(MaintenanceContext context,String window,String path,int count)throws Exception{
  for(int attempt=0;attempt<3;attempt++){boolean open;try(GameMemory m=new GameMemory(context.controller.cache)){open=m.open(window);if(!open)return;if(m.state.getInt("modalWindowCount")!=count)return;}context.input.tapControl(path);long until=System.currentTimeMillis()+2000;while(System.currentTimeMillis()<until){if(!context.controller.open(window))return;context.input.pause(150);}}
  throw new IOException("Known alliance window did not close: "+window);
 }
 MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,AllianceHelpReader.Snapshot s)throws Exception{Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",s.json().toString());return new MaintenanceResult(outcome,reason,System.currentTimeMillis()+300000,evidence);}
}
