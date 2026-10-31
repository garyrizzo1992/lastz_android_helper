package dev.codex.lastzhelper;
import java.io.*;import java.nio.charset.*;
public final class RuntimeAssetIdentityTests {
 static String name(String content)throws Exception{return RuntimeAssetIdentity.agentName(new ByteArrayInputStream(content.getBytes(StandardCharsets.UTF_8)));}
 public static void main(String[] args)throws Exception{
  String a=name("abc");if(!a.equals("input-agent-ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad.js"))throw new AssertionError("Known digest");
  if(!a.equals(name("abc"))||a.equals(name("abcd"))||!a.matches("input-agent-[0-9a-f]{64}\\.js"))throw new AssertionError("Stable unique safe path");
  try{name("");throw new AssertionError("Empty accepted");}catch(IOException expected){}
  try{RuntimeAssetIdentity.agentName(new ByteArrayInputStream(new byte[4*1024*1024+1]));throw new AssertionError("Oversized accepted");}catch(IOException expected){}
  System.out.println("Passed runtime asset identity digest/stability/path/empty/size checks");
 }
}
