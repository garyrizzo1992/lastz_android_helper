package dev.codex.lastzhelper;
import java.io.*;import java.nio.*;import java.nio.charset.*;
/** Synthetic Lua layout mutations in a local file, never in game memory. */
public final class MemoryLookupTests {
 static RandomAccessFile file;static int passed;
 static void write(long at,byte[] bytes)throws Exception{file.seek(at);file.write(bytes);}
 static void integer(long at,long value)throws Exception{write(at,ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putLong(value).array());}
 static void tag(long at,int value)throws Exception{file.seek(at);file.write(value);}
 static void table(long address,long nodes,int log)throws Exception{tag(address+11,log);integer(address+24,nodes);}
 static void text(long address,String value,boolean longer)throws Exception{byte[] bytes=value.getBytes(StandardCharsets.UTF_8);tag(address+8,longer?84:68);tag(address+11,bytes.length);if(longer)integer(address+16,bytes.length);write(address+24,bytes);}
 static void node(long at,long key,long value)throws Exception{write(at,new byte[24]);integer(at,value);tag(at+8,3);tag(at+9,4);integer(at+16,key);}
 static void expect(boolean value)throws Exception{if(!value)throw new IOException("Lookup check "+(passed+1)+" failed");passed++;}
 static void missing(long t,String k)throws Exception{boolean missing=false;try{StateProbe.findField(t,k);}catch(IOException e){missing=true;}expect(missing);}
 public static void main(String[] args){File fixture=null;try{
  fixture=File.createTempFile("lastz-lua-lookup-",".bin",new File(args[0]));file=new RandomAccessFile(fixture,"rw");file.setLength(10000);StateProbe.mem=file;StateProbe.fieldSlots.clear();
  text(3000,"power",false);text(3100,"owner",false);text(3200,"uuid",false);table(1000,2000,1);node(2000,3000,100);node(2024,3100,900);
  expect(StateProbe.number(1000,"power")==100);expect(StateProbe.number(1000,"owner")==900);
  integer(2000,200);expect(StateProbe.number(1000,"power")==200); // cached location, fresh value
  table(1000,2100,1);node(2100,3100,901);node(2124,3000,300);expect(StateProbe.number(1000,"power")==300); // moved node array
  node(2124,3100,902);node(2100,3000,400);expect(StateProbe.number(1000,"power")==400); // same array, key moved
  tag(2108,0);missing(1000,"power");node(2100,3000,500);expect(StateProbe.number(1000,"power")==500); // deleted and restored value
  text(3000,"other",false);missing(1000,"power");text(3000,"power",false);expect(StateProbe.number(1000,"power")==500); // string pointer reused
  table(1000,2200,2);node(2272,3200,1430458630091584086L);expect(StateProbe.number(1000,"uuid")==1430458630091584086L); // exact 64-bit value
  table(1100,2400,1);node(2400,3000,600);expect(StateProbe.number(1100,"power")==600);expect(StateProbe.number(1000,"uuid")==1430458630091584086L); // independent table
  text(3300,"state_key",true);node(2424,3300,700);expect(StateProbe.number(1100,"state_key")==700); // long-string representation
  text(3400,"caf\u00e9",false);node(2400,3400,800);expect(StateProbe.number(1100,"caf\u00e9")==800); // UTF-8 key length
  missing(1100,"missing");tag(1111,19);missing(1100,"power");
  System.out.println("Passed "+passed+" memory lookup mutation checks");
 }catch(Throwable e){e.printStackTrace();System.exit(1);}finally{StateProbe.mem=null;try{if(file!=null)file.close();}catch(Exception ignored){}if(fixture!=null)fixture.delete();}}
}
