package dev.codex.lastzhelper;
import java.io.*;import org.json.*;import android.system.*;
/** Root workers produce state that the helper's own settings UI must be able to read. */
final class RotationFiles {
 static void write(File file,JSONObject data)throws Exception{
  ShareLedger.atomic(file,data);
  if(Os.getuid()==0&&file.getParentFile().getCanonicalPath().equals(new File("/data/user/0/dev.codex.lastzhelper/files").getCanonicalPath())){
   StructStat parent=Os.stat(file.getParent());Os.chown(file.getPath(),parent.st_uid,parent.st_gid);Os.chmod(file.getPath(),0600);
   DeviceInput.exec(5,"/system/bin/restorecon",file.getPath());
  }
 }
}
