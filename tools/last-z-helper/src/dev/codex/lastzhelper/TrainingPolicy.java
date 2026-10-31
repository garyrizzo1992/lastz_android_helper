package dev.codex.lastzhelper;
/** Completed training only. Hospital/healing, upgrades and new queue starts are separate features. */
final class TrainingPolicy {
 static boolean supported(int type){return type==1||type==8||type==9;}
 static int building(int type){if(type==1)return 423000;if(type==8)return 424000;if(type==9)return 425000;throw new IllegalArgumentException("Not a training queue");}
 static final class Item{final String id;final int count;Item(String id,int count){this.id=id;this.count=count;}}
 static Item item(int type,String encoded){if(!supported(type)||encoded==null||!encoded.matches("107[012][0-9]{2};[1-9][0-9]{0,5};0"))throw new IllegalArgumentException("Unsupported training payload");String[] p=encoded.split(";");char family=type==1?'0':type==8?'1':'2';if(p[0].charAt(3)!=family)throw new IllegalArgumentException("Unit family differs from queue");return new Item(p[0],Integer.parseInt(p[1]));}
 static boolean collected(int state,long beforeFree,long afterFree,long beforeTrain,long afterTrain,int quantity){return state==0&&quantity>0&&beforeFree>=0&&beforeTrain>=quantity&&afterFree>=beforeFree&&afterFree-beforeFree>=quantity&&afterTrain>=0&&afterTrain<=beforeTrain-quantity;}
 static String classify(int type,int state,long now,long start,long end,int buildingId,boolean unlocked,boolean locked,long inTraining,int count,boolean bubbleMatches){
  if(!supported(type))return "EXCLUDED";
  if(buildingId!=building(type)||!unlocked||locked||inTraining<0)return "BLOCKED";
  if(state==0)return inTraining==0?"NOTHING_TO_DO":"BLOCKED";
  if(state==1||state==2)return "WAITING";
  if(state!=3||now<0||start<=0||end<start||end>now||count<=0||inTraining<count||!bubbleMatches)return "BLOCKED";
  return "READY_TO_COLLECT";
 }
}
