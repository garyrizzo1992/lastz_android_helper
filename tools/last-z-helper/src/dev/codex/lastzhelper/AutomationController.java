package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.*;import org.json.*;
/** On-device worker. Target memory is read-only; actions use Android input. */
public final class AutomationController {
 final File dir,stop;File progress;boolean bountyGroup;final String cache;final DeviceInput input;final ShareLedger ledger;ShareLedger attacks;final BountyReader bounties;
 final boolean dryRun;int sent=0,planned=0,scanned=0;String mode;int ownerPid;String ownerStart;JSONObject alertedTruck;
 boolean logRefreshes;TruckRefreshLog refreshLog;
 boolean diagnosticScreenshots=false,truckFilterVerified=false;
 DeadStateStore deadStateStore;
 boolean diagnosticDefeatTest; boolean twoFragmentTest; int diagnosticMinimumSlots=2;
 final Set<String> drySeen=new HashSet<>();int dryScanSteps=0,skipTruckState=0,attacked=0,sendLimit=0;long attackPowerLimit=TruckRules.LIMIT;String truckMode="truck-world";
 String classifyValues(int quality,int slots,long power){return classifyValues(quality,slots,power,-1);}
 String classifyValues(int quality,int slots,long power,int boxes){if(diagnosticDefeatTest&&truckMode.equals("truck-attack"))return quality>=1&&quality<=5&&slots>=0&&power>=500000000L?"ALERT_TARGET":"SKIP";return twoFragmentTest&&truckMode.equals("truck-attack")?TruckPolicy.classifySelectedTest(quality,slots,power,attackPowerLimit,diagnosticMinimumSlots):TruckPolicy.classify(truckMode,quality,slots,power,attackPowerLimit,boxes);}
 String classify(JSONObject truck)throws Exception{return classifyValues(truck.getInt("quality"),truck.getInt("orangeFragmentSlots"),truck.getLong("power"),truck.optInt("moduleBoxIcons",-1));}
 JSONObject truckSnapshot()throws Exception{ensureTruckFilter();JSONObject s=TruckProbe.snapshot(cache,attackPowerLimit);JSONArray a=s.getJSONArray("candidates");for(int i=0;i<a.length();i++)a.getJSONObject(i).put("decision",classify(a.getJSONObject(i)));return s;}
 AutomationController(File dir,File injector,File agent,File stop,boolean dryRun,int ownerPid)throws Exception{
  this(dir,injector,agent,stop,dryRun,ownerPid,false);
 }
 AutomationController(File dir,File injector,File agent,File stop,boolean dryRun,int ownerPid,boolean allowBattle)throws Exception{
  this.dir=dir;this.stop=stop;this.dryRun=dryRun;this.ownerPid=ownerPid;cache=new File(dir,"probe-cache.txt").getPath();progress=new File(dir,dryRun?"bounty-progress-dry.json":"bounty-progress.json");
  if(ownerPid>0)ownerStart=StateProbe.start(String.valueOf(ownerPid));
  input=new DeviceInput(cache,stop,injector,agent,dir,allowBattle);input.guard=()->{if(ownerPid>0&&(!ownerStart.equals(StateProbe.start(String.valueOf(ownerPid)))||!StateProbe.cmdline(String.valueOf(ownerPid)).equals("dev.codex.lastzhelper")))throw new InterruptedException("Helper process ended; automation stopped");};
  input.combatGuard=()->{if(!CombatPolicy.allowed(truckMode,StateProbe.pinnedUid)||dryRun)throw new IOException("Plunder/Fight is allowed only in Attack 3+ on Gaarix mode");};
  ledger=new ShareLedger(new File(dir,"world-shares.json"));bounties=new BountyReader(cache);attacks=new ShareLedger(new File(dir,"truck-attacks.json"));
 }
 void event(String message)throws Exception{input.check();System.out.println(new JSONObject().put("event","progress").put("mode",mode).put("message",message).put("scanned",scanned).put("shared",sent).put("attacked",attacked).put("dryRun",dryRun));System.out.flush();}
 void closeShare()throws Exception{input.tapControl("UIManagerInstance/windows/UIPositionShare/View/close_btn");}
 void dismissPoint()throws Exception{if(!open("UIWorldPoint"))return;input.action(new JSONObject().put("action","ui-dismiss").put("path","UIManagerInstance/windows/UIWorldPoint/View/bg_go"));input.pause(800);if(open("UIWorldPoint"))throw new IOException("Point popup did not dismiss");}
 int worldShareRow()throws Exception{try(GameMemory m=new GameMemory(cache)){if(!m.open("UIPositionShare"))throw new IOException("Share menu missing");String room=GameMemory.string(m.path("ChatManager2/Instance/Room"),"countryRoomId");int found=0;for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("UIManagerInstance/windows/UIPositionShare/View/list")))if((v.tag&15)==5&&room.equals(GameMemory.string(v.raw,"roomId"))){if(found!=0)throw new IOException("Duplicate World share row");found=Integer.parseInt(v.key.substring(1));}if(found==0)throw new IOException("World share room missing");return found;}}
 boolean open(String name)throws Exception{try(GameMemory m=new GameMemory(cache)){return m.open(name);}}
 void worldReady()throws Exception{
  for(int attempt=0;attempt<6;attempt++)try(GameMemory m=new GameMemory(cache)){
   int scene=m.state.getInt("sceneId");if(scene!=1&&scene!=2)throw new IOException("Wait for the base/world scene");
   if(m.state.getInt("modalWindowCount")==0)break;
   if(m.open("UIChatPrivateSet"))throw new IOException("Close the private options popup before starting");
   else if(m.open("UISettingBlock"))input.tapControl("UIManagerInstance/windows/UISettingBlock/View/close_btn");
   else if(m.open("UIPositionShareConfirm"))input.tapControl("UIManagerInstance/windows/UIPositionShareConfirm/View/close_btn");
   else if(m.open("UIPositionShare"))closeShare();
   else if(m.open("UILWTrainScene"))input.tapControl("UIManagerInstance/windows/UILWTrainScene/View/closeBtn");
   else if(m.open("UIChatNew"))closeChat();
   else if(m.open("UISearchMonster"))input.tapControl("UIManagerInstance/windows/UISearchMonster/View/close_btn");
   else if(m.open("UIWorldPoint"))dismissPoint();
   else throw new IOException("Close the in-game menu before starting");
  }
  if(StateProbe.snapshot(cache).getInt("modalWindowCount")!=0)throw new IOException("Menu did not close; stopped");
  JSONObject state=StateProbe.snapshot(cache);if(state.getInt("sceneId")==1){input.tapControl("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn");input.pause(1000);}
  state=StateProbe.snapshot(cache);if(state.getInt("sceneId")!=2||state.getInt("modalWindowCount")!=0)throw new IOException("World view was not confirmed");
 }
 double height()throws Exception{try(GameMemory m=new GameMemory(cache)){return GameMemory.decimal(m.path("SceneManager/World/Camera"),"_lastHeight");}}
 void zoom()throws Exception{
  for(int i=0;i<9;i++){
   double h=height();if(Math.abs(h-BountyReader.ZOOM)<=1)return;
   double delta=Math.abs(1/Math.sqrt(h)-1/Math.sqrt(BountyReader.ZOOM))*5;delta=Math.max(.0002,Math.min(.18,delta));
   input.mapZoom(h<BountyReader.ZOOM?delta:-delta);
  }throw new IOException("Zoom did not converge; stopped for review");
 }
 Set<String> stateErrors()throws Exception{JSONArray a=input.action(new JSONObject().put("action","state-errors")).getJSONArray("messages");Set<String> out=new HashSet<>();for(int i=0;i<a.length();i++)out.add(a.getString(i));return out;}
 DeadStateStore deadStates()throws Exception{if(deadStateStore==null)deadStateStore=new DeadStateStore(new File(dir,"dead-states.json"));return deadStateStore;}
 boolean go(int server,int x,int y)throws Exception{
  if(deadStates().contains(server)){event("Skipping remembered dead state "+server+"; no search opened");return false;}
  worldReady();if(height()>180)input.mapZoom(-.24);
  input.tapControl("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/search_btn");if(!open("UISearchMonster"))throw new IOException("Coordinate search did not open");
  input.numericControl("server",server);input.numericControl("x",x);input.numericControl("y",y);Set<String> beforeErrors=stateErrors();for(int stale=0;!beforeErrors.isEmpty()&&stale<12;stale++){input.pause(200);beforeErrors=stateErrors();}if(!beforeErrors.isEmpty())throw new IOException("Previous state error has not cleared; no new search sent");input.tapControl("UIManagerInstance/windows/UISearchMonster/View/gotoWorld/btn");
  for(int i=0;i<12;i++){
   Set<String> errors=stateErrors();errors.removeAll(beforeErrors);if(!errors.isEmpty()){for(String message:errors)if(deadStates().record(server,message,System.currentTimeMillis()))event("State "+server+" confirmed dead and saved for future runs");event("State "+server+" unavailable; metadata message confirmed");if(open("UISearchMonster"))input.tapControl("UIManagerInstance/windows/UISearchMonster/View/close_btn");return false;}
   JSONObject s=bounties.snapshot();if(s.getInt("server")==server&&Math.abs(s.getInt("x")-x)<=1&&Math.abs(s.getInt("y")-y)<=1&&!open("UISearchMonster"))return true;
   input.pause(400);
  }throw new IOException("State/coordinate change not confirmed. No further input sent.");
 }
 void capital(int server)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   int count=0;for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("DataCenter/WorldAllianceCityDataManager/allAllianceCityList")))if((v.tag&15)==5&&GameMemory.number(v.raw,"serverId")==server&&GameMemory.number(v.raw,"cityLevel")==7){long xy=GameMemory.f(v.raw,"posV2");if(Math.abs(GameMemory.number(xy,"x")-496)>8||Math.abs(GameMemory.number(xy,"y")-496)>8)throw new IOException("Capital location changed");count++;}
   if(count!=1)throw new IOException("Capital metadata not confirmed for state "+server);
  }
 }
 JSONObject selectedBounty(String id)throws Exception{try(GameMemory m=new GameMemory(cache)){if(!m.open("UIWorldPoint"))return null;long ctrl=m.path("UIManagerInstance/windows/UIWorldPoint/Ctrl");return id.equals(Long.toString(GameMemory.number(ctrl,"uuid")))?new JSONObject().put("id",id):null;}}
 JSONObject selectedTruck()throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   if(!m.open("UILWTrainScene"))return null;long view=m.path("UIManagerInstance/windows/UILWTrainScene/View"),obj=GameMemory.f(view,"objInfoPanel");
   if(!GameMemory.bool(obj,"activeSelf"))return null;long train=GameMemory.optional(view,"selectTrain");if(train==0)return null;
   long data=GameMemory.f(GameMemory.f(view,"infoPanel"),"trainData");String id=Long.toString(GameMemory.number(train,"uuid"));if(!id.equals(Long.toString(GameMemory.number(data,"uuid"))))throw new IOException("Selected truck identity conflict");
   return new JSONObject().put("id",id);
  }
 }
 void validateTruckShareParam(JSONObject target,long param)throws Exception{
  long manager=GameMemory.f(GameMemory.f(StateProbe.globalsAt(StateProbe.pinnedManager),"DataCenter"),"LWTrainDataManager");if(!TruckHidePolicy.enabled(StateProbe.u8(StateProbe.findField(manager,"filterLocalServer")+8)))throw new IOException("Hide trucks of this state was switched off; no share sent");
  if(!target.getString("id").equals(Long.toString(GameMemory.number(param,"trainUuid"))))throw new IOException("Truck share UUID mismatch");
  int[] cargo=TruckCargo.payload(GameMemory.string(param,"rewardStr"));int quality=(int)GameMemory.number(param,"quality");long power=GameMemory.number(param,"power");
  String decision=TruckPolicy.classify(truckMode,quality,cargo[0],power,attackPowerLimit,cargo[1]);
  if(cargo[0]!=target.getInt("orangeFragmentSlots")||cargo[1]!=target.getInt("moduleBoxIcons")||power!=target.getLong("power")||quality!=target.getInt("quality")||(!decision.equals("WORLD_SHARE_ELIGIBLE")&&!decision.equals("PRIVATE_SHARE_ELIGIBLE")))throw new IOException("Truck share rewards changed or no longer qualify");
 }
 long validateShare(JSONObject target,boolean truck)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   if(!m.open("UIPositionShare"))throw new IOException("Share menu missing");long p=m.path("UIManagerInstance/windows/UIPositionShare/View/chat_data_param");
   if(truck){
    String id=Long.toString(GameMemory.number(p,"trainUuid"));if(!id.equals(target.getString("id")))throw new IOException("Truck share UUID mismatch");
    validateTruckShareParam(target,p);
    long msg=GameMemory.optional(p,"msg");if(msg!=0&&!StateProbe.luaString(msg).isEmpty())throw new IOException("Share note must be empty");return 604;
   }
   if(!GameMemory.string(p,"dispatchTaskUuid").equals(target.getString("uuid"))||GameMemory.number(p,"sid")!=target.getInt("server")||GameMemory.number(p,"x")!=target.getInt("x")||GameMemory.number(p,"y")!=target.getInt("y"))throw new IOException("Bounty share destination mismatch");
   int boxes=BountyRules.itemQuantity(GameMemory.string(p,"dispatchStealRewards"),252006);if(boxes!=12&&boxes!=15)throw new IOException("Bounty live reward is not 12 or 15 boxes");return 630;
  }
 }
 boolean share(JSONObject target,boolean truck)throws Exception{
  if(truck&&!TruckRules.shareAllowed(target.getLong("serverId"),skipTruckState)){event("Skipped World share for truck from state "+skipTruckState);return false;}
  String id=target.getString(truck?"id":"uuid"),key=(truck?"truck:":"bounty:")+id;if(ledger.contains(key)||drySeen.contains(key))return false;
  int post=(int)validateShare(target,truck);int worldIndex=worldShareRow();input.action(new JSONObject().put("action","ui-bounds").put("path","UIManagerInstance/windows/UIPositionShare/View/ScrollView").put("child","Viewport/Content/"+worldIndex+"/ImgBg/ImageShare").put("expectedLabel","World"));
  if(dryRun){drySeen.add(key);planned++;event("Preview: qualifying "+(truck?"truck":"bounty")+" verified; no post sent");closeShare();return false;}
  WorldReceipt receipt=new WorldReceipt(cache);long baseline=receipt.baseline();JSONObject record=new JSONObject(target.toString()).put("kind",truck?"truck":"bounty").put("channel","World").put("note","");
  ledger.pending(key,record);if(diagnosticScreenshots)input.screenshot((truck?"truck-":"bounty-")+id+"-prepared.png");input.tapWorldChannel(worldIndex);
  if(open("UIPositionShareConfirm")){
   validateShare(target,truck);
   try(GameMemory m=new GameMemory(cache)){long chat=m.path("UIManagerInstance/windows/UIPositionShareConfirm/View/chat_data"),param=GameMemory.f(chat,"param");String room=GameMemory.string(m.path("ChatManager2/Instance/Room"),"countryRoomId");if(!room.equals(GameMemory.string(chat,"roomId"))||GameMemory.number(chat,"post")!=post||!(truck?Long.toString(GameMemory.number(param,"trainUuid")):GameMemory.string(param,"dispatchTaskUuid")).equals(id))throw new IOException("World confirmation identity changed");if(truck)validateTruckShareParam(target,param);}
   JSONObject draft=input.action(new JSONObject().put("action","ui-bounds").put("path","UIManagerInstance/windows/UIPositionShareConfirm/View/input_field").put("readText",true));if(!draft.getString("inputText").isEmpty())throw new IOException("Share note is not empty; no Send pressed");
   input.tapControl("UIManagerInstance/windows/UIPositionShareConfirm/View/btn_yes");
  }
  if(diagnosticScreenshots)input.screenshot((truck?"truck-":"bounty-")+id+"-receipt.png");long end=System.currentTimeMillis()+15000;
  while(System.currentTimeMillis()<end){long seq=receipt.read(baseline,post,id);if(seq>baseline){ledger.verified(key,seq);sent++;event("World share verified: "+(truck?"truck ":"bounty ")+id);return true;}input.pause(400);}
  throw new IOException("World outcome uncertain. Attempt saved and will not be retried automatically.");
 }
 void configureBounties(boolean group){bountyGroup=group;progress=new File(dir,BountyRoute.checkpoint(group,dryRun));}
 String bountyKey(String id){return BountyRoute.key(bountyGroup,GroupTruckSender.ROOM,id);}
 void scanBounties(int server)throws Exception{
  JSONObject snapshot=bounties.snapshot();if(snapshot.getInt("server")!=server||snapshot.getInt("lod")!=4||Math.abs(snapshot.getDouble("height")-BountyReader.ZOOM)>3)throw new IOException("State/approved zoom changed");
  int returnX=snapshot.getInt("x"),returnY=snapshot.getInt("y");JSONArray list=snapshot.getJSONArray("bounties");scanned+=list.length();
  for(int i=0;i<list.length();i++){
   JSONObject v=list.getJSONObject(i);String key=bountyKey(v.getString("uuid"));
   if(v.getInt("server")!=server||ledger.contains(key)||drySeen.contains(key)||!BountyRules.qualifies(v.getInt("boxes"),v.getInt("taken"),v.getInt("maximum"))||v.getLong("finishTime")>snapshot.getLong("gameTime"))continue;
   input.check();if(!go(server,v.getInt("x"),v.getInt("y")))throw new IOException("State became unavailable");
   JSONObject fresh=bounties.find(v.getString("uuid"));if(fresh==null||fresh.getInt("taken")>=fresh.getInt("maximum"))continue;
   JSONObject projected=input.action(new JSONObject().put("action","map-point").put("tileX",v.getInt("x")).put("tileY",v.getInt("y")));input.mapTap(v.getInt("x"),v.getInt("y"));if(selectedBounty(v.getString("uuid"))==null)throw new IOException("Selected bounty does not match memory");
   fresh=bounties.find(v.getString("uuid"));if(fresh==null||fresh.getInt("taken")>=fresh.getInt("maximum")){dismissPoint();continue;}
   input.tapControl("UIManagerInstance/windows/UIWorldPoint/View/btn_share");if(bountyGroup)new GroupBountySender(this).send(fresh);else share(fresh,false);if(open("UIPositionShare"))closeShare();dismissPoint();
   if(sendLimit>0&&sent>=sendLimit)break;
  }
  if(list.length()>0){JSONObject current=bounties.snapshot();if(current.getInt("x")!=returnX||current.getInt("y")!=returnY||Math.abs(height()-BountyReader.ZOOM)>1){if(!go(server,returnX,returnY))throw new IOException("Cannot restore scan area");zoom();}}
  event("State "+server+": capital area scanned");
 }
 void moveMap(String direction)throws Exception{JSONObject before=bounties.snapshot();input.mapMove(direction);JSONObject after=bounties.snapshot();if(before.getInt("server")!=after.getInt("server")||before.getInt("x")==after.getInt("x")&&before.getInt("y")==after.getInt("y"))throw new IOException("Map movement not confirmed; stopped before repeat scan");}
 void bountyRun(int start,int end,boolean resume,int limit)throws Exception{
  mode=bountyGroup?BountyRoute.GROUP:BountyRoute.WORLD;int next=start;if(resume&&progress.exists()){JSONObject p=new JSONObject(StateProbe.text(progress.getPath()));if(!p.optBoolean("complete")&&p.optInt("start")==start&&p.optInt("end")==end)next=Math.max(start,p.optInt("nextState",start));}
  int completed=0;String[] route=MapSweep.DIRECTIONS;
  for(int server=next;server<=end;server++){
   input.check();ShareLedger.atomic(progress,new JSONObject().put("start",start).put("end",end).put("nextState",server).put("complete",false));
   if(deadStates().contains(server)){event("Skipping remembered dead state "+server+"; no search opened");}
   else{event("Opening state "+server+" capital");if(go(server,500,500)){capital(server);zoom();scanBounties(server);int steps=0;for(String move:route){if(dryRun&&dryScanSteps>0&&steps>=dryScanSteps)break;moveMap(move);scanBounties(server);steps++;}}}
   ShareLedger.atomic(progress,new JSONObject().put("start",start).put("end",end).put("nextState",server+1).put("complete",server==end));completed++;if(limit>0&&completed>=limit)break;
  }
  event("Bounty run finished");
 }
 Set<String> rendered()throws Exception{try(GameMemory m=new GameMemory(cache)){Set<String> ids=new HashSet<>();for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("UIManagerInstance/windows/UILWTrainScene/View/trainList")))if((v.tag&15)==5)ids.add(Long.toString(GameMemory.number(v.raw,"uuid")));return ids;}}
 boolean trucksHideEnabled()throws Exception{
  try(GameMemory m=new GameMemory(cache)){long manager=m.path("DataCenter/LWTrainDataManager");return TruckHidePolicy.enabled(StateProbe.u8(StateProbe.findField(manager,"filterLocalServer")+8));}
 }
 JSONObject truckHideControl()throws Exception{
  JSONObject state=input.action(new JSONObject().put("action","ui-bounds").put("path",TruckHidePolicy.PATH).put("stateOnly",true));
  return state;
 }
 void ensureTruckFilter()throws Exception{
  boolean saved=trucksHideEnabled();if(saved&&truckFilterVerified)return;
  try(GameMemory m=new GameMemory(cache)){if(!m.open("UILWTrainScene")||m.state.getInt("modalWindowCount")!=1||GameMemory.number(m.path("UIManagerInstance/windows/UILWTrainScene/View"),"curTab")!=1)throw new IOException("Others' Trucks required to verify state filter");}
  long until=System.nanoTime()+5000000000L;boolean requested=false,clicked=false;JSONObject state;
  while(true){
   state=truckHideControl();saved=trucksHideEnabled();Boolean checked=state.has("toggleOn")&&!state.isNull("toggleOn")?Boolean.valueOf(state.getBoolean("toggleOn")):null;
   if(TruckHidePolicy.ready(saved,checked,state.optBoolean("active"),state.optBoolean("interactable"))){
    if(!TruckHidePolicy.shouldClick(saved,checked.booleanValue())){truckFilterVerified=true;if(clicked)event("Hide trucks of this state enabled and verified");return;}
    if(!requested){requested=true;
     try{input.action(new JSONObject().put("action","ui-tap").put("path",TruckHidePolicy.PATH).put("ensureTruckHide",true));clicked=true;}
     catch(DeviceInput.PreDispatchRejected rejected){if(!rejected.receipt.optString("error").equals("Error: Hide trucks filter is already enabled")||!trucksHideEnabled())throw rejected;}
    }
   }
   if(System.nanoTime()>=until)throw new IOException("Hide trucks of this state not ready after 5 seconds; saved="+saved+", checked="+checked+", active="+state.optBoolean("active")+", interactable="+state.optBoolean("interactable")+"; stopped without another click");
   input.pause(100);
  }
 }
 void ensureTrucks()throws Exception{
  boolean shareOpen,ready=false;
  try(GameMemory m=new GameMemory(cache)){
   if(m.open("UIPositionShareConfirm"))throw new IOException("Close the unfinished share confirmation before restarting");shareOpen=m.open("UIPositionShare");
   if(!shareOpen&&m.open("UILWTrainScene")){if(GameMemory.number(m.path("UIManagerInstance/windows/UILWTrainScene/View"),"curTab")!=1||m.state.getInt("modalWindowCount")!=1)throw new IOException("Open Others' Trucks and close other dialogs first");ready=true;}
  }
  if(ready){ensureTruckFilter();return;}
  if(shareOpen)closeShare();
  if(!open("UILWTrainScene")){truckFilterVerified=false;worldReady();if(height()>180)input.mapZoom(-.24);input.tapControl("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/truckBtn");}
  long until=System.nanoTime()+5000000000L;
  while(System.nanoTime()<until){try(GameMemory m=new GameMemory(cache)){if(m.open("UILWTrainScene")){if(m.state.getInt("modalWindowCount")!=1)throw new IOException("Unexpected dialog while opening Trucks");ready=GameMemory.number(m.path("UIManagerInstance/windows/UILWTrainScene/View"),"curTab")==1;}}if(ready){ensureTruckFilter();return;}input.pause(100);}
  throw new IOException("Open Others' Trucks first");
 }
 boolean openTruck(JSONObject truck)throws Exception{
  JSONObject current=selectedTruck();if(current!=null&&current.getString("id").equals(truck.getString("id")))return true;String path=null;
  try(GameMemory m=new GameMemory(cache)){for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("UIManagerInstance/windows/UILWTrainScene/View/trainCells")))if((v.tag&15)==5){long train=GameMemory.optional(v.raw,"train");if(train!=0&&Long.toString(GameMemory.number(train,"uuid")).equals(truck.getString("id"))){if(path!=null)throw new IOException("Duplicate truck touch cell");path="UIManagerInstance/windows/UILWTrainScene/View/trainCells/"+v.key+"/btn";}}}
  if(path==null)return false;
  try{input.tapControl(path);}catch(DeviceInput.PreDispatchRejected rejected){JSONObject r=rejected.receipt;if(!TruckPolicy.unavailableCell(r.optBoolean("inputDispatched",true),r.optString("phase"),r.optString("requestAction"),r.optString("error")))throw rejected;event("Truck cell hidden, disabled or offscreen before input; refreshing the list");return false;}
  current=selectedTruck();return current!=null&&current.getString("id").equals(truck.getString("id"));
 }
 void truckShare()throws Exception{input.tapControl("UIManagerInstance/windows/UILWTrainScene/View/infoPanel/shareBtn");}
 void waitMapTruck(JSONObject truck)throws Exception{
  long until=System.nanoTime()+10000000000L;
  while(System.nanoTime()<until){input.check();try(GameMemory m=new GameMemory(cache)){if(m.open("UIPVEScene")||m.state.getInt("modalWindowCount")>1)throw new IOException("Unexpected dialog while locating truck");if(m.open("UIWorldPoint")){long view=m.path("UIManagerInstance/windows/UIWorldPoint/View"),obj=GameMemory.optional(view,"train_obj"),data=obj==0?0:GameMemory.optional(obj,"data");if(data!=0&&truck.getString("id").equals(Long.toString(GameMemory.number(data,"uuid"))))return;}}input.pause(100);}
  throw new TruckChanged("Target truck did not finish loading on the map");
 }
 void verifyMapTruck(JSONObject truck,String decision)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   if(!m.open("UIWorldPoint")||m.open("UIPVEScene")||m.state.getInt("modalWindowCount")!=1)throw new IOException("Expected the unstarted truck map preview");long data=m.path("UIManagerInstance/windows/UIWorldPoint/View/train_obj/data");
   if(!truck.getString("id").equals(Long.toString(GameMemory.number(data,"uuid"))))throw new IOException("Map truck identity changed");
   long power=GameMemory.number(data,"power");int slots=TruckProbe.fragmentSlots(data,"baseGoods")[0]+TruckProbe.fragmentSlots(data,"extraGoods")[0],quality=(int)GameMemory.number(data,"quality");
   if(power!=truck.getLong("power")||slots!=truck.getInt("orangeFragmentSlots")||quality!=truck.getInt("quality")||!classifyValues(quality,slots,power).equals(decision))throw new TruckChanged("Map truck rewards/power changed or no longer qualify");
  }
 }
 void groupTruckShare(JSONObject truck)throws Exception{JSONObject selected=selectedTruck();if(selected==null||!truck.getString("id").equals(selected.getString("id"))||!classify(truck).equals("PRIVATE_SHARE_ELIGIBLE"))throw new IOException("Selected truck no longer qualifies for group share");event("Opening truck Share button");truckShare();validateShare(truck,true);}
 void refreshTrucks()throws Exception{
  long until=System.nanoTime()+3000000000L;
  while(true)try{input.tapControl("UIManagerInstance/windows/UILWTrainScene/View/refreshBtn",0);return;}catch(IOException e){String message=e.getMessage();boolean beforeInput=message!=null&&(message.contains("Control is outside visible screen")||message.contains("Exported control is hidden")||message.contains("Exported control is disabled"));if(!beforeInput||System.nanoTime()>=until)throw e;input.pause(100);}
 }
 void waitRefreshed(Map<String,String> old)throws Exception{
  long until=System.nanoTime()+10000000000L;
  while(System.nanoTime()<until){input.pause(100);try{if(!old.equals(TruckProbe.identities(TruckProbe.readList(cache))))return;}catch(TruckProbe.ListLoading loading){/* Keep waiting only while the same validated Trucks window is loading. */}}
  throw new IOException("Truck refresh did not produce a new list; stopped");
 }
 void closeChat()throws Exception{input.tapControl("UIManagerInstance/windows/UIChatNew/View/close_btn");}

 void waitWindow(String name,long timeout)throws Exception{long end=System.currentTimeMillis()+timeout;while(System.currentTimeMillis()<end){if(open(name))return;input.pause(150);}throw new IOException(name+" did not open; stopped");}
 void requireWorldRoom()throws Exception{try(GameMemory m=new GameMemory(cache)){if(!m.open("UIChatNew"))throw new IOException("Chat is not open");long v=m.path("UIManagerInstance/windows/UIChatNew/View");String expected=GameMemory.string(m.path("ChatManager2/Instance/Room"),"countryRoomId");if(GameMemory.number(v,"curTab")!=5||!expected.equals(GameMemory.string(GameMemory.f(v,"curRoomData"),"roomId")))throw new IOException("World chat channel not confirmed");}}
 void requireBattle(JSONObject truck)throws Exception{try(GameMemory m=new GameMemory(cache)){if(!m.open("UIPVEScene"))throw new IOException("Truck battle screen missing");long view=m.path("UIManagerInstance/windows/UIPVEScene/View"),data=m.path("UIManagerInstance/windows/UIPVEScene/View/levelParam/truckData");if(GameMemory.number(view,"levelId")!=25003||GameMemory.number(view,"rightPower")!=truck.getLong("power")||!Long.toString(GameMemory.number(data,"uuid")).equals(truck.getString("id")))throw new IOException("Truck battle identity/power mismatch");}}
 int heroCount()throws Exception{try(GameMemory m=new GameMemory(cache)){int count=0;for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("UIManagerInstance/windows/UIPVEScene/Ctrl/curHeroes")))if(v.key.startsWith("#")&&v.raw>0)count++;return count;}}
 static final class TruckChanged extends IOException{TruckChanged(String message){super(message);}}
 void skipChangedTruck(JSONObject truck,String reason)throws Exception{String key="attack:"+truck.getString("id");JSONObject record=attacks.data.getJSONObject(key);if(record.has("battleStartMs"))throw new IOException("Battle may have started; cannot mark it skipped");record.put("status","skipped-before-battle").put("reason",reason).put("skippedMs",System.currentTimeMillis());ShareLedger.atomic(attacks.file,attacks.data);if(open("UIWorldPoint"))dismissPoint();event("Truck rewards/power changed; skipped before battle");}
 void attackTruck(JSONObject truck)throws Exception{
  if(dryRun)throw new IOException("Dry run cannot attack");String id=truck.getString("id"),key="attack:"+id;
  JSONObject selected=selectedTruck();if(selected==null||!selected.getString("id").equals(id)||!classify(truck).equals("ALERT_TARGET")||!TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid))throw new IOException("Truck no longer qualifies for attack on Gaarix");
  attacks.pending(key,new JSONObject(truck.toString()).put("kind","truck-attack"));event("Opening attack for truck "+id);input.tapControl("UIManagerInstance/windows/UILWTrainScene/View/infoPanel/goBtn");
  try{waitMapTruck(truck);attackFromMap(truck);}catch(TruckChanged changed){skipChangedTruck(truck,changed.getMessage());}
 }
 void attackFromMap(JSONObject truck)throws Exception{
  String id=truck.getString("id"),key="attack:"+id;if(dryRun||!TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid)||!classify(truck).equals("ALERT_TARGET"))throw new IOException("Map attack requires a qualifying truck on active Gaarix");
  JSONObject record=attacks.data.getJSONObject(key);if(!record.optString("status").equals("pending")||record.has("battleStartMs"))throw new IOException("Attack already started or completed; no retry");String path=null;
  verifyMapTruck(truck,"ALERT_TARGET");
  try(GameMemory m=new GameMemory(cache)){
   if(!m.open("UIWorldPoint"))throw new IOException("Map truck preview closed before attack");long view=m.path("UIManagerInstance/windows/UIWorldPoint/View");
   for(TruckDiscoveryProbe.Value v:GameMemory.rows(GameMemory.f(view,"buildBtnCells")))if((v.tag&15)==5&&GameMemory.bool(v.raw,"activeSelf")&&"AttackTrain".equals(GameMemory.string(v.raw,"__name"))){if(path!=null)throw new IOException("Duplicate active truck attack button");path="UIManagerInstance/windows/UIWorldPoint/View/buildBtnCells/"+v.key+"/btn";}
  }
  if(path==null)throw new IOException("Live AttackTrain control missing");input.tapControl(path);waitWindow("UIPVEScene",15000);fightFromSetup(truck);
 }
 void fightFromSetup(JSONObject truck)throws Exception{
  String id=truck.getString("id"),key="attack:"+id;JSONObject record=attacks.data.getJSONObject(key);
  if(dryRun||!TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid)||!classify(truck).equals("ALERT_TARGET")||!record.optString("status").equals("pending")||record.has("battleStartMs"))throw new IOException("Battle continuation requires an unstarted qualifying attack on Gaarix");
  requireBattle(truck);input.pause(800);int heroes=heroCount();
  if(heroes==0){requireBattle(truck);input.tapControl("UIManagerInstance/windows/UIPVEScene/View/onekeyFillHeroBtn");}
  if(heroCount()!=5)throw new IOException("Select five heroes for the truck battle, then run again");requireBattle(truck);
  try(GameMemory m=new GameMemory(cache)){long ownPower=GameMemory.number(m.path("UIManagerInstance/windows/UIPVEScene/View"),"leftPower");if(ownPower<=0)throw new IOException("Attack team has no power");if(diagnosticDefeatTest&&truck.getLong("power")<=ownPower)throw new IOException("Defeat test requires defender above actual formation power");}
  record.put("battleStartMs",System.currentTimeMillis());ShareLedger.atomic(attacks.file,attacks.data);input.tapControl("UIManagerInstance/windows/UIPVEScene/View/btn_start");long until=System.currentTimeMillis()+120000;String outcome=null;
  while(System.currentTimeMillis()<until){if(open("UIParkourBattleLose")){outcome="defeat";break;}if(open("UIParkourBattleWin")){outcome="victory";break;}input.pause(500);}
  if(outcome==null)throw new IOException("Battle result not confirmed; attack attempt saved");attacks.attackComplete(key,outcome);attacked++;input.screenshot("truck-attack-"+id+"-"+outcome+".png");
  returnFromBattle();event("Truck attack completed: "+outcome);
 }
 void returnFromBattle()throws Exception{
  long ready=System.currentTimeMillis()+8000;String result=null;while(System.currentTimeMillis()<ready){result=open("UIParkourBattleLose")?"UIParkourBattleLose":open("UIParkourBattleWin")?"UIParkourBattleWin":null;if(result==null)throw new IOException("Battle result changed before closing");try{input.controlBounds("UIManagerInstance/windows/"+result+"/View/"+(result.equals("UIParkourBattleWin")?"btnContinue":"continueTipText"));break;}catch(IOException waiting){if(System.currentTimeMillis()>=ready)throw waiting;input.pause(200);}}input.tapControl("UIManagerInstance/windows/"+result+"/View/"+(result.equals("UIParkourBattleWin")?"btnContinue":"continueTipText"));
  long end=System.currentTimeMillis()+15000;while(System.currentTimeMillis()<end){JSONObject state=StateProbe.snapshot(cache);if(state.getInt("sceneId")==2)break;input.pause(200);}input.pause(1000);ensureTrucks();
 }

 void truckRun(int maxRefreshes)throws Exception{
  if(!TruckPolicy.accountAllowed(truckMode,StateProbe.pinnedUid))throw new IOException(truckMode.equals("truck-attack")?"Attack mode requires the active Gaarix account. No account was opened or switched.":"Send-to-Gaarix mode cannot send to itself. Open a scanning account first.");
  mode=truckMode;if(logRefreshes){refreshLog=new TruckRefreshLog(dir,mode,attackPowerLimit);System.out.println(new JSONObject().put("event","refresh-log").put("path",refreshLog.file.getPath()));System.out.flush();}
  try{ensureTrucks();int refreshes=0;
  while(true){
   input.check();JSONObject snap=truckSnapshot();JSONArray candidates=snap.getJSONArray("candidates");Set<String> visible=rendered();scanned+=snap.getInt("loadedTruckCount");boolean restartList=false;
   if(refreshLog!=null)refreshLog.record(refreshes,snap.getJSONArray("loadedTrucks"),visible);
   for(int i=0;i<candidates.length();i++){
    JSONObject truck=candidates.getJSONObject(i);String decision=truck.getString("decision"),id=truck.getString("id");if(!visible.contains(id)||decision.startsWith("SKIP"))continue;if(decision.equals("UNKNOWN"))throw new IOException("Unknown truck power/rewards; stopped");
    if(decision.equals("WORLD_SHARE_ELIGIBLE")&&(ledger.contains("truck:"+id)||drySeen.contains("truck:"+id)))continue;
    if(decision.equals("WORLD_SHARE_ELIGIBLE")&&!TruckRules.shareAllowed(truck.getLong("serverId"),skipTruckState))continue;
    if(decision.equals("ALERT_TARGET")&&(attacks.contains("attack:"+id)||drySeen.contains("attack:"+id)))continue;
    if(decision.equals("PRIVATE_SHARE_ELIGIBLE")&&(ledger.contains(GroupTruckSender.key(id))||drySeen.contains(GroupTruckSender.key(id))))continue;
    if(!openTruck(truck)){
     event("Could not select truck "+id+"; skipping this list and refreshing if the refresh limit allows");
     break;
    }
    JSONObject current=truckSnapshot();JSONObject fresh=null;JSONArray a=current.getJSONArray("candidates");for(int j=0;j<a.length();j++)if(a.getJSONObject(j).getString("id").equals(id))fresh=a.getJSONObject(j);
    if(fresh==null||!fresh.getString("decision").equals(decision))throw new IOException("Truck changed before action");
    if(decision.equals("ALERT_TARGET")){
     if(dryRun){drySeen.add("attack:"+id);planned++;event("Preview: attack target verified; no attack sent");continue;}
     attackTruck(fresh);if(sendLimit>0&&attacked>=sendLimit)return;restartList=true;break;
    }
    if(decision.equals("PRIVATE_SHARE_ELIGIBLE")){
     try{groupTruckShare(fresh);}catch(TruckChanged changed){drySeen.add(GroupTruckSender.key(id));if(open("UIWorldPoint"))dismissPoint();event("Truck rewards/power changed; skipped before group share");restartList=true;break;}
     new GroupTruckSender(this).send(fresh);if(sendLimit>0&&(sent>=sendLimit||(dryRun&&planned>=sendLimit)))return;restartList=true;break;
    }
    truckShare();if(share(fresh,true)){if(sendLimit>0&&sent>=sendLimit)return;restartList=true;break;}if(open("UIPositionShare"))closeShare();
   }
   if(restartList){ensureTrucks();continue;}
   event("Trucks scanned; refreshes "+refreshes);if(maxRefreshes>=0&&refreshes>=maxRefreshes)return;
   ensureTrucks();Map<String,String> old=TruckProbe.identities(TruckProbe.readList(cache));
   refreshTrucks();refreshes++;waitRefreshed(old);
  }}finally{if(refreshLog!=null)refreshLog.close();}
 }
 public static void main(String[] args){JSONObject result=new JSONObject();try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length!=7)throw new IOException("Expected mode, directory, injector, agent, stop, options, owner PID");
  File dir=new File(args[1]);if(!dir.isDirectory())throw new IOException("Helper directory missing");JSONObject options=new JSONObject(args[5]);boolean dry=options.optBoolean("dryRun",false);int start=options.optInt("start",17),end=options.optInt("end",64);
  if(start<1||end>9999||end<start||end-start>100)throw new IOException("Invalid state range");
  File lockPath=new File("/data/local/tmp/codex-lastz-helper");lockPath.mkdirs();
  try(RandomAccessFile lock=new RandomAccessFile(new File(lockPath,"control.lock"),"rw");FileChannel channel=lock.getChannel();FileLock held=channel.tryLock()){
   if(held==null)throw new IOException("Another controller is active");ControllerOwnership.check();RecoveryGuard.noInjector();try(DisplaySession display=new DisplaySession()){System.out.println(new JSONObject().put("event","progress").put("mode",args[0]).put("message","Checking active game window and character").put("dryRun",dry));System.out.flush();AutomationController c=new AutomationController(dir,new File(args[2]),new File(args[3]),new File(args[4]),dry,Integer.parseInt(args[6]));c.mode=args[0];c.diagnosticScreenshots=options.optBoolean("diagnosticScreenshots",false);c.input.foreground();
   c.attackPowerLimit=1000000L*TruckRules.parsePowerLimit(options.optString("attackPowerM","440"));c.skipTruckState=TruckRules.parseSkipState(options.optString("skipTruckState","0"));c.dryScanSteps=options.optInt("scanSteps",0);if(BountyRoute.known(args[0])){c.configureBounties(BountyRoute.GROUP.equals(args[0]));if(c.bountyGroup)new GroupTruckSender(c).room();c.bountyRun(start,end,options.optBoolean("resume",true),options.optInt("stateLimit",0));}else if(TruckPolicy.known(args[0])){c.truckMode=args[0];c.truckRun(options.optInt("maxRefreshes",-1));}else throw new IOException("Choose a supported truck mode");
   result.put("event","result").put("ok",true).put("mode",c.mode).put("shared",c.sent).put("planned",c.planned).put("scanned",c.scanned).put("attacked",c.attacked).put("dryRun",dry).put("targetFound",c.alertedTruck!=null);if(c.alertedTruck!=null)result.put("truck",c.alertedTruck);}
  }
 }catch(Throwable e){try{result.put("event","result").put("ok",false).put("stopped",e instanceof InterruptedException).put("error",e.toString());}catch(Exception ignored){}System.out.println(result);System.exit(1);}System.out.println(result);}
}
