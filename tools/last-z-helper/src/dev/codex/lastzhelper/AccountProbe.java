package dev.codex.lastzhelper;
import org.json.*;
/** Read-only account discovery. Does not focus, launch or resize an activity. */
public final class AccountProbe {
 public static void main(String[] args){try{try(GameMemory m=new GameMemory(args[0])){
  JSONObject out=new JSONObject().put("state",m.state);
  out.put("uid",GameMemory.string(m.path("ChatManager2/Instance"),"cur_gameuid"));
  out.put("self",TruckDiscoveryProbe.describe(m.path("DataCenter/PlayerInfoDataManager/selfPlayerData"),0));
  JSONArray managers=new JSONArray();for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("DataCenter")))if(v.key.matches("(?i).*(player|user|role|lord|commander).*")){JSONObject row=v.json();if((v.tag&15)==5)row.put("fields",TruckDiscoveryProbe.describe(v.raw,0));managers.put(row);}out.put("playerManagers",managers);
  System.out.println(out.toString(2));
 }}catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
