package dev.codex.lastzhelper;
public final class TruckRules {
 public static final long LIMIT=440000000L;
 public static int parseSkipState(String value){int state=value.trim().isEmpty()?0:Integer.parseInt(value.trim());if(state<0||state>9999)throw new IllegalArgumentException("Skip truck state must be 0 to 9999 (0 means none).");return state;}
 public static boolean shareAllowed(long serverId,int skipState){return skipState==0||serverId!=skipState;}
 public static int parsePowerLimit(String value){int m=Integer.parseInt(value.trim());if(m<1||m>1000000)throw new IllegalArgumentException("Attack limit must be 1 to 1000000 million.");return m;}
 public static String summary(long power){if(power<=0)throw new IllegalArgumentException("Unknown truck power");return Math.round(power/1000000.0)+"m";}
 public static String classify(int quality,int slots,long power){return classify(quality,slots,power,LIMIT);}
 public static String classify(int quality,int slots,long power,long limit){if(quality!=4&&quality!=5)return "SKIP_GRADE";if(slots<0)return "UNKNOWN";if(slots<2)return "SKIP";if(slots==2)return "WORLD_SHARE_ELIGIBLE";if(power<=0)return "UNKNOWN";return power<limit?"ALERT_TARGET":"WORLD_SHARE_ELIGIBLE";}
}
