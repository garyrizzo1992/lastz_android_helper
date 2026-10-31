package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Exact tile identity from either decoded parameters or the server attachment. */
final class ChatTileIdentity {
 static String attachment(String json,int post)throws Exception{
  if(post!=604&&post!=630)throw new IOException("Unsupported tile post type");
  JSONObject data=new JSONObject(json);if(data.has("postType")&&data.getInt("postType")!=post)throw new IOException("Chat attachment post type changed");
  Object value=data.get(post==604?"trainUuid":"dispatchTaskUuid");
  if(!(value instanceof String)&&!(value instanceof Long)&&!(value instanceof Integer))throw new IOException("Chat tile UUID must retain exact integer precision");
  String id=value.toString();if(id.isEmpty()||id.length()>128)throw new IOException("Chat tile UUID length bound");
  if(post==604){if(!id.matches("[1-9][0-9]{0,18}"))throw new IOException("Invalid truck UUID");return Long.toString(Long.parseLong(id));}return id;
 }
 static String read(long message,int post)throws Exception{
  long param=GameMemory.optional(message,"param");if(param!=0)return post==604?Long.toString(GameMemory.number(param,"trainUuid")):GameMemory.string(param,"dispatchTaskUuid");
  if(GameMemory.optional(message,"attachmentId")==0)return null;
  return attachment(GameMemory.attachment(message),post);
 }
}
