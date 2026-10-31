package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import java.security.*;import java.nio.charset.*;import org.json.*;
final class AllianceHelpReader {
 final MaintenanceContext context;AllianceHelpReader(MaintenanceContext c){context=c;}
 static final class Snapshot {
  String guild;long count,points,reset;TreeSet<String> requests=new TreeSet<>(),handled=new TreeSet<>();boolean claimable;
  String period()throws Exception{String input=guild+"|"+reset+"|"+String.join(",",requests);byte[] bytes=MessageDigest.getInstance("SHA-256").digest(input.getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format("%02x",b&255));return out.toString();}
  JSONObject json()throws Exception{return new JSONObject().put("guild",guild).put("count",count).put("points",points).put("reset",reset).put("requests",new JSONArray(requests)).put("handled",new JSONArray(handled)).put("claimable",claimable);}
 }
 Snapshot read()throws Exception{
  context.active();Snapshot s=new Snapshot();try(GameMemory m=new GameMemory(context.controller.cache)){
   long parentState=GameMemory.number(m.path("UIManagerInstance/windows/UIAllianceMainTable"),"State");if(!m.open("UIAllianceHelp")||(parentState!=2&&parentState!=3)||m.state.getInt("modalWindowCount")!=2)throw new IOException("Unexpected alliance help window context");
   s.guild=GameMemory.string(m.path("DataCenter/AllianceBaseDataManager/allianceBaseData"),"uid");if(!s.guild.matches("[a-f0-9]{32}"))throw new IOException("Alliance identity unavailable");
   long data=m.path("DataCenter/AllianceHelpDataManager");s.count=GameMemory.number(data,"helpNum");s.points=GameMemory.number(data,"todayHelpPoint");s.reset=GameMemory.number(data,"refreshTime");
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(GameMemory.f(data,"otherHelpInfoList"))){if((row.tag&15)!=5)continue;String guild=GameMemory.string(row.raw,"allianceId"),id=GameMemory.string(row.raw,"helpId");if(!guild.equals(s.guild)||!id.matches("[a-f0-9]{32}"))throw new IOException("Alliance request identity mismatch");s.requests.add(id);}
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(GameMemory.f(data,"_handledCallHelpIds")))s.handled.add(row.key);
   if(s.count<0||s.count>8192||s.points<0||s.reset<=0||(s.count>0&&s.requests.isEmpty()))throw new IOException("Invalid alliance help counters");
  }
  JSONObject button=control("help_btn"),label=control("help_txt");s.claimable=AllianceHelpPolicy.eligible(s.count,button.getBoolean("active"),button.getBoolean("interactable"),label.optString("text"));context.active();return s;
 }
 JSONObject control(String name)throws Exception{return context.input.action(new JSONObject().put("action","ui-bounds").put("path",AllianceHelpPolicy.VIEW+name).put("stateOnly",true));}
}
