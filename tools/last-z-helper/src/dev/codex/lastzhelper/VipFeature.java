package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Bounded two-category free reward workflow. Never presses Activate or a paid offer. */
final class VipFeature implements MaintenanceFeature {
 public String id(){return "vip";}public int priority(){return 10;}
 public boolean permitsInput(String action,String path,boolean preview){if(action.equals("ui-dismiss"))return path.equals("UIManagerInstance/windows/UIWorldPoint/View/bg_go");return action.equals("ui-tap")&&VipPolicy.allowedControl(path)&&!(preview&&(path.endsWith("/box_btn")||path.endsWith("/free_btn")));}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  AutomationController c=context.controller;VipReader reader=new VipReader(context);int claimed=0;String pending=null;
  try{
   if(c.open("UIVip"))dismissKnownReward(context);
   if(!c.open("UIVip")){context.base();context.input.tapControl(VipReader.ENTRY);c.waitWindow("UIVip",5000);}
   VipReader.Snapshot snapshot=reader.read();context.event(id(),"VIP points: "+snapshot.points.state+"; Daily Freebies: "+snapshot.freebies.state);
   if(context.preview)return result(MaintenanceResult.Outcome.PREVIEW,"VIP preview: points "+snapshot.points.state+", freebies "+snapshot.freebies.state,0,snapshot,0);
   for(String target:new String[]{"daily_points","daily_freebies"}){
    snapshot=reader.read();VipReader.Unit unit=snapshot.unit(target);if(unit.state==VipPolicy.State.BLOCKED)return result(MaintenanceResult.Outcome.BLOCKED,"VIP state is ambiguous for "+target+"; no claim sent",System.currentTimeMillis()+900000,snapshot,claimed);
    if(unit.state==VipPolicy.State.COOLDOWN)continue;
    // Later eligibility periods follow the last VERIFIED game cooldown, not an assumed
    // local reset hour or a cache timestamp that may stay unchanged across daily resets.
    JSONObject previous=context.store.latestVerified(context.uid,id(),target);long previousReady=0;
    if(previous!=null){JSONObject prior=previous.getJSONObject("after").getJSONObject(target.equals("daily_points")?"points":"freebies");previousReady=VipPolicy.nextDue(prior.getLong("observedMs"),prior.getLong("cooldownSeconds"));}
    pending=context.begin(id(),VipPolicy.period(System.currentTimeMillis(),previousReady,snapshot.revision),target,snapshot.json());context.active();
    VipReader.Snapshot fresh=reader.read();if(fresh.level!=snapshot.level||fresh.unit(target).state!=VipPolicy.State.CLAIMABLE)throw new IOException("VIP eligibility changed before commit");
    context.input.action(new JSONObject().put("action","ui-tap").put("path",VipReader.VIEW+unit.button).put("vipClaimLevel",fresh.level));context.input.pause(450);long until=System.currentTimeMillis()+12000;VipReader.Snapshot after=null;
    while(System.currentTimeMillis()<until){after=reader.read();if(after.unit(target).state==VipPolicy.State.COOLDOWN)break;context.input.pause(250);}
    if(after==null||after.unit(target).state!=VipPolicy.State.COOLDOWN)throw new IOException("VIP claim outcome not confirmed");
    context.store.verified(context.uid,pending,System.currentTimeMillis(),after.json());pending=null;claimed++;
    dismissKnownReward(context);try(GameMemory m=new GameMemory(c.cache)){if(m.state.getInt("modalWindowCount")!=1)return result(MaintenanceResult.Outcome.BLOCKED,"VIP claim confirmed; reward overlay needs inspection before the next claim",System.currentTimeMillis()+900000,after,claimed);}
   }
   snapshot=reader.read();if(snapshot.points.state!=VipPolicy.State.COOLDOWN||snapshot.freebies.state!=VipPolicy.State.COOLDOWN)throw new IOException("Both VIP categories are not confirmed on cooldown");
   return result(claimed>0?MaintenanceResult.Outcome.COMPLETED:MaintenanceResult.Outcome.NOTHING_TO_DO,"Both VIP daily rewards verified on cooldown; collected "+claimed,snapshot.nextDue(),snapshot,claimed);
  }catch(InterruptedException e){throw e;}catch(Exception e){
   if(pending!=null){context.store.uncertain(context.uid,pending,e.toString());return MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"VIP attempt saved; no automatic retry: "+e.getMessage(),0);}
   return MaintenanceResult.of(MaintenanceResult.Outcome.FAILED,"VIP check stopped: "+e.getMessage(),System.currentTimeMillis()+900000);
  }finally{
   context.active();try(GameMemory m=new GameMemory(c.cache)){if(m.open("UIVip")&&m.state.getInt("modalWindowCount")==1)context.input.tapControl(VipReader.VIEW+"close_btn");}
  }
 }
 void dismissKnownReward(MaintenanceContext context)throws Exception{AutomationController c=context.controller;if(!c.open("UIVIPRewardPopUp"))return;try(GameMemory m=new GameMemory(c.cache)){if(!m.open("UIVip")||m.state.getInt("modalWindowCount")!=2)throw new IOException("Unexpected VIP reward context");}context.input.tapControl("UIManagerInstance/windows/UIVIPRewardPopUp/View/return_btn");long until=System.currentTimeMillis()+5000;while(c.open("UIVIPRewardPopUp")&&System.currentTimeMillis()<until)context.input.pause(150);if(c.open("UIVIPRewardPopUp"))throw new IOException("VIP reward popup did not close");}
 MaintenanceResult result(MaintenanceResult.Outcome outcome,String reason,long due,VipReader.Snapshot snapshot,int claimed)throws Exception{Map<String,String> evidence=new LinkedHashMap<>();evidence.put("snapshot",snapshot.json().toString());evidence.put("claimed",Integer.toString(claimed));return new MaintenanceResult(outcome,reason,due,evidence);}
}
