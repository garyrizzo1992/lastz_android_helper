package dev.codex.lastzhelper;
/** Only definitive nonexistence is permanent; temporary/unopened states are not. */
public final class DeadStatePolicy {
 public static String message(String value){return value.replaceAll("<[^>]*>","").trim().replaceAll("\\s+"," ");}
 public static boolean permanent(String value){return message(value).equalsIgnoreCase("The State you are searching for does not exist.");}
 public static int state(int state){if(state<1||state>9999)throw new IllegalArgumentException("State must be1to9999");return state;}
}
