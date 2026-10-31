package dev.codex.lastzhelper;
import java.io.*;
/** Negative identity checks without changing accounts or sending input. */
public final class GuardCheck {
 public static void main(String[] args){try{
  StateProbe.pinForeground();StateProbe.snapshot(args[0]);String uid=StateProbe.pinnedUid,pid=StateProbe.pinnedPid;int checks=0;
  try{StateProbe.pinnedUid="00000000";try{StateProbe.verifyPinned();throw new AssertionError("Wrong character accepted");}catch(IOException expected){if(!expected.getMessage().contains("Character changed"))throw expected;checks++;}}finally{StateProbe.pinnedUid=uid;}
  try{StateProbe.pinnedPid=""+android.os.Process.myPid();try{StateProbe.verifyPinned();throw new AssertionError("Wrong process accepted");}catch(IOException expected){checks++;}}finally{StateProbe.pinnedPid=pid;}
  StateProbe.verifyPinned();checks++;System.out.println("Passed "+checks+" live identity guards; selected PID="+pid+", account="+uid+"; no input sent");
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
