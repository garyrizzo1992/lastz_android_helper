package dev.codex.lastzhelper;
import java.io.*;
/** Legacy copy diagnostics; production delivery uses GroupTruckSender. */
final class PrivateTruckSender {
 final AutomationController c;PrivateTruckSender(AutomationController controller){c=controller;}
 boolean copiedLink(String link,String id)throws Exception{try(GameMemory m=new GameMemory(c.cache)){
  long p=m.path("UIManagerInstance/windows/UIPositionShare/View/chat_data_param");if(!id.equals(Long.toString(GameMemory.number(p,"trainUuid"))))throw new IOException("Copied truck identity changed");
  return LinkRules.containsTruck(link,id)||LinkRules.coordinates(link,GameMemory.string(p,"uname"),GameMemory.string(p,"abbr"),GameMemory.number(p,"sid"),GameMemory.number(p,"x"),GameMemory.number(p,"y"));
 }}
 String room()throws Exception{throw new IOException("Private-link delivery is retired. Use Share 3+ to trucks group.");}
 void openRecipient()throws Exception{room();}
}
