package dev.codex.lastzhelper;
/** Inspection policy only. Geometry and an eight-hour label do not authorize a claim. */
final class ChestPolicy {
 static final long CAP_MS=8L*60*60*1000;
 static String inspect(long now,long accumulatedSince,String text,boolean geometryVerified){
  if(now<0||accumulatedSince<=0||accumulatedSince>now||!geometryVerified)return "BLOCKED";
  if("08:00:00".equals(text)&&now-accumulatedSince>=CAP_MS)return "FULL_INSPECTION_ONLY";
  if("08:00:00".equals(text))return "BLOCKED";
  return "NOT_FULL_OR_UNRECOGNIZED";
 }
 static boolean claimable(long now,long since,String title,String time,String caption,boolean active,boolean enabled,int rewards){return since>0&&since<=now&&now-since>=CAP_MS&&"Idle Reward".equals(title)&&"08:00:00 (MAX)".equals(time)&&"Collect".equals(caption)&&active&&enabled&&rewards>0;}
 static long seconds(String value){if(value==null||!value.matches("0[0-8]:[0-5][0-9]:[0-5][0-9]"))return -1;String[] p=value.split(":");long s=Long.parseLong(p[0])*3600+Long.parseLong(p[1])*60+Long.parseLong(p[2]);return s<=CAP_MS/1000?s:-1;}
 static boolean partial(long now,long since,String value){long seconds=seconds(value);return now>=since&&since>0&&now-since<CAP_MS&&seconds>=0&&seconds<CAP_MS/1000&&Math.abs((now-since)-seconds*1000)<=60000;}
 static String period(long accumulatedSince){if(accumulatedSince<=0)throw new IllegalArgumentException("Missing accumulation timestamp");return "since_"+accumulatedSince;}
}
