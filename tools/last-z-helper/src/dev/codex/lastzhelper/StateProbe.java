package dev.codex.lastzhelper;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.json.JSONObject;

/** Root-launched read-only probe. No target memory writes or function calls. */
public final class StateProbe {
 static File stopSignal;
 static void releaseRotationIdentity()throws Exception{
  if(DeviceInput.active!=null||mem!=null)throw new IOException("Cannot release an active game context");
  pinnedPid=pinnedStart=pinnedUid=pinnedName=validatedLibrary=boundCachePath=lastFocusPid=null;
  pinnedManager=pinnedManagerClass=pinnedLuaClass=lastFocusNanos=0;regions=null;fieldSlots.clear();
 }
 static String pinnedPid,pinnedStart,pinnedUid,pinnedName,validatedLibrary,boundCachePath,lastFocusPid;static long pinnedManager,pinnedManagerClass,pinnedLuaClass,lastFocusNanos;
 static void pinForeground()throws Exception{
  if(pinnedPid!=null){findPid();return;}
  long until=System.currentTimeMillis()+2500;String pid="";
  do{pid=focusedPid();if(!pid.isEmpty())try{if(PKG.equals(cmdline(pid))&&text("/proc/"+pid+"/maps").contains("/libil2cpp.so")){pinnedPid=pid;pinnedStart=start(pid);return;}}catch(IOException ignored){}Thread.sleep(100);}while(System.currentTimeMillis()<until);
  throw new IOException("Open the intended Last Z game window and start from floating controls. No other account was selected.");
 }
 static String fieldString(long globals,String path)throws Exception{long t=globals;for(String key:path.split("/"))t=ptr(findField(t,key));return luaString(t);}
 static long globalsAt(long manager)throws Exception{return ptr(ptr(ptr(ptr(ptr(ptr(manager+32)+16)+24)+64)+16)+16);}
 static void account(long globals)throws Exception{
  String uid=fieldString(globals,"ChatManager2/Instance/cur_gameuid"),self=fieldString(globals,"DataCenter/PlayerInfoDataManager/selfPlayerData/uid");
  if(!uid.matches("[0-9]{8,24}")||!uid.equals(self))throw new IOException("Current character identity is not stable; stopped");
  if(pinnedUid!=null&&!pinnedUid.equals(uid))throw new IOException("Character changed from "+pinnedName+"; stopped before further input");
  if(pinnedUid==null){pinnedUid=uid;pinnedName=fieldString(globals,"DataCenter/PlayerInfoDataManager/selfPlayerData/name");}
 }
 static void verifyPinned()throws Exception{
  if(pinnedPid==null||pinnedUid==null||pinnedManager==0)throw new IOException("Game identity is not pinned");
  if(!pinnedStart.equals(start(pinnedPid))||!pinnedPid.equals(focusedPid()))throw new IOException("Selected game window changed or restarted; stopped");
  RandomAccessFile previous=mem;try(RandomAccessFile current=new RandomAccessFile("/proc/"+pinnedPid+"/mem","r")){mem=current;account(globalsAt(pinnedManager));}finally{mem=previous;}
 }
 static void cancelCheck()throws InterruptedException{if(stopSignal!=null&&stopSignal.exists())throw new InterruptedException("Stopped by user");}
 static final String PKG="com.readygo.barrel.gp";
 static final String EXPECTED="310ad5120b508f8063bdc393dc9d605ef6ace7cf83ecf403cdd1dabe7bc2b660";
 static class Region {long start,end,offset;String perms,path;Region(String line){String[] a=line.trim().split("\\s+",6);String[] b=a[0].split("-");start=Long.parseUnsignedLong(b[0],16);end=Long.parseUnsignedLong(b[1],16);perms=a[1];offset=Long.parseLong(a[2],16);path=a.length>5?a[5]:"";}}
 static RandomAccessFile mem; static List<Region> regions;static long deadline;
 static long u64(byte[] b,int i){long x=0;for(int j=7;j>=0;j--)x=(x<<8)|(b[i+j]&255L);return x;}
 static byte[] bytes(long addr,int n)throws Exception {if(addr<=0||n<0||n>1048600)throw new IOException("Invalid read");Perf.read(n);byte[] b=new byte[n];mem.seek(addr);mem.readFully(b);return b;}
 static long ptr(long addr)throws Exception{return u64(bytes(addr,8),0);}
 static int u8(long addr)throws Exception{return bytes(addr,1)[0]&255;}
 static String text(String path)throws Exception{StringBuilder s=new StringBuilder();try(BufferedReader r=new BufferedReader(new FileReader(path))){String l;while((l=r.readLine())!=null)s.append(l).append('\n');}return s.toString().trim();}
 static String cmdline(String pid)throws Exception{try(FileInputStream f=new FileInputStream("/proc/"+pid+"/cmdline")){byte[] b=new byte[256];int n=f.read(b);int k=0;while(k<n&&b[k]!=0)k++;return new String(b,0,k,StandardCharsets.UTF_8);}}
 static String findPid()throws Exception{
  return findPinnedProcess(true);
 }
 static String findPinnedProcess(boolean freshFocus)throws Exception{
  if(pinnedPid==null)pinForeground();
  String focus=!freshFocus&&lastFocusPid!=null&&System.nanoTime()-lastFocusNanos<500000000L?lastFocusPid:focusedPid();
  if(!pinnedStart.equals(start(pinnedPid))||!PKG.equals(cmdline(pinnedPid))||!pinnedPid.equals(focus))throw new IOException("Selected game window changed or restarted; stopped. No fallback account selected.");
  return pinnedPid;
 }
 static String focusedPid()throws Exception{
  long timing=Perf.begin();try{String focus=ProcessWindows.focusedPid(DeviceInput.exec(5,"/system/bin/dumpsys","window"));lastFocusPid=focus;lastFocusNanos=System.nanoTime();return focus;}finally{Perf.end("focusCheck",timing);}
 }
 static String start(String pid)throws Exception{String s=text("/proc/"+pid+"/stat");String[] a=s.substring(s.lastIndexOf(')')+2).split("\\s+");return a[19];}
 static String hash(String path)throws Exception{MessageDigest md=MessageDigest.getInstance("SHA-256");try(InputStream f=new FileInputStream(path)){byte[] b=new byte[1048576];int n;while((n=f.read(b))!=-1)md.update(b,0,n);}StringBuilder s=new StringBuilder();for(byte b:md.digest())s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();}
 static boolean name(long cls,String wanted){try{byte[] b=bytes(ptr(cls+16),wanted.length());return new String(b,StandardCharsets.UTF_8).equals(wanted);}catch(Exception e){return false;}}
 static boolean valid(long obj,long managerClass,long luaClass){try{return ptr(obj)==managerClass&&ptr(ptr(obj+32))==luaClass&&ptr(ptr(obj+32)+16)!=0;}catch(Exception e){return false;}}
 static long scan(long cls,long luaClass)throws Exception{List<Region> candidates=new ArrayList<>();for(Region r:regions)if(r.perms.startsWith("rw")&&r.start>=0x100000000L&&r.end-r.start<=300L*1024*1024&&(r.path.isEmpty()||r.path.startsWith("[anon")))candidates.add(r);Collections.sort(candidates,(a,b)->Long.compare(b.start,a.start));long scanned=0;for(Region r:candidates){for(long at=r.start;at<r.end;at+=1048576){cancelCheck();if(System.currentTimeMillis()>deadline||scanned>2200L*1024*1024)throw new IOException("Bounded discovery exhausted. Retry while the game is fully loaded.");int n=(int)Math.min(1048576+8,r.end-at);byte[] b;try{b=bytes(at,n);}catch(Exception e){continue;}scanned+=n;for(int i=0;i+8<=n;i+=8){if(b[i]!=(byte)cls)continue;if(u64(b,i)==cls&&valid(at+i,cls,luaClass))return at+i;}}}throw new IOException("Lua manager not found in the scanned heap. Wait for loading to finish.");}
 static String luaString(long p)throws Exception{int tt=u8(p+8)&63;int n=tt==4?u8(p+11):(int)ptr(p+16);if(n<0||n>128)throw new IOException("String bound");return new String(bytes(p+24,n),StandardCharsets.UTF_8);}
 static final class FieldSlot{final long nodes;final int log,index;FieldSlot(long nodes,int log,int index){this.nodes=nodes;this.log=log;this.index=index;}}
 static final Map<Long,Map<String,FieldSlot>> fieldSlots=new LinkedHashMap<Long,Map<String,FieldSlot>>(256,.75f,true){protected boolean removeEldestEntry(Map.Entry<Long,Map<String,FieldSlot>> e){return size()>2048;}};
 static boolean keyEquals(long p,byte[] wanted)throws Exception{byte[] header=bytes(p+8,16);int type=header[0]&63;if(type!=4&&type!=20)return false;long n=type==4?(header[3]&255):u64(header,8);return n<=128&&n==wanted.length&&Arrays.equals(wanted,bytes(p+24,(int)n));}
 static long findField(long table,String key)throws Exception{
  byte[] wanted=key.getBytes(StandardCharsets.UTF_8);
  for(int attempt=0;attempt<2;attempt++){
   byte[] header=bytes(table+8,24);int log=header[3]&255;if(log>18)throw new IOException("Table bound");long nodes=u64(header,16);if(nodes==0)throw new IOException("Lua field absent: "+key);
   Map<String,FieldSlot> slots=fieldSlots.get(table);FieldSlot slot=slots==null?null:slots.get(key);
   if(slot!=null&&slot.nodes==nodes&&slot.log==log)try{long at=nodes+slot.index*24L;byte[] node=bytes(at,24);if((node[9]&15)==4&&(node[8]&15)!=0&&keyEquals(u64(node,16),wanted)&&ptr(table+24)==nodes&&u8(table+11)==log){if(Perf.enabled)Perf.fieldHits++;return at;}}catch(IOException ignored){}
   if(Perf.enabled)Perf.fieldMisses++;int count=1<<log;long found=0;int foundIndex=-1;
   // Copy bounded chunks rather than issuing several seek/read calls per empty node.
   for(int start=0;start<count&&found==0;start+=4096){int length=Math.min(4096,count-start);byte[] block=bytes(nodes+start*24L,length*24);for(int i=0;i<length;i++){int offset=i*24;if((block[offset+9]&15)==4&&(block[offset+8]&15)!=0)try{if(keyEquals(u64(block,offset+16),wanted)){foundIndex=start+i;found=nodes+foundIndex*24L;break;}}catch(IOException ignored){}}}
   if(ptr(table+24)!=nodes||u8(table+11)!=log)continue;
   if(found==0)throw new IOException("Lua field absent: "+key);
   if(slots==null){slots=new HashMap<>();fieldSlots.put(table,slots);}if(slots.size()>=128)slots.clear();slots.put(key,new FieldSlot(nodes,log,foundIndex));return found;
  }throw new IOException("Lua table changed during field lookup: "+key);
 }
 static long number(long table,String key)throws Exception{long v=findField(table,key);int tt=u8(v+8);if(tt==3)return ptr(v);if(tt==19)return (long)Double.longBitsToDouble(ptr(v));throw new IOException("Expected numeric field: "+key);}
 static void bindCache(String path,String pid,String identity,long manager)throws Exception{if(path==null)return;File cache=new File(path);if(!path.equals(boundCachePath)||!cache.exists())try(FileWriter w=new FileWriter(cache)){w.write(pid+" "+identity+" "+Long.toHexString(manager));}boundCachePath=path;}
 static JSONObject liveState(String pid,String identity,long globals,long manager,String discovery)throws Exception{
  long scene=ptr(findField(globals,"SceneManager")),sceneId=number(scene,"CurrSceneID"),level=number(scene,"LevelId"),view=number(scene,"curViewMode");long ui=ptr(findField(globals,"UIManagerInstance")),windowStack=ptr(findField(ui,"windowStack")),modalCount=number(windowStack,"length");
  if(!identity.equals(start(pid)))throw new IOException("Game restarted during read; stopped");
  return new JSONObject().put("ok",true).put("pid",Integer.parseInt(pid)).put("processStart",identity).put("accountUid",pinnedUid).put("accountName",pinnedName).put("discovery",discovery).put("sceneId",sceneId).put("scene",sceneId==1?"City / base":sceneId==2?"World":"Other ("+sceneId+")").put("levelId",level).put("viewMode",view).put("gameStarted",u8(manager+0x98)==1).put("timestampMs",System.currentTimeMillis()).put("modalWindowCount",modalCount).put("navigationReady",modalCount==0&&(sceneId==1||sceneId==2)).put("readOnly",true);
 }
 public static JSONObject snapshot(String cachePath)throws Exception {long timing=Perf.begin();try{
  deadline=System.currentTimeMillis()+35000;String pid=findPinnedProcess(false),identity=start(pid);mem=new RandomAccessFile("/proc/"+pid+"/mem","r");
  if(pinnedManager!=0&&pinnedManagerClass!=0&&pinnedLuaClass!=0&&valid(pinnedManager,pinnedManagerClass,pinnedLuaClass)){long globals=globalsAt(pinnedManager);account(globals);bindCache(cachePath,pid,identity,pinnedManager);return liveState(pid,identity,globals,pinnedManager,"validated runtime");}
  regions=new ArrayList<>();for(String l:text("/proc/"+pid+"/maps").split("\n"))regions.add(new Region(l));
  long base=0,mc=0,lc=0;String lib="";for(Region r:regions)if(r.offset==0&&r.path.endsWith("/libil2cpp.so")&&r.path.contains(PKG)){try{long m=ptr(ptr(r.start+0x5451aa8L)),c=ptr(ptr(r.start+0x542cd08L));if(name(m,"XLuaManager")&&name(c,"LuaEnv")){base=r.start;mc=m;lc=c;lib=r.path;break;}}catch(Exception ignored){}}
  if(base==0)throw new IOException("Expected Unity runtime not found for this build.");File binary=new File(lib);String stamp=lib+":"+binary.length()+":"+binary.lastModified();if(!stamp.equals(validatedLibrary)){if(!EXPECTED.equals(hash(lib)))throw new IOException("Game build changed. New static analysis required.");validatedLibrary=stamp;}
  File cache=cachePath!=null?new File(cachePath):null;long manager=0;boolean cached=false;
  if(cache!=null&&cache.exists())try{String[] a=text(cache.getPath()).split(" ");if(a.length==3&&a[0].equals(pid)&&a[1].equals(identity)){long p=Long.parseLong(a[2],16);if(valid(p,mc,lc)){manager=p;cached=true;}}}catch(Exception ignored){}
  if(manager==0)manager=scan(mc,lc);long globals=globalsAt(manager);account(globals);pinnedManager=manager;pinnedManagerClass=mc;pinnedLuaClass=lc;boundCachePath=null;bindCache(cachePath,pid,identity,manager);
  return liveState(pid,identity,globals,manager,cached?"validated cache":"automatic heap discovery");
 }finally{if(mem!=null){try{mem.close();}catch(Exception ignored){}mem=null;}Perf.end("stateSnapshot",timing);}}
 public static void main(String[] args){try{System.out.println(snapshot(args.length>0?args[0]:null).toString(2));}catch(Throwable e){try{System.out.println(new JSONObject().put("ok",false).put("error",e.toString()).toString(2));}catch(Exception ignored){}System.exit(1);}}
}
