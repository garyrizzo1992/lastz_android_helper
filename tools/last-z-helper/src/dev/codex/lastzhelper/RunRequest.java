package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Only the app process writes run consent; workers only read it. STOP revokes it. */
final class RunRequest {
 interface BootSource{String read()throws Exception;}static final Object LOCK=new Object();final File file;final BootSource bootSource;RunRequest(File dir){this(dir,RunRequest::boot);}
 RunRequest(File dir,BootSource bootSource){file=new File(dir,"bot-run-request.json");this.bootSource=bootSource;}
 static volatile String bootId;static synchronized String boot()throws Exception{if(bootId==null)bootId=StateProbe.text("/proc/sys/kernel/random/boot_id");return bootId;}
 JSONObject read()throws Exception{return file.exists()?new JSONObject(StateProbe.text(file.getPath())):null;}
 String begin(JSONObject options)throws Exception{synchronized(LOCK){String generation=UUID.randomUUID().toString();options.put("runGeneration",generation);RotationFiles.write(file,new JSONObject().put("schema",1).put("generation",generation).put("requestedRunning",true).put("boot",bootSource.read()).put("options",new JSONObject(options.toString())).put("workerRestarts",0));return generation;}}
 void stop()throws Exception{synchronized(LOCK){JSONObject r=read();if(r!=null){r.put("requestedRunning",false);RotationFiles.write(file,r);}}}
 boolean matches(String generation)throws Exception{JSONObject r=read();return r!=null&&generation.equals(r.getString("generation"));}
 boolean active(String generation,File stop)throws Exception{JSONObject r=read();return r!=null&&r.getInt("schema")==1&&generation.equals(r.getString("generation"))&&RecoveryPolicy.sessionAllowed(r.getBoolean("requestedRunning"),stop.exists(),r.getString("boot"),bootSource.read());}
 boolean restart(String generation,File stop)throws Exception{synchronized(LOCK){if(!active(generation,stop))return false;JSONObject r=read();JSONArray old=r.optJSONArray("restartTimes"),times=new JSONArray();long now=System.currentTimeMillis();if(old!=null)for(int i=0;i<old.length();i++){long t=old.getLong(i);if(t>now||now-t<RecoveryPolicy.WINDOW)times.put(t);}if(!RecoveryPolicy.restartAllowed(times.length()))return false;times.put(now);r.put("restartTimes",times).put("workerRestarts",r.optInt("workerRestarts")+1);RotationFiles.write(file,r);return true;}}
 void finish(String generation)throws Exception{synchronized(LOCK){JSONObject r=read();if(r!=null&&generation.equals(r.getString("generation"))){r.put("requestedRunning",false);RotationFiles.write(file,r);}}}
}
