package dev.codex.lastzhelper;
import java.io.*;import java.security.*;
/** Immutable runtime identity; never removes or rewrites an older session asset. */
final class RuntimeAssetIdentity {
 static String agentName(InputStream source)throws Exception{
  MessageDigest digest=MessageDigest.getInstance("SHA-256");byte[] buffer=new byte[16384];int n,total=0;
  while((n=source.read(buffer))!=-1){total+=n;if(total>4*1024*1024)throw new IOException("Agent asset exceeds supported size");digest.update(buffer,0,n);}
  if(total==0)throw new IOException("Empty agent asset");StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return "input-agent-"+hex+".js";
 }
}
