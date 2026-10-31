package dev.codex.lastzhelper;
import java.util.regex.*;
/** Match the focused Window token to its owning Android session, not its title. */
final class ProcessWindows {
 static String focusedPid(String windows){
  Matcher focus=Pattern.compile("mCurrentFocus=Window\\{([^ ]+)").matcher(windows);
  if(!focus.find())return "";String token=focus.group(1);boolean current=false;
  for(String line:windows.split("\n")){if(line.trim().startsWith("Window #"))current=line.contains("Window{"+token+" ");if(current){Matcher session=Pattern.compile("mSession=Session\\{[^ ]+ (\\d+):").matcher(line);if(session.find())return session.group(1);}}
  return "";
 }
}
