package dev.codex.lastzhelper;
import java.time.*;
/** Pure reset/cooldown rules: no UI, Android services or device wall-clock changes. */
final class MaintenanceSchedule {
 static final class Period {final String key;final long nextResetMs;Period(String key,long nextResetMs){this.key=key;this.nextResetMs=nextResetMs;}}
 static Period daily(long nowMs,String zone,int resetHour){
  if(nowMs<0||resetHour<0||resetHour>23)throw new IllegalArgumentException("Invalid game-day parameters");
  ZoneId z=ZoneId.of(zone);ZonedDateTime now=Instant.ofEpochMilli(nowMs).atZone(z);LocalDate day=now.toLocalDate();
  if(now.isBefore(day.atTime(resetHour,0).atZone(z)))day=day.minusDays(1);
  return new Period(day.toString(),day.plusDays(1).atTime(resetHour,0).atZone(z).toInstant().toEpochMilli());
 }
 static long retryAt(long nowMs,int consecutiveFailures,long baseMs,long maxMs){
  if(nowMs<0||consecutiveFailures<1||baseMs<1||maxMs<baseMs)throw new IllegalArgumentException("Invalid retry policy");
  long delay=baseMs;for(int i=1;i<consecutiveFailures&&delay<maxMs;i++)delay=delay>maxMs/2?maxMs:Math.min(maxMs,delay*2);
  return Math.addExact(nowMs,delay);
 }
 static boolean due(long nowMs,long nextDueMs,boolean unresolvedCommit){if(nowMs<0||nextDueMs<0)throw new IllegalArgumentException("Invalid due timestamp");return !unresolvedCommit&&nowMs>=nextDueMs;}
 static String feature(String value){if(value==null||!value.matches("[a-z][a-z0-9_-]{0,63}"))throw new IllegalArgumentException("Invalid feature ID");return value;}
 static String uid(String value){if(value==null||!value.matches("[0-9]{8,24}"))throw new IllegalArgumentException("Invalid character UID");return value;}
 static String operation(String feature,String period,String target){feature(feature);if(period==null||!period.matches("[A-Za-z0-9_-]{1,64}")||target==null||!target.matches("[A-Za-z0-9_-]{1,64}"))throw new IllegalArgumentException("Invalid operation identity");return feature+":"+period+":"+target;}
}
