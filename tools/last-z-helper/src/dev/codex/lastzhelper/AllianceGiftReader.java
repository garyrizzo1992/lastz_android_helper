package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import java.security.*;import java.nio.charset.*;import org.json.*;
final class AllianceGiftReader {
 final MaintenanceContext context;AllianceGiftReader(MaintenanceContext c){context=c;}
 static final class Gift {String id;int type,state;long expires,received;JSONObject json()throws Exception{return new JSONObject().put("id",id).put("type",type).put("state",state).put("expires",expires).put("received",received);}}
 static final class Snapshot {
  String guild;int tab;boolean busy,ready,claimable;TreeMap<String,Gift> gifts=new TreeMap<>();
  TreeSet<String> pending(){TreeSet<String> out=new TreeSet<>();for(Gift g:gifts.values())if(g.type==AllianceGiftPolicy.rewardType(tab)&&g.state==0&&g.expires>System.currentTimeMillis())out.add(g.id);return out;}
  String period()throws Exception{byte[] bytes=MessageDigest.getInstance("SHA-256").digest((guild+"|"+tab+"|"+String.join(",",pending())).getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format("%02x",b&255));return out.toString();}
  JSONObject json()throws Exception{JSONArray rows=new JSONArray();for(Gift g:gifts.values())rows.put(g.json());return new JSONObject().put("guild",guild).put("tab",tab).put("busy",busy).put("ready",ready).put("claimable",claimable).put("gifts",rows);}
 }
 Snapshot read()throws Exception{
  context.active();Snapshot s=new Snapshot();try(GameMemory m=new GameMemory(context.controller.cache)){
   long parentState=GameMemory.number(m.path("UIManagerInstance/windows/UIAllianceMainTable"),"State");if(!m.open("UIAllianceGift")||(parentState!=2&&parentState!=3)||m.state.getInt("modalWindowCount")!=2)throw new IOException("Unexpected alliance gift window context");
   s.guild=GameMemory.string(m.path("DataCenter/AllianceBaseDataManager/allianceBaseData"),"uid");if(!s.guild.matches("[a-f0-9]{32}"))throw new IOException("Alliance identity unavailable");
   long view=m.path(AllianceGiftPolicy.VIEW.substring(0,AllianceGiftPolicy.VIEW.length()-1));s.tab=(int)GameMemory.number(view,"tabIndex");if(GameMemory.number(view,"toogleIndex")!=s.tab)throw new IOException("Gift tab selection changed");AllianceGiftPolicy.name(s.tab);s.busy=GameMemory.bool(view,"isGettingAll");s.ready=GameMemory.bool(view,"isGetBtnReady");
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(m.path("DataCenter/AllianceGiftDataManager/giftInfoList"))){if((row.tag&15)!=5)continue;Gift g=new Gift();g.id=GameMemory.string(row.raw,"uuid");g.type=(int)GameMemory.number(row.raw,"rewardType");g.state=(int)GameMemory.number(row.raw,"receiveState");g.expires=GameMemory.number(row.raw,"expirationTime");g.received=GameMemory.number(row.raw,"receiveTime");if(!g.id.matches("[a-f0-9]{32}")||(g.type!=1&&g.type!=2)||(g.state!=0&&g.state!=1))throw new IOException("Unknown gift identity/type/state");if(s.gifts.put(g.id,g)!=null)throw new IOException("Duplicate gift identity");}
  }
  JSONObject selected=control("toogles/#"+s.tab+"/selectName");if(!selected.getBoolean("active")||!AllianceGiftPolicy.name(s.tab).equals(selected.optString("text")))throw new IOException("Gift tab label mismatch");
  JSONObject button=control("get_all_btn"),label=control("get_all_btn_txt");s.claimable=AllianceGiftPolicy.claimable(s.pending().size(),button.getBoolean("active"),button.getBoolean("interactable"),label.optString("text"),s.busy,s.ready);context.active();return s;
 }
 JSONObject control(String name)throws Exception{return context.input.action(new JSONObject().put("action","ui-bounds").put("path",AllianceGiftPolicy.VIEW+name).put("stateOnly",true));}
}
