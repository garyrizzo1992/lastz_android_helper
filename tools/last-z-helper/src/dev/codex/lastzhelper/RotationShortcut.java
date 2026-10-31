package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import java.util.regex.*;import org.json.*;
/** Read Android's registered shortcut export; labels/array positions never identify a character. */
final class RotationShortcut {
 final String id,component,action;final int clone;
 RotationShortcut(String id,String component,String action,int clone){
  if(id==null||id.length()>128||!component.equals("com.lbe.parallel.intl/com.lbe.parallel.ui.LaunchDelegateActivity")||!action.equals("com.lbe.parallel.ACTION_LAUNCH_PACKAGE")||clone<0||clone>99)throw new IllegalArgumentException("Unsupported Last Z launch target");
  this.id=id;this.component=component;this.action=action;this.clone=clone;
 }
 static List<RotationShortcut> parse(String dump)throws Exception{
  List<RotationShortcut> found=new ArrayList<>();Set<Integer> clones=new HashSet<>();Set<String> ids=new HashSet<>();
  Matcher blocks=Pattern.compile("ShortcutInfo \\{id=([^,\\r\\n]+),([\\s\\S]*?)(?=ShortcutInfo \\{|\\z)").matcher(dump);
  while(blocks.find()){
   String b=blocks.group(2);if(!b.contains("packageName=com.lbe.parallel.intl")||!b.contains("EXTRA_LAUNCH_PACKAGE=com.readygo.barrel.gp"))continue;
   if(!b.contains("disabledReason=[Not disabled]"))continue;
   Matcher target=Pattern.compile("intents=\\[Intent \\{ act=([^ \\r\\n]+)\\s+cmp=([^ \\r\\n}]+) \\}/PersistableBundle\\[\\{([^}]+)\\}\\]\\]").matcher(b);
   if(!target.find())throw new IOException("Cannot decode registered Last Z shortcut "+blocks.group(1));
   Map<String,String> extras=new HashMap<>();for(String part:target.group(3).split(",\\s*")){String[] kv=part.trim().split("=",2);if(kv.length!=2||extras.put(kv[0],kv[1])!=null)throw new IOException("Ambiguous shortcut extras");}
   if(extras.size()!=2||!"com.readygo.barrel.gp".equals(extras.get("EXTRA_LAUNCH_PACKAGE"))||!extras.getOrDefault("EXTRA_LAUNCH_UID","").matches("[0-9]{1,2}"))throw new IOException("Unsupported shortcut extras");
   RotationShortcut s=new RotationShortcut(blocks.group(1),target.group(2),target.group(1),Integer.parseInt(extras.get("EXTRA_LAUNCH_UID")));
   if(!ids.add(s.id)||!clones.add(s.clone))throw new IOException("Duplicate Last Z shortcut route");found.add(s);
  }
  found.sort(Comparator.comparingInt(s->s.clone));if(found.isEmpty()||found.size()>20)throw new IOException("No supported registered Last Z shortcuts found");return found;
 }
 JSONObject json()throws Exception{return new JSONObject().put("shortcutId",id).put("component",component).put("action",action).put("clone",clone);}
 static RotationShortcut from(JSONObject o)throws Exception{return new RotationShortcut(o.getString("shortcutId"),o.getString("component"),o.getString("action"),o.getInt("clone"));}
 boolean same(RotationShortcut s){return id.equals(s.id)&&component.equals(s.component)&&action.equals(s.action)&&clone==s.clone;}
 String[] launch(){return new String[]{"/system/bin/am","start","-W","-n",component,"-a",action,"--ei","EXTRA_LAUNCH_UID",Integer.toString(clone),"--es","EXTRA_LAUNCH_PACKAGE","com.readygo.barrel.gp"};}
}
