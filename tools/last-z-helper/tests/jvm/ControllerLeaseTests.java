package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.nio.file.*;
public final class ControllerLeaseTests {
 static int checks;static void expect(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
 public static void main(String[] args)throws Exception{File file=Files.createTempFile("lastz-lease-", ".lock").toFile();try(RandomAccessFile owner=new RandomAccessFile(file,"rw");RandomAccessFile next=new RandomAccessFile(file,"rw");FileChannel a=owner.getChannel();FileChannel b=next.getChannel()){
  FileLock held=a.lock();expect(ControllerLease.acquire(b,false,()->{},0)==null,"normal contender cannot steal lease");expect(ControllerLease.acquire(b,true,()->{},5)==null,"recovery wait is bounded");boolean stopped=false;try{ControllerLease.acquire(b,true,()->{throw new InterruptedException("STOP");},5);}catch(InterruptedException e){stopped=true;}expect(stopped,"STOP cancels ownership wait");held.close();try(FileLock acquired=ControllerLease.acquire(b,true,()->{},5)){expect(acquired!=null,"successor acquires only after release");}
  boolean bad=false;try{ControllerLease.acquire(b,true,()->{},20001);}catch(IllegalArgumentException e){bad=true;}expect(bad,"cannot configure unbounded ownership wait");System.out.println("Recovery ownership handoff: "+checks+" checks passed");
 }finally{file.delete();}}
}
