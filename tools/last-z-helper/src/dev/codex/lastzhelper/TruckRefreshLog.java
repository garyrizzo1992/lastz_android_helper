package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Bounded opt-in observation log. No game values or game actions are modified. */
final class TruckRefreshLog implements AutoCloseable {
 final File file;final String runId;int lastRefresh=-1,observations;boolean truncated;
 TruckRefreshLog(File dir,String mode,long powerLimit)throws Exception{
  runId=UUID.randomUUID().toString();file=new File(dir,"truck-refresh-"+System.currentTimeMillis()+"-"+runId.substring(0,8)+".jsonl");
  append(new JSONObject().put("type","start").put("schema",1).put("runId",runId).put("mode",mode).put("accountUid",StateProbe.pinnedUid).put("pid",StateProbe.pinnedPid).put("processStart",StateProbe.pinnedStart).put("powerLimit",powerLimit).put("startedMs",System.currentTimeMillis()));
 }
 void append(JSONObject row)throws Exception{try(FileOutputStream out=new FileOutputStream(file,true)){out.write((row.toString()+"\n").getBytes("UTF-8"));}}
 void record(int refresh,JSONArray trucks,Set<String> rendered)throws Exception{
  if(refresh==lastRefresh)return;if(observations>=4000||file.length()>=8*1024*1024){truncated=true;return;}
  append(new JSONObject().put("type","observation").put("refresh",refresh).put("observedMs",System.currentTimeMillis()).put("trucks",trucks).put("renderedIds",new JSONArray(rendered)));lastRefresh=refresh;observations++;
 }
 public void close()throws Exception{append(new JSONObject().put("type","end").put("lastRefresh",lastRefresh).put("observations",observations).put("truncated",truncated).put("finishedMs",System.currentTimeMillis()));}
}
