package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.concurrent.*;import org.json.*;
/** Platform-independent lock/protocol core, exercised on real filesystem locks in tests. */
final class LegacyOwnershipSession {
 interface Command{String execute(String command)throws Exception;}interface Clock{long now();}
 static void run(File dir,String token,BufferedReader in,PrintStream out,Command commands,Clock clock)throws Exception{
  if(!token.matches("[a-f0-9]{32}"))throw new IOException("Ownership token required");dir.mkdirs();File marker=new File(dir,"legacy-input.json");
  try(RandomAccessFile file=new RandomAccessFile(new File(dir,"control.lock"),"rw");FileChannel channel=file.getChannel();FileLock lock=channel.tryLock()){
   if(lock==null)throw new IOException("Another controller is active");ControllerOwnership.check(marker);
   BlockingQueue<String> queue=new ArrayBlockingQueue<>(64);java.util.concurrent.atomic.AtomicBoolean ended=new java.util.concurrent.atomic.AtomicBoolean(false);
   Thread reader=new Thread(()->{try{String l;while((l=in.readLine())!=null){if(l.length()>32768||!queue.offer(l))break;}}catch(Exception ignored){}finally{ended.set(true);}});reader.setDaemon(true);reader.start();
   out.println(new JSONObject().put("event","ownership").put("ok",true).put("token",token));out.flush();long last=clock.now();
   while(true){String line=queue.poll(500,TimeUnit.MILLISECONDS);if(line==null){if(ended.get()||clock.now()-last>15000)break;continue;}
    JSONObject request=new JSONObject(line);if(!token.equals(request.getString("token")))throw new IOException("Ownership token changed");last=clock.now();String nonce=request.getString("nonce"),action=request.getString("action");if(!nonce.matches("[a-f0-9]{32}"))throw new IOException("Invalid ownership request");JSONObject result=new JSONObject().put("event","ownership-receipt").put("nonce",nonce).put("ok",true);
    if(action.equals("shell")){
     String command=request.getString("command");if(command.length()>16000)throw new IOException("Legacy command bound");
     RotationFiles.write(marker,new JSONObject().put("schema",1).put("pending",true).put("token",token).put("nonce",nonce));
     // Marker is committed before child creation; timeout, owner death or lost
     // completion cannot permit another controller to take over unconfirmed input.
     String output=commands.execute(command);
     RotationFiles.write(marker,new JSONObject().put("schema",1).put("pending",false).put("token",token).put("nonce",nonce));result.put("stdout",output).put("returncode",0);
    }else if(!action.equals("ping"))throw new IOException("Unsupported ownership action");
    out.println(result);out.flush();
   }
  }
 }
}
