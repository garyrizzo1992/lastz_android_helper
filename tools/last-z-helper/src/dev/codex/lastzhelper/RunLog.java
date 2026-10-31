package dev.codex.lastzhelper;
import java.io.*;
/** Keep recent rotation evidence; an endless loop must not freeze its log at the first 256K. */
final class RunLog {
 static final int LIMIT=262144;
 static void append(StringBuilder text,String line,boolean rolling,FileOutputStream live)throws Exception{
  if(!rolling){if(text.length()<LIMIT){text.append(line).append('\n');live.write((line+"\n").getBytes("UTF-8"));live.flush();}return;}
  text.append(line).append('\n');
  if(text.length()>LIMIT){int from=text.length()-196608,end=text.indexOf("\n",from);text.delete(0,end>=0&&end<text.length()-1?end+1:from);live.getChannel().truncate(0);live.getChannel().position(0);live.write(text.toString().getBytes("UTF-8"));}
  else live.write((line+"\n").getBytes("UTF-8"));live.flush();
 }
}
