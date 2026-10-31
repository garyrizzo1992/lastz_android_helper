package dev.codex.lastzhelper;
import java.io.*;import java.nio.file.*;import org.json.*;
final class ShareLedger {
 final File file;JSONObject data;
 ShareLedger(File file)throws Exception{this.file=file;data=file.exists()?new JSONObject(StateProbe.text(file.getPath())):new JSONObject();}
 boolean contains(String key){return data.has(key);}
 static void atomic(File file,JSONObject data)throws Exception{
  File temp=new File(file.getPath()+".tmp");try(FileOutputStream out=new FileOutputStream(temp)){out.write(data.toString(2).getBytes("UTF-8"));out.getFD().sync();}
  Files.move(temp.toPath(),file.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
 }
 void pending(String key,JSONObject record)throws Exception{if(contains(key))throw new IOException("Share already attempted: "+key);JSONObject r=new JSONObject(record.toString());r.put("status","pending").put("attemptMs",System.currentTimeMillis());data.put(key,r);atomic(file,data);}
 void verified(String key,long sequence)throws Exception{JSONObject record=data.getJSONObject(key);String kind=record.optString("kind"),field=kind.startsWith("group-")?"groupSequence":kind.equals("private-truck")?"privateSequence":"worldSequence";record.put("status","verified").put(field,sequence).put("verifiedMs",System.currentTimeMillis());if(kind.startsWith("group-"))record.remove("worldSequence");atomic(file,data);}
 void attackComplete(String key,String outcome)throws Exception{data.getJSONObject(key).put("status","completed").put("outcome",outcome).put("completedMs",System.currentTimeMillis());atomic(file,data);}
}
