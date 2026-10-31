package dev.codex.lastzhelper;
import java.util.regex.*;
/** Auto Team-Up is independent of manual march/shield restrictions. */
final class BoomerPolicy {
 static final long DURATION=43200000L,RETRY=900000L;enum State {ACTIVE,INACTIVE,BLOCKED}
 static long seconds(String text){
  if("Auto-Join Duration:Disabled".equals(text))return -2;if(text==null)return -1;
  Matcher m=Pattern.compile("^Auto-Join Duration:(?:<color=#[A-Fa-f0-9]{6}>([0-9]{2}:[0-5][0-9]:[0-5][0-9])</color>|([0-9]{2}:[0-5][0-9]:[0-5][0-9]))$").matcher(text);
  if(!m.matches())return -1;String[] parts=(m.group(1)==null?m.group(2):m.group(1)).split(":");long seconds=Integer.parseInt(parts[0])*3600L+Integer.parseInt(parts[1])*60L+Integer.parseInt(parts[2]);return seconds<=DURATION/1000?seconds:-1;
 }

 static State state(long now,long end,long timer,boolean timerVisible,boolean activeInfo,boolean offVisible,String title,String activate,boolean activateVisible,boolean interactable){
  if(now<0||!"Auto Team-Up".equals(title)||!"Activate".equals(activate)||!activateVisible||!interactable)return State.BLOCKED;
  if(end>now&&end-now<=DURATION+5000&&timerVisible&&activeInfo&&offVisible&&timer>=0&&Math.abs((end-now)/1000-timer)<=5)return State.ACTIVE;
  // Observed disabled layout keeps both buttons and the duration panel visible.
  if(end==0&&timer==-2&&timerVisible&&activeInfo&&offVisible)return State.INACTIVE;
  return State.BLOCKED;
 }
 static long nextCheck(long now,long expiry){if(now<0||expiry<=now)throw new IllegalArgumentException("Active expiry required");return Math.min(Math.addExact(now,DURATION),expiry);}
 static boolean activated(long before,long after,long sent,long observed){return sent>=0&&observed>=sent&&observed-sent<=15000&&after>before&&after>=sent+DURATION-5000&&after<=observed+DURATION+5000;}
}
