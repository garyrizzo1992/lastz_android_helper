package dev.codex.lastzhelper;
import org.json.*;
/** Bounded read-only investigation of explicitly selected game tables. */
public final class MemoryQuery {
 public static void main(String[] args){try{try(GameMemory m=new GameMemory(args[0])){
  long t=args[1].equals("globals")?m.globals:m.path(args[1]);int depth=args.length>2?Integer.parseInt(args[2]):0;
  if(depth<0||depth>2)throw new IllegalArgumentException("Depth 0..2");
  JSONArray rows=new JSONArray();for(TruckDiscoveryProbe.Value v:GameMemory.rows(t)){if(args.length>3&&!v.key.matches(args[3]))continue;JSONObject row=v.json();if(v.key.equals("attachmentId")&&(v.tag&15)==4)row.put("string",GameMemory.attachment(t));if(depth>0&&(v.tag&15)==5)row.put("fields",TruckDiscoveryProbe.describe(v.raw,depth-1));rows.put(row);}
  System.out.println(new JSONObject().put("state",m.state).put("fields",rows).toString(2));
 }}catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
