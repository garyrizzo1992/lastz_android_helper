package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Discovery navigation only: no explicit claim/read-all/delete; visiting tabs may mark mail read. */
final class MailInspectionFeature implements MaintenanceFeature {
 public String id(){return "mail_inspection";}public int priority(){return 40;}
 public boolean permitsInput(String action,String path,boolean preview){return action.equals("ui-tap")&&MailPolicy.inspectionControl(path);}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  AutomationController c=context.controller;JSONArray rows=new JSONArray();
  try{
   if(!c.open("UIMailNew4")){context.base();context.input.tapControl(MailPolicy.ENTRY);c.waitWindow("UIMailNew4",5000);}
   MailReader reader=new MailReader(context);
   for(int index=1;index<=6;index++){
    boolean selected=false;for(int attempt=0;attempt<3&&!selected;attempt++){
     context.active();try(GameMemory m=new GameMemory(c.cache)){if(!m.open("UIMailNew4")||m.state.getInt("modalWindowCount")!=1)throw new IOException("Mail navigation context changed");long group=m.path(MailPolicy.VIEW+"_toggles/#"+index+"/_mailChannelType");if(GameMemory.number(group,"id")!=index||GameMemory.number(group,"type")!=MailPolicy.type(index))throw new IOException("Mail tab definition changed");selected=GameMemory.number(m.path(MailPolicy.VIEW+"ctrl"),"currentTab")==MailPolicy.type(index);}
     if(!selected){context.input.tapControl(MailPolicy.VIEW+"_toggles/#"+index);long until=System.currentTimeMillis()+2000;while(System.currentTimeMillis()<until){try(GameMemory m=new GameMemory(c.cache)){selected=GameMemory.number(m.path(MailPolicy.VIEW+"ctrl"),"currentTab")==MailPolicy.type(index);}if(selected)break;context.input.pause(150);}}
    }if(!selected)throw new IOException("Mail tab did not settle");JSONObject row=reader.inspect(index);rows.put(row);context.event(id(),row.getString("tab")+": "+row.getInt("loadedHeaders")+" loaded, "+row.getInt("ordinaryCandidates")+" ordinary candidates, "+row.getInt("specialPending")+" special pending");
   }
   Map<String,String> evidence=new LinkedHashMap<>();evidence.put("tabs",rows.toString());return new MaintenanceResult(MaintenanceResult.Outcome.PREVIEW,"Mail inspection only; no claims or mailbox completion recorded",0,evidence);
  }finally{context.active();for(int attempt=0;attempt<3;attempt++){if(!c.open("UIMailNew4"))break;try(GameMemory m=new GameMemory(c.cache)){if(m.state.getInt("modalWindowCount")!=1)break;}context.input.tapControl(MailPolicy.VIEW+"_btnClose");long until=System.currentTimeMillis()+2000;while(c.open("UIMailNew4")&&System.currentTimeMillis()<until)context.input.pause(150);}}
 }
}
