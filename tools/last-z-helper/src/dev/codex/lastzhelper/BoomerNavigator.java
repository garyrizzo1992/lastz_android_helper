package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Bounded semantic navigation; every input is guarded again in the native agent. */
final class BoomerNavigator {
 final MaintenanceContext c;BoomerNavigator(MaintenanceContext c){this.c=c;}
 void waitNotice()throws Exception{
  long until=System.currentTimeMillis()+5000;boolean reported=false;
  while(true){c.active();try(GameMemory m=new GameMemory(c.controller.cache)){
   if(!m.open("UINoticeTips"))return;
   int expected=m.open("UIAllianceAutoJoinRally")?2:m.open("UIActivityCenterTable")?1:0;
   if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=expected)throw new IOException("Unexpected modal while waiting for game notice");
  }
   if(System.currentTimeMillis()>=until)throw new IOException("Game notice did not clear; no navigation sent");
   if(!reported){c.event("boomer_auto_join","Waiting for game notice to clear");reported=true;}c.input.pause(150);
  }
 }
 void tap(String path)throws Exception{
  for(int attempt=0;attempt<2;attempt++){
   c.active();waitNotice();try{c.input.action(new JSONObject().put("action","ui-tap").put("path",path).put("boomerRoute",BoomerNavigationPolicy.route(path)));c.input.pause(350);return;}
   catch(DeviceInput.PreDispatchRejected e){JSONObject receipt=e.receipt;if(attempt!=0||!BoomerNavigationPolicy.retryNotice(receipt.optBoolean("inputDispatched",true),receipt.optString("phase"),receipt.optString("requestAction"),receipt.optString("controlPath"),path,receipt.optString("error")))throw e;}
  }
 }

 void center()throws Exception{try(GameMemory m=new GameMemory(c.controller.cache)){if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=1||!m.open("UIActivityCenterTable"))throw new IOException("Event Center alone required");}}
 String target()throws Exception{center();try(GameMemory m=new GameMemory(c.controller.cache)){return BoomerEventTarget.find(m);}}
 String waitTarget()throws Exception{long until=System.currentTimeMillis()+5000;while(true){c.active();try{return target();}catch(IOException e){if(!(e.getMessage().equals("Danger Lurks event is unavailable")||e.getMessage().equals("Lua field absent: groupItems"))||System.currentTimeMillis()>=until)throw e;c.input.pause(200);}}}
 void open()throws Exception{
  c.active();boolean dialog,center,world;try(GameMemory m=new GameMemory(c.controller.cache)){dialog=m.open("UIAllianceAutoJoinRally");center=m.open("UIActivityCenterTable");world=m.state.getInt("sceneId")==2;if(dialog){BoomerReader.identity(m);return;}if(!center&&((m.state.getInt("sceneId")!=1&&m.state.getInt("sceneId")!=2)||m.state.getInt("modalWindowCount")!=0))throw new IOException("Clear base required for Auto Boomer navigation");}
  if(!center&&world){tap(BoomerNavigationPolicy.HOME);long until=System.currentTimeMillis()+5000;while(true){c.active();try(GameMemory m=new GameMemory(c.controller.cache)){if(m.state.getInt("sceneId")==1&&m.state.getInt("modalWindowCount")==0)break;}if(System.currentTimeMillis()>=until)throw new IOException("Base not ready after recognized Home control");c.input.pause(150);}}
  if(!center){c.event("boomer_auto_join","Opening Event Center");tap(BoomerNavigationPolicy.ENTRY);c.controller.waitWindow("UIActivityCenterTable",5000);}
  c.event("boomer_auto_join","Finding Danger Lurks");String card=waitTarget();boolean visible=false;
  for(int swipe=0;swipe<=24;swipe++){
   c.active();if(!card.equals(target()))throw new IOException("Danger Lurks route changed during search");try{c.input.controlBounds(card);visible=true;break;}catch(IOException e){if(!e.getMessage().contains("Control is outside visible screen")&&!e.getMessage().contains("Danger Lurks card is outside visible carousel"))throw e;}
   if(swipe==24)break;
   c.input.action(new JSONObject().put("action","ui-swipe").put("path",BoomerNavigationPolicy.EVENT+"tabScrollViewN").put("child","Viewport").put("direction",swipe<8?"left":"right").put("eventCarousel",true).put("eventCardPath",card));c.input.pause(500);
  }
  if(!visible)throw new IOException("Danger Lurks card is not visible after bounded carousel search");
  tap(card);long until=System.currentTimeMillis()+5000;
  while(true){c.active();try(GameMemory m=new GameMemory(c.controller.cache)){if(m.open("UIActivityCenterTable")&&m.state.getInt("modalWindowCount")==1&&"40005".equals(GameMemory.string(m.path(BoomerNavigationPolicy.EVENT.substring(0,BoomerNavigationPolicy.EVENT.length()-1)),"lastActivityId")))break;}if(System.currentTimeMillis()>=until)throw new IOException("Danger Lurks panel not ready");c.input.pause(150);}
  until=System.currentTimeMillis()+10000;while(true){c.active();target();try{c.input.controlBounds(BoomerNavigationPolicy.AUTO);break;}catch(IOException e){if(!e.getMessage().contains("Exported control is hidden")&&!e.getMessage().contains("Exported control is disabled")&&!e.getMessage().contains("Control is outside visible screen"))throw e;if(System.currentTimeMillis()>=until)throw e;c.input.pause(200);}}
  c.event("boomer_auto_join","Opening Auto Team-Up");tap(BoomerNavigationPolicy.AUTO);c.controller.waitWindow("UIAllianceAutoJoinRally",5000);try(GameMemory m=new GameMemory(c.controller.cache)){BoomerReader.identity(m);}
 }
 void waitClosed(String name,long timeout)throws Exception{long until=System.currentTimeMillis()+timeout;while(c.controller.open(name)){if(System.currentTimeMillis()>=until)throw new IOException(name+" did not close");c.input.pause(150);}}
 void close()throws Exception{
  c.active();boolean dialog;try(GameMemory m=new GameMemory(c.controller.cache)){dialog=m.open("UIAllianceAutoJoinRally");if(dialog)BoomerReader.identity(m);}
  if(dialog){tap(BoomerNavigationPolicy.DIALOG+"closeBtnN");waitClosed("UIAllianceAutoJoinRally",5000);}
  boolean center;try(GameMemory m=new GameMemory(c.controller.cache)){center=m.open("UIActivityCenterTable");}
  if(center){center();tap(BoomerNavigationPolicy.EVENT+"bottomCloseBtn");waitClosed("UIActivityCenterTable",5000);}
  try(GameMemory m=new GameMemory(c.controller.cache)){if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=0)throw new IOException("Auto Boomer did not return to clear base");}
 }
}
