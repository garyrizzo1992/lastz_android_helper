package dev.codex.lastzhelper;
import java.util.*;
/** Inventory schema only: no bubble is authorized for collection. */
final class BaseBubblePolicy {
 static boolean identity(String key,long buildingUid,long itemId){return buildingUid>0&&itemId>0&&key.equals("#"+buildingUid);}
 static boolean parameter(String key){return Arrays.asList("uuid","funcUuid","itemId","count","type","buildUuid","queueUuid").contains(key);}
 static boolean sensitiveBuilding(long item){return item==411000||item==423000||item==424000||item==425000;}
 static boolean inventoryIdentity(String item,String uuid,String actualItem,String actualUuid,long count){return item!=null&&item.matches("[1-9][0-9]{0,9}")&&uuid!=null&&uuid.matches("[1-9][0-9]{0,18}")&&item.equals(actualItem)&&uuid.equals(actualUuid)&&count>=0;}
 static String boundedName(String name){return name!=null&&name.matches("[A-Za-z_][A-Za-z0-9_]{0,79}")?name:"";}
}
