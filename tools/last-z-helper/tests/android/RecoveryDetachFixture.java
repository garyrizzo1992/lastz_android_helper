package dev.codex.lastzhelper;
import java.io.*;import java.nio.file.*;import java.nio.channels.*;import java.util.concurrent.*;
/** Android /proc guard fixture. The named child is a shell, never an injector. */
public final class RecoveryDetachFixture {
 static int checks;
 static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 public static void main(String[]args)throws Exception{
  if(args.length!=1)throw new IllegalArgumentException("Isolated fixture parent directory required");
  File locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile owner=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel channel=owner.getChannel();FileLock lock=channel.tryLock()){
  if(lock==null)throw new IOException("Another controller is active");ControllerOwnership.check();
  RecoveryGuard.noInjector();Path directory=Files.createTempDirectory(Paths.get(args[0]),"detach-");
  File executable=directory.resolve("injector-arm64-17.24.3").toFile();
  Files.copy(Paths.get("/system/bin/sh"),executable.toPath());expect(executable.setExecutable(true,false),"owned shell fixture executable");
  Process child=null;
  try{
   child=new ProcessBuilder(executable.getPath(),"-c","ticks=0; while [ \"$ticks\" -lt 30 ]; do /system/bin/sleep 1; ticks=$((ticks+1)); done").redirectErrorStream(true).start();
   int pid=DeviceInput.childPid(child);String start=StateProbe.start(Integer.toString(pid));
   expect(child.isAlive()&&StateProbe.cmdline(Integer.toString(pid)).equals(executable.getPath()),"owned shell has exact guard-test identity");
   boolean blocked=false;try{RecoveryGuard.noInjector();}catch(IOException expected){blocked=expected.getMessage().contains("Previous input session remains");}
   expect(blocked&&child.isAlive(),"unconfirmed live owner blocks recovery");
   child.destroy();if(!child.waitFor(5,TimeUnit.SECONDS)){child.destroyForcibly();expect(child.waitFor(5,TimeUnit.SECONDS),"owned child terminated");}
   expect(RecoveryGuard.gone(Integer.toString(pid),start),"exact owner exit confirmed");
   RecoveryGuard.noInjector();expect(true,"recovery guard clears only after confirmed owner exit");
   System.out.println("Android detach guard: "+checks+" checks passed; shell fixture only, no game input or memory");
  }finally{
   if(child!=null&&child.isAlive()){child.destroyForcibly();if(!child.waitFor(5,TimeUnit.SECONDS))throw new IOException("Owned shell fixture exit is unconfirmed");}
   Files.deleteIfExists(executable.toPath());Files.deleteIfExists(directory);
  }
  }
 }
}
