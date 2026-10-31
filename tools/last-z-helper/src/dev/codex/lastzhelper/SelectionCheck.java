package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Live selection/rejection check. This diagnostic never selects a chat channel. */
public final class SelectionCheck {
 public static void main(String[] a)throws Exception{
  try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  AutomationController c=new AutomationController(new File(a[0]),new File(a[1]),new File(a[2]),new File(a[0],"stop-request"),true,0);c.mode="selection-test";c.input.foreground();c.ensureTrucks();
  JSONArray candidates=TruckProbe.snapshot(c.cache).getJSONArray("candidates");JSONObject sample=null;for(int i=0;i<candidates.length();i++)if(candidates.getJSONObject(i).getString("decision").startsWith("SKIP")){sample=candidates.getJSONObject(i);break;}
  if(sample==null)throw new IOException("No non-qualifying fixture available for rejection test");
  if(!c.openTruck(sample))throw new IOException("Selection test failed");
  c.truckShare();boolean rejected=false;try{c.share(sample,true);}catch(IOException e){rejected=e.getMessage().contains("no longer qualify");}
  if(!rejected)throw new IOException("Non-qualifying share was not rejected");
  if(!c.open("UIPositionShare"))throw new IOException("Diagnostic unexpectedly left prepared menu");
  c.closeShare();
  System.out.println(new JSONObject().put("ok",true).put("selected",sample.getString("id")).put("invalidShareRejectedBeforeChannel",true).put("worldPosts",0));
  }
 }
}
