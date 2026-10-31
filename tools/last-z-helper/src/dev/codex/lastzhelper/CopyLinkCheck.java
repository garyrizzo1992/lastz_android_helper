package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Copy-only investigation: never chooses a sharing channel or sends a message. */
public final class CopyLinkCheck {
 static void copy(AutomationController c,File dir,String id)throws Exception{c.input.tapControl("UIManagerInstance/windows/UIPositionShare/View/copy_btn");String link=c.input.clipboard();try(FileOutputStream out=new FileOutputStream(new File(dir,"copied-truck-link.txt"))){out.write(link.getBytes("UTF-8"));}if(!new PrivateTruckSender(c).copiedLink(link,id))throw new IOException("Copied link format needs review");System.out.println("Copied selected truck "+id+"; displayed location verified; length="+link.length()+"; no messages sent");c.input.screenshot("copy-link.png");}
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){File dir=new File(args[0]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller active");File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(dir,"injector"),new File(dir,"input-agent.js"),stop,true,0);c.input.foreground();
   if(c.open("UIPositionShare")){String id;try(GameMemory m=new GameMemory(c.cache)){id=Long.toString(GameMemory.number(m.path("UIManagerInstance/windows/UIPositionShare/View/chat_data_param"),"trainUuid"));}copy(c,dir,id);return;}c.ensureTrucks();
   JSONArray a=TruckProbe.snapshot(c.cache).getJSONArray("candidates");boolean copied=false;
   for(int i=0;i<a.length();i++){JSONObject t=a.getJSONObject(i);if(!c.openTruck(t))continue;String id=t.getString("id");c.truckShare();try(GameMemory m=new GameMemory(c.cache)){if(!m.open("UIPositionShare")||!id.equals(Long.toString(GameMemory.number(m.path("UIManagerInstance/windows/UIPositionShare/View/chat_data_param"),"trainUuid"))))throw new IOException("Copy selection mismatch");}
    copy(c,dir,id);copied=true;break;
   }if(!copied)throw new IOException("No selectable copy fixture");c.input.screenshot("copy-link.png");
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
