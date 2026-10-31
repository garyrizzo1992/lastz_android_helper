package dev.codex.lastzhelper;
import java.io.*;import java.nio.file.*;
public final class RunLogTests {
 public static void main(String[] args)throws Exception{File file=File.createTempFile("lastz-rotation-log-",".txt");try{StringBuilder text=new StringBuilder();try(FileOutputStream live=new FileOutputStream(file)){for(int i=0;i<15000;i++)RunLog.append(text,"progress-"+i+" — long rotation evidence",true,live);RunLog.append(text,"FINAL: worker interrupted; pending attempt protected",true,live);}String saved=new String(Files.readAllBytes(file.toPath()),"UTF-8");if(!saved.equals(text.toString())||!saved.contains("progress-14999")||saved.contains("progress-0 —")||!saved.endsWith("FINAL: worker interrupted; pending attempt protected\n")||text.length()>RunLog.LIMIT)throw new AssertionError("Rolling log must retain bounded recent UTF-8 evidence and final error");System.out.println("Rolling rotation log retention/UTF-8/final-error checks passed");}finally{file.delete();}}
}
