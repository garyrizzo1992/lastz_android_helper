package dev.codex.lastzhelper;
import java.nio.channels.*;
/** Recovery waits for old ownership to end; normal competing runs fail immediately. */
final class ControllerLease {
 interface Check {void active()throws Exception;}
 static FileLock acquire(FileChannel channel,boolean recovering,Check check)throws Exception{return acquire(channel,recovering,check,20000);}
 static FileLock acquire(FileChannel channel,boolean recovering,Check check,long timeoutMs)throws Exception{
  if(timeoutMs<0||timeoutMs>20000)throw new IllegalArgumentException("Ownership wait bound");long end=System.nanoTime()+timeoutMs*1000000L;
  while(true){check.active();FileLock lock=null;try{lock=channel.tryLock();}catch(OverlappingFileLockException ignored){}if(lock!=null)return lock;if(!recovering||System.nanoTime()>=end)return null;Thread.sleep(Math.min(100,Math.max(1,timeoutMs)));}
 }
}
