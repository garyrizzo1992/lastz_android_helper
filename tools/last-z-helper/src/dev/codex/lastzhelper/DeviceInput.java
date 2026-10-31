package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import java.util.concurrent.*;import org.json.*;
final class DeviceInput implements AutoCloseable {
 static DeviceInput active;
 static final class Scope implements AutoCloseable{public void close()throws Exception{closeActive();}}
 Process session;boolean sessionCompatible=false;Thread reader;int injectorPid;String injectorStart;final ConcurrentHashMap<String,JSONObject> receipts=new ConcurrentHashMap<>();final StringBuffer sessionLog=new StringBuffer();
 final String cache;final File stop,injector,agent,dir;final int pid;final String identity;long lastIdentityCheck;
 interface Guard{void verify()throws Exception;}Guard guard,combatGuard;
 interface RequestGuard{void verify(JSONObject request)throws Exception;}RequestGuard requestGuard;
 DeviceInput(String cache,File stop,File injector,File agent,File dir)throws Exception{
  this(cache,stop,injector,agent,dir,false);
 }
 DeviceInput(String cache,File stop,File injector,File agent,File dir,boolean allowBattle)throws Exception{
  this.cache=cache;this.stop=stop;this.injector=injector;this.agent=agent;this.dir=dir;
  StateProbe.stopSignal=stop;StateProbe.cancelCheck();
  StateProbe.pinForeground();JSONObject s=StateProbe.snapshot(cache);
  boolean ready=s.getInt("sceneId")==1||s.getInt("sceneId")==2;
  if(!ready&&allowBattle)try(GameMemory m=new GameMemory(cache)){ready=m.open("UIParkourBattleLose")||m.open("UIParkourBattleWin");}
  if(!s.optBoolean("gameStarted")||!ready)throw new IOException("Wait for the selected game to load; no other window was opened");
  pid=s.getInt("pid");identity=s.getString("processStart");
  if(active!=null)throw new IOException("An input session is already active");active=this;
  System.out.println(new JSONObject().put("event","progress").put("message","Using active account: "+s.getString("accountName")+" ("+s.getString("accountUid")+")").put("accountUid",s.getString("accountUid")).put("pid",pid));System.out.flush();
 }
 void check()throws Exception{check(false);}
 void check(boolean forceIdentity)throws Exception{
  if(stop.exists())throw new InterruptedException("Stopped by user");
  if(guard!=null)guard.verify();
  if(!identity.equals(StateProbe.start(String.valueOf(pid))))throw new IOException("Game restarted; run again");
  if(forceIdentity||System.currentTimeMillis()-lastIdentityCheck>=500){StateProbe.verifyPinned();lastIdentityCheck=System.currentTimeMillis();}
 }
 void pause(long ms)throws Exception{long end=System.currentTimeMillis()+ms;while(System.currentTimeMillis()<end){check();Thread.sleep(Math.min(100,Math.max(1,end-System.currentTimeMillis())));}}
 static String exec(long timeout,String... command)throws Exception{
  Process p=new ProcessBuilder(command).redirectErrorStream(true).start();ByteArrayOutputStream out=new ByteArrayOutputStream();
  Thread drain=new Thread(()->{try(InputStream in=p.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1)if(out.size()<131072)out.write(b,0,n);}catch(Exception ignored){}});drain.start();
  if(!p.waitFor(timeout,TimeUnit.SECONDS)){p.destroyForcibly();p.waitFor(2,TimeUnit.SECONDS);throw new IOException("Command timed out: "+command[0]);}
  drain.join(1000);String s=out.toString("UTF-8");if(p.exitValue()!=0)throw new IOException("Command failed: "+command[0]+": "+s);return s;
 }
 static int childPid(Process process)throws Exception{for(Class<?> type=process.getClass();type!=null;type=type.getSuperclass())try{java.lang.reflect.Field field=type.getDeclaredField("pid");field.setAccessible(true);return field.getInt(process);}catch(NoSuchFieldException ignored){}throw new IOException("Cannot identify owned injector process");}
 void killOwnedInjector(int child,String childStart)throws Exception{
  if(child<=1||child==pid||child==android.os.Process.myPid())throw new IOException("Invalid injector cleanup target");
  if(!new File("/proc/"+child).exists())return;
  String stat=StateProbe.text("/proc/"+child+"/stat");String[] fields=stat.substring(stat.lastIndexOf(')')+2).split("\\s+");
  if(!injector.getPath().equals(StateProbe.cmdline(""+child))||!childStart.equals(StateProbe.start(""+child))||Integer.parseInt(fields[1])!=android.os.Process.myPid())throw new IOException("Injector cleanup ownership changed; stopped");
  exec(3,"/system/bin/kill","-9",""+child);
 }
 void foreground()throws Exception{check();JSONObject info=action(new JSONObject().put("action","inspect"));if(!info.optBoolean("compatible"))throw new IOException("Unsupported active game surface: "+info);}
 JSONObject action(JSONObject args)throws Exception{
  if(requestGuard!=null)requestGuard.verify(args);
  if("ui-tap".equals(args.optString("action"))&&CombatPolicy.protectedControl(args.optString("path")+"/"+args.optString("child"),args.optString("label"))){if(combatGuard==null)throw new IOException("Combat input requires explicit Gaarix attack mode");combatGuard.verify();}
  check(true);args.put("nonce",UUID.randomUUID().toString()).put("accountUid",StateProbe.pinnedUid).put("manager","0x"+Long.toHexString(StateProbe.pinnedManager));String nonce=args.getString("nonce");
  if(session==null){
   JSONObject hello=new JSONObject(args.toString()).put("action","inspect").put("nonce",UUID.randomUUID().toString());
   session=new ProcessBuilder(injector.getPath(),"-i","-p",String.valueOf(pid),"-s",agent.getPath(),"-P",hello.toString()).redirectErrorStream(true).start();
   injectorPid=childPid(session);injectorStart=StateProbe.start(""+injectorPid);
   reader=new Thread(()->{try(BufferedReader in=new BufferedReader(new InputStreamReader(session.getInputStream(),"UTF-8"))){String line;while((line=in.readLine())!=null){synchronized(sessionLog){sessionLog.append(line).append('\n');if(sessionLog.length()>16384)sessionLog.delete(0,sessionLog.length()-16384);}int at=line.indexOf("LASTZ_RECEIPT:");if(at>=0)try{JSONObject o=new JSONObject(line.substring(at+14));if(receipts.size()<64)receipts.put(o.getString("nonce"),o);}catch(Exception ignored){}}}catch(Exception ignored){}});reader.setDaemon(true);reader.start();
   JSONObject inspection=await(hello.getString("nonce"),true);requireSuccess(inspection);
   if(!inspection.optBoolean("compatible",false))throw new IOException("Unsupported active game surface: "+inspection);
   sessionCompatible=true;
  }
  if(!sessionCompatible)throw new IOException("Input session compatibility is not confirmed");
  send(args);JSONObject result=await(nonce,true);requireSuccess(result);
  check();return result;
 }
 void send(JSONObject args)throws Exception{if(!session.isAlive())throw new IOException("Input session ended: "+sessionLog);session.getOutputStream().write((args.toString()+"\n").getBytes("UTF-8"));session.getOutputStream().flush();}
 JSONObject await(String nonce,boolean guarded)throws Exception{long end=System.currentTimeMillis()+18000;while(System.currentTimeMillis()<end){JSONObject result=receipts.remove(nonce);if(result!=null)return result;if(!session.isAlive())break;if(guarded)check();Thread.sleep(40);}throw new IOException("No matching input receipt: "+sessionLog);}
 static final class PreDispatchRejected extends IOException{final JSONObject receipt;PreDispatchRejected(JSONObject receipt)throws Exception{super("Input rejected before dispatch: "+receipt.optString("error")+(receipt.has("controlPath")?" ["+receipt.optString("controlPath")+"]":""));this.receipt=new JSONObject(receipt.toString());}}
 void requireSuccess(JSONObject result)throws Exception{if(!result.optBoolean("ok")){if(result.has("inputDispatched")&&!result.optBoolean("inputDispatched",true)&&result.optString("phase").equals("native_pre_dispatch")&&(result.optString("requestAction").equals("ui-tap")||result.optString("requestAction").equals("training-collect")))throw new PreDispatchRejected(result);String error=result.optString("error");if(error.contains("focus"))throw new IOException("Keep the selected Last Z game open and close startup popups, then run again.");throw new IOException("Input rejected: "+error);}}
 public void close()throws Exception{
  try{if(session==null)return;
   if(session.isAlive()){
    // Only one detach per run, after the final Java callback has returned.
    try{JSONObject bye=new JSONObject().put("action","shutdown").put("nonce",UUID.randomUUID().toString()).put("accountUid",StateProbe.pinnedUid).put("manager","0x"+Long.toHexString(StateProbe.pinnedManager));send(bye);await(bye.getString("nonce"),false);}catch(Exception ignored){}
    session.destroy();if(!session.waitFor(15,TimeUnit.SECONDS)){killOwnedInjector(injectorPid,injectorStart);session.waitFor(3,TimeUnit.SECONDS);throw new IOException("Input detach timed out; stopped");}
   }
   reader.join(1000);if(session.exitValue()!=0)throw new IOException("Input cleanup unconfirmed; exit "+session.exitValue());
  }finally{active=null;}
 }
 static void closeActive()throws Exception{if(active!=null)active.close();}
 JSONObject controlBounds(String path)throws Exception{return action(new JSONObject().put("action","ui-bounds").put("path",path));}
 void tapChild(String path,String child)throws Exception{action(new JSONObject().put("action","ui-tap").put("path",path).put("child",child));pause(450);}
 void tapLabel(String path,String label,int parent)throws Exception{action(new JSONObject().put("action","ui-tap").put("path",path).put("label",label).put("parent",parent));pause(450);}
 void tapControl(String path)throws Exception{tapControl(path,450);}
 void tapControl(String path,int settleMs)throws Exception{if(settleMs<0||settleMs>2000)throw new IOException("Control settle bound");try(GameMemory m=new GameMemory(cache)){String[] parts=path.split("/");if(parts.length<4||!m.open(parts[2])||(parts[2].equals("MainUI_SU")&&m.state.getInt("modalWindowCount")!=0))throw new IOException("UI window context changed");if(parts[2].equals("UILWTrainScene")&&(m.state.getInt("modalWindowCount")!=1||GameMemory.number(m.path("UIManagerInstance/windows/UILWTrainScene/View"),"curTab")!=1))throw new IOException("Unexpected Trucks dialog/tab; no input sent");}action(new JSONObject().put("action","ui-tap").put("path",path));if(settleMs>0)pause(settleMs);}
 void tapWorldChannel(int index)throws Exception{if(index<1)throw new IOException("Invalid World share row");action(new JSONObject().put("action","ui-tap").put("path","UIManagerInstance/windows/UIPositionShare/View/ScrollView").put("child","Viewport/Content/"+index+"/ImgBg/ImageShare").put("expectedLabel","World"));pause(450);}
 String clipboard()throws Exception{return action(new JSONObject().put("action","clipboard")).getString("text");}
 void mapMove(String direction)throws Exception{mapAction(direction,0);pause(800);}
 void mapZoom(double amount)throws Exception{mapAction("zoom",amount);pause(1400);}
 void mapAction(String kind,double amount)throws Exception{try(GameMemory m=new GameMemory(cache)){if(m.state.getInt("sceneId")!=2||m.state.getInt("modalWindowCount")!=0)throw new IOException("Clear World view required for map gesture");}action(new JSONObject().put("action","map-gesture").put("kind",kind).put("amount",amount));}
 void mapTap(int x,int y)throws Exception{action(new JSONObject().put("action","map-tap").put("tileX",x).put("tileY",y));pause(450);}
 void scrollControl(String path,String direction)throws Exception{action(new JSONObject().put("action","ui-swipe").put("path",path).put("child","Viewport").put("direction",direction));pause(500);}
 void back()throws Exception{action(new JSONObject().put("action","back"));pause(500);}
 void numericControl(String field,int value)throws Exception{
  if(!field.matches("server|x|y")||value<0||value>9999)throw new IOException("Numeric control bound");String root="UIManagerInstance/windows/UISearchMonster/View/gotoWorld";tapControl(root+"/"+field+"_input");pause(250);
  try(GameMemory m=new GameMemory(cache)){if(!m.open("UISearchMonster")||m.state.getInt("modalWindowCount")!=1)throw new IOException("Coordinate editor context changed");}
  String text=String.valueOf(value),before=action(new JSONObject().put("action","text").put("kind","number").put("text",text).put("readOnly",true)).getString("text");
  action(new JSONObject().put("action","text").put("kind","number").put("text",text).put("expected",before).put("selectAll",true));checkNativeFocus();exec(5,"/system/bin/input","text",text);action(new JSONObject().put("action","text").put("kind","number").put("text",text).put("expected",text));checkNativeFocus();exec(5,"/system/bin/input","keyevent","66");pause(400);
  try(GameMemory m=new GameMemory(cache)){if(!m.open("UISearchMonster")||GameMemory.number(m.path(root),field)!=value)throw new IOException("Coordinate field did not accept "+field+"="+value);}
 }
 void checkNativeFocus()throws Exception{
  check(true);
 }
 File screenshot(String name)throws Exception{check();File out=new File(dir,name);exec(5,"/system/bin/screencap","-p",out.getPath());return out;}
}
