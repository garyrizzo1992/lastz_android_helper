package dev.codex.lastzhelper;
/** Current reward icons, not the number of items inside each icon. */
public final class TruckCargo {
 public static final String ORANGE="210454",MODULE_BOX="253102",MODULE_ICON="car_compon_giftbox_blue";
 public static int icons(String item,int type,long quantity){
  if(!ORANGE.equals(item)&&!MODULE_BOX.equals(item))return 0;
  if(type!=7||quantity<0||quantity>1000000000L)throw new IllegalArgumentException("Invalid truck reward item/type/quantity");
  if(quantity==0)return 0;
  if(MODULE_BOX.equals(item)&&quantity!=2)throw new IllegalArgumentException("Lv.3 module chest icon must contain two items");
  return 1;
 }
 public static int[] payload(String rewards){int fragments=0,boxes=0;
  for(String part:rewards.split("\\|")){String[] fields=part.split(";",-1);if(fields.length!=3)throw new IllegalArgumentException("Malformed truck share reward");
   if(!ORANGE.equals(fields[0])&&!MODULE_BOX.equals(fields[0]))continue;
   int count=icons(fields[0],Integer.parseInt(fields[1]),Long.parseLong(fields[2]));if(ORANGE.equals(fields[0]))fragments+=count;else boxes+=count;
  }return new int[]{fragments,boxes};
 }
 public static boolean valuable(int fragments,int boxes){if(fragments<0||boxes<0)throw new IllegalArgumentException("Unknown cargo counts");return boxes>=4||(fragments>=1&&boxes>=3)||(fragments>=2&&boxes>=2)||fragments>=3;}
}
