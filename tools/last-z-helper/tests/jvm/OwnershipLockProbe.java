package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;
public final class OwnershipLockProbe {public static void main(String[] args)throws Exception{try(RandomAccessFile f=new RandomAccessFile(new File(args[0],"control.lock"),"rw");FileChannel c=f.getChannel();FileLock lock=c.tryLock()){System.out.println(lock==null?"busy":"free");}}}
