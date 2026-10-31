package dev.codex.lastzhelper;
import java.io.*;import java.nio.file.*;import org.json.*;
/** Real atomic ledger files; simulated game/STOP faults, never device input. */
public final class BoomerEngineTests {
 static final String UID="2059765822000064",OTHER="2059770776000064",ID="boomer_auto_join";
 static int checks;static Path root;
 static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 static final class Fixture implements BoomerEngine.Journal,BoomerEngine.World {
  final File file;final MaintenanceStore store;long time=1000000,expiry;int reads,activations,bits=3;
  boolean enabled,stopped,uncertainFails;String fault="",beginFault="",verifyFault="";
  Fixture(String name)throws Exception{Path dir=Files.createDirectory(root.resolve(name));file=dir.resolve("maintenance-state.json").toFile();store=new MaintenanceStore(file);}
  public String uid(){return UID;}
  public boolean unresolved()throws Exception{return store.unresolved(UID,ID);}
  public JSONObject previous()throws Exception{return store.latestVerified(UID,ID,"activate");}
  public String begin(String period,long now,JSONObject before)throws Exception{
   if(beginFault.equals("disk"))throw new IOException("journal unavailable");
   String key=store.begin(UID,ID,period,"activate",now,before);
   if(beginFault.equals("stop-after-save"))throw new InterruptedException("STOP after durable intent");
   if(beginFault.equals("lost-result"))throw new IOException("intent saved but return lost");
   return key;
  }
  public void verified(String key,long now,JSONObject after)throws Exception{
   if(verifyFault.equals("disk"))throw new IOException("receipt save unavailable");
   store.verified(UID,key,now,after);
   if(verifyFault.equals("lost-result"))throw new IOException("receipt saved but return lost");
  }
  public void uncertain(String key,String reason)throws Exception{if(uncertainFails)throw new IOException("uncertainty save unavailable");store.uncertain(UID,key,reason);}
  public long now(){return time;}
  public void active()throws Exception{
   if(stopped)throw new InterruptedException("STOP");
   if(reads==2&&activations==0){
    if(fault.equals("stop-before-intent")&&!unresolved())throw new InterruptedException("STOP before intent");
    if(fault.equals("stop-after-intent")&&unresolved())throw new InterruptedException("STOP after intent");
    if(fault.equals("uid-change-before-intent")&&!unresolved())throw new IOException("character changed");
   }
  }
  JSONObject snapshot()throws Exception{
   return new JSONObject().put("accountUid",UID).put("activityId","40005").put("state",enabled?"ACTIVE":"INACTIVE").put("expiryMs",enabled?expiry:0).put("timerSeconds",enabled?(expiry-time)/1000:-2).put("observedMs",time).put("options",new JSONArray().put(new JSONObject().put("type",1).put("selected",(bits&1)!=0)).put(new JSONObject().put("type",2).put("selected",(bits&2)!=0)));
  }
  public JSONObject read()throws Exception{
   reads++;if(activations>0&&fault.equals("missing-receipt"))throw new IOException("receipt unavailable");
   JSONObject s=snapshot();
   if(fault.equals("blocked"))s.put("state","BLOCKED");
   if(fault.equals("stale"))s.put("observedMs",time-20000);
   if(fault.equals("wrong-uid")||(fault.equals("uid-change-after-input")&&activations>0))s.put("accountUid",OTHER);
   if(fault.equals("wrong-event"))s.put("activityId","40006");
   if(fault.equals("fresh-options-change")&&reads==2)s.getJSONArray("options").getJSONObject(1).put("selected",false);
   if(fault.equals("after-options-change")&&activations>0)s.getJSONArray("options").getJSONObject(1).put("selected",false);
   if(fault.equals("stop-after-proof")&&activations>0)stopped=true;
   return s;
  }
  public void activate(JSONObject before)throws Exception{
   MaintenanceStore durable=reload();expect(durable.unresolved(UID,ID),"intent must be on disk before input");
   JSONObject ops=durable.account(UID).getJSONObject("operations"),op=null;int pending=0;java.util.Iterator<String> keys=ops.keys();while(keys.hasNext()){JSONObject candidate=ops.getJSONObject(keys.next());if(candidate.getString("status").equals("pending")){pending++;op=candidate;}}expect(pending==1,"exactly one pending activation, older verified periods retained");expect(op.getJSONObject("before").getLong("activationRequestedMs")==time,"durable request timestamp precedes input");
   activations++;enabled=!fault.equals("no-ack");expiry=time+(fault.equals("short-expiry")?600000:BoomerPolicy.DURATION);
   if(fault.equals("stop-in-input")){stopped=true;throw new InterruptedException("STOP during input");}
   if(fault.equals("lost-ack"))throw new IOException("input receipt lost");
  }
  public void pause(long millis)throws Exception{active();time+=millis;}
  MaintenanceStore reload()throws Exception{return new MaintenanceStore(file);}
  MaintenanceResult run(boolean preview)throws Exception{return BoomerEngine.run(this,this,preview);}
  void restartIsFenced()throws Exception{
   Fixture next=this;int oldReads=reads,oldActivations=activations;fault="";beginFault="";verifyFault="";stopped=false;
   MaintenanceResult result=BoomerEngine.run(new Ledger(reload()),next,false);
   expect(result.outcome==MaintenanceResult.Outcome.UNCERTAIN,"reopened process must remain fenced");
   expect(reads==oldReads&&activations==oldActivations,"fence must precede read/input, never replay");
  }
 }
 static final class Ledger implements BoomerEngine.Journal {
  final MaintenanceStore s;Ledger(MaintenanceStore s){this.s=s;}
  public String uid(){return UID;}
  public boolean unresolved()throws Exception{return s.unresolved(UID,ID);}
  public JSONObject previous()throws Exception{return s.latestVerified(UID,ID,"activate");}
  public String begin(String period,long now,JSONObject before)throws Exception{return s.begin(UID,ID,period,"activate",now,before);}
  public void verified(String key,long now,JSONObject after)throws Exception{s.verified(UID,key,now,after);}
  public void uncertain(String key,String reason)throws Exception{s.uncertain(UID,key,reason);}
 }
 static JSONObject only(MaintenanceStore s)throws Exception{JSONObject ops=s.account(UID).getJSONObject("operations");expect(ops.length()==1,"one activation operation only");return ops.getJSONObject(ops.keys().next());}
 static void stopped(Fixture f)throws Exception{boolean caught=false;try{f.run(false);}catch(InterruptedException expected){caught=true;}expect(caught,"STOP propagates to the controller");}
 public static void main(String[]args)throws Exception{
  root=args.length==0?Files.createTempDirectory("lastz-boomer-engine-"):Files.createTempDirectory(Paths.get(args[0]),"engine-");
  Fixture f=new Fixture("preview");expect(f.run(true).outcome==MaintenanceResult.Outcome.PREVIEW,"inactive preview");expect(!f.file.exists()&&f.activations==0,"preview has no ledger or input");
  f=new Fixture("active");f.enabled=true;f.expiry=f.time+3600000;MaintenanceResult r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.NOTHING_TO_DO&&r.nextDueMs==f.expiry,"active retains exact expiry");expect(!f.file.exists()&&f.activations==0,"already-active never starts an operation");
  f=new Fixture("no-options");f.bits=0;expect(f.run(false).outcome==MaintenanceResult.Outcome.BLOCKED,"no selected joins is blocked");expect(!f.file.exists()&&f.activations==0,"no-choice block before journal/input");
  for(String fault:new String[]{"blocked","stale","wrong-uid","wrong-event","fresh-options-change","uid-change-before-intent"}){
   f=new Fixture(fault);f.fault=fault;r=f.run(false);expect(r.outcome==(fault.equals("blocked")?MaintenanceResult.Outcome.BLOCKED:MaintenanceResult.Outcome.FAILED),"pre-input rejection: "+fault);expect(!f.file.exists()&&f.activations==0,"no pre-input mutation: "+fault);
  }
  f=new Fixture("stop-before-intent");f.fault="stop-before-intent";stopped(f);expect(!f.file.exists()&&f.activations==0,"STOP before journal is clean");
  f=new Fixture("stop-in-journal-return");f.beginFault="stop-after-save";stopped(f);expect(f.reload().unresolved(UID,ID)&&f.activations==0,"STOP after durable write stays pending");f.restartIsFenced();
  f=new Fixture("stop-after-intent");f.fault="stop-after-intent";stopped(f);expect(f.reload().unresolved(UID,ID)&&f.activations==0,"STOP at final input boundary stays pending");f.restartIsFenced();
  f=new Fixture("stop-in-input");f.fault="stop-in-input";stopped(f);expect(f.activations==1&&f.reload().unresolved(UID,ID),"STOP after dispatch retains unresolved intent");f.restartIsFenced();
  for(String fault:new String[]{"lost-ack","missing-receipt","short-expiry","after-options-change","uid-change-after-input","no-ack"}){
   f=new Fixture(fault);f.fault=fault;r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.UNCERTAIN&&r.nextDueMs==0,"unconfirmed commit is uncertain: "+fault);expect(f.activations==1&&f.reload().unresolved(UID,ID),"uncertain persisted: "+fault);expect(only(f.reload()).getString("status").equals("uncertain"),"uncertain status on disk: "+fault);f.restartIsFenced();
  }
  f=new Fixture("journal-failure");f.beginFault="disk";r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.FAILED&&r.nextDueMs==f.time+BoomerPolicy.RETRY,"pre-input failure uses15minute retry");expect(f.activations==0&&!f.file.exists(),"failed journal prohibits input");
  f=new Fixture("receipt-write-failure");f.verifyFault="disk";r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.UNCERTAIN&&f.reload().unresolved(UID,ID),"failed receipt save cannot complete");f.restartIsFenced();
  f=new Fixture("intent-return-failure");f.beginFault="lost-result";r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.FAILED&&f.activations==0,"lost intent return sends no input");expect(f.reload().unresolved(UID,ID),"saved intent survives lost local key");f.restartIsFenced();
  f=new Fixture("receipt-return-failure");f.verifyFault="lost-result";boolean failed=false;try{f.run(false);}catch(IOException expected){failed=true;}expect(failed,"verified receipt cannot be downgraded to uncertain on lost return");expect(only(f.reload()).getString("status").equals("verified"),"verified disk receipt survives caller failure");f.verifyFault="";expect(BoomerEngine.run(new Ledger(f.reload()),f,false).outcome==MaintenanceResult.Outcome.NOTHING_TO_DO&&f.activations==1,"lost receipt return cannot replay input");
  f=new Fixture("uncertainty-save-failure");f.fault="lost-ack";f.uncertainFails=true;failed=false;try{f.run(false);}catch(IOException expected){failed=true;}expect(failed&&f.activations==1,"uncertainty write failure propagates after input");expect(only(f.reload()).getString("status").equals("pending"),"earlier durable pending record remains the fence");f.restartIsFenced();
  f=new Fixture("complete");r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.COMPLETED&&r.nextDueMs==f.expiry,"exact activation completes at actual expiry");expect(only(f.reload()).getString("status").equals("verified"),"verified receipt persists");int count=f.activations;expect(f.run(false).outcome==MaintenanceResult.Outcome.NOTHING_TO_DO&&f.activations==count,"normal repeat does not reactivate");only(f.reload());
  long oldExpiry=f.expiry;f.time=oldExpiry+1000;f.enabled=false;r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.COMPLETED&&f.activations==2,"eligible natural-expiry renewal");expect(f.reload().account(UID).getJSONObject("operations").has(ID+":after_"+oldExpiry+":activate"),"renewal identity follows verified prior expiry");
  f=new Fixture("stop-after-proof");f.fault="stop-after-proof";r=f.run(false);expect(r.outcome==MaintenanceResult.Outcome.COMPLETED,"receipt is saved before caller observes late STOP");expect(only(f.reload()).getString("status").equals("verified"),"late STOP cannot erase conclusive proof");boolean late=false;try{f.active();}catch(InterruptedException expected){late=true;}expect(late,"caller cleanup still observes STOP");
  f.stopped=false;f.fault="";expect(BoomerEngine.run(new Ledger(f.reload()),f,false).outcome==MaintenanceResult.Outcome.NOTHING_TO_DO&&f.activations==1,"new request after late STOP does not replay");
  f=new Fixture("other-account");String prior=f.store.begin(OTHER,"vip","sample","reward",f.time,new JSONObject());f.store.verified(OTHER,prior,f.time,new JSONObject().put("retained",true));String original=f.store.account(OTHER).toString();f.run(false);expect(f.reload().account(OTHER).toString().equals(original),"another UID's records are preserved");
  System.out.println("Auto Boomer transaction faults: "+checks+" checks passed; real durable files, simulated input/STOP only");
 }
}
