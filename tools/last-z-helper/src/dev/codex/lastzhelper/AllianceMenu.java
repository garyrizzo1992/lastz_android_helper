package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Menu rows are pooled and may arrive after the parent window opens. */
final class AllianceMenu {
 static final String LIST=AllianceHelpPolicy.MAIN+"_allianceMain/_buttonListInType";
 static boolean path(String path){return path.matches(java.util.regex.Pattern.quote(LIST)+"/#(?:[1-9]|[1-5][0-9]|6[0-4])/_btn");}
 static boolean requestAllowed(String feature,int type,String name){return (feature.equals("alliance_help")&&type==3&&"Help".equals(name))||(feature.equals("alliance_gifts")&&type==4&&"Alliance Gifts".equals(name));}
 static void open(MaintenanceContext c,int type,String name)throws Exception{
  if(!((type==3&&name.equals("Help"))||(type==4&&name.equals("Alliance Gifts"))))throw new IOException("Unsupported alliance menu");
  long end=android.os.SystemClock.elapsedRealtime()+6000;String seen="Menu rows not ready";
  while(android.os.SystemClock.elapsedRealtime()<end){c.active();String path=null,guild=null;
   try(GameMemory m=new GameMemory(c.controller.cache)){
    if(!m.open("UIAllianceMainTable")||m.state.getInt("modalWindowCount")!=1)throw new IOException("Unexpected alliance menu context");
    guild=GameMemory.string(m.path("DataCenter/PlayerInfoDataManager/selfPlayerData"),"allianceId");String base=GameMemory.string(m.path("DataCenter/AllianceBaseDataManager/allianceBaseData"),"uid");if(!guild.matches("[a-f0-9]{32}")||!guild.equals(base))throw new IOException("Alliance membership unavailable or changed");
    long parent=m.path(AllianceHelpPolicy.MAIN+"_allianceMain"),list=GameMemory.optional(parent,"_buttonListInType");JSONArray rows=new JSONArray();
    if(list!=0)for(TruckDiscoveryProbe.Value v:GameMemory.rows(list)){if((v.tag&15)!=5)continue;long item=GameMemory.optional(v.raw,"_itemData");if(item==0)continue;long t=GameMemory.number(item,"type");String label=GameMemory.string(item,"name");rows.put(new JSONObject().put("key",v.key).put("type",t).put("name",label));if(t==type&&name.equals(label)){String candidate=LIST+"/"+v.key+"/_btn";if(!path(candidate)||path!=null)throw new IOException("Ambiguous alliance menu control");path=candidate;}}
    seen=rows.toString();
   }
   if(path!=null){c.input.action(new JSONObject().put("action","ui-tap").put("path",path).put("allianceMenuType",type).put("allianceMenuName",name).put("allianceMenuGuild",guild));c.input.pause(450);return;}
   c.input.pause(200);
  }throw new IOException("Alliance menu did not expose "+name+": "+seen);
 }
}
