package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Permanent shared bounty-navigation knowledge, independent of run/account/channel. */
final class DeadStateStore {
 final File file;final JSONObject data,states;
 DeadStateStore(File file)throws Exception{
  this.file=file;
  if(file.exists()){
   if(file.length()>8*1024*1024)throw new IOException("Dead-state file exceeds supported bound");
   data=new JSONObject(StateProbe.text(file.getPath()));if(data.getInt("schema")!=1)throw new IOException("Unsupported dead-state file schema");states=data.getJSONObject("states");
   Iterator<String> keys=states.keys();while(keys.hasNext()){String key=keys.next();if(!key.matches("[1-9][0-9]{0,3}"))throw new IOException("Invalid saved dead state");int state=DeadStatePolicy.state(Integer.parseInt(key));JSONObject record=states.getJSONObject(key);if(record.getInt("state")!=state||record.getLong("confirmedAtMs")<=0||!DeadStatePolicy.permanent(record.getString("message")))throw new IOException("Unconfirmed saved dead-state record");}
  }else{states=new JSONObject();data=new JSONObject().put("schema",1).put("states",states);}
 }
 boolean contains(int state){return states.has(Integer.toString(DeadStatePolicy.state(state)));}
 boolean record(int state,String message,long now)throws Exception{
  DeadStatePolicy.state(state);if(!DeadStatePolicy.permanent(message))return false;if(now<=0)throw new IllegalArgumentException("Invalid dead-state confirmation time");
  if(contains(state))return false;
  states.put(Integer.toString(state),new JSONObject().put("state",state).put("message",DeadStatePolicy.message(message)).put("confirmedAtMs",now));ShareLedger.atomic(file,data);return true;
 }
}
