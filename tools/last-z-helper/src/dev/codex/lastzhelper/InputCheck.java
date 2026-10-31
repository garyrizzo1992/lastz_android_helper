package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Local diagnostic for the same input path as the foreground worker. */
public final class InputCheck {
 public static void main(String[] a)throws Exception{
  try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  DeviceInput d=new DeviceInput(a[0],new File(a[1]),new File(a[2]),new File(a[3]),new File("/data/local/tmp"));
  d.foreground();if(a.length>4){if(a[4].equals("back"))d.back();else throw new IOException("Use named live UI controls; coordinate input retired");}
  System.out.println(new JSONObject().put("ok",true).put("pid",d.pid).put("identity",d.identity));
  }
 }
}
