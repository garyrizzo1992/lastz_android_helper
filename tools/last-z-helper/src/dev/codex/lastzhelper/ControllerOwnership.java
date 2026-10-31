package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** A lost legacy input receipt blocks native takeover until explicitly reconciled. */
final class ControllerOwnership {
 static final File MARKER=new File("/data/local/tmp/codex-lastz-helper/legacy-input.json");
 static void check()throws Exception{check(MARKER);}
 static void check(File file)throws Exception{if(file.exists()){JSONObject record=new JSONObject(StateProbe.text(file.getPath()));if(record.getInt("schema")!=1||record.getBoolean("pending"))throw new IOException("Previous Python input is unconfirmed; reconcile before another controller takes ownership");}}
}
