package dev.codex.lastzhelper;
import org.json.JSONObject;
/** Live receipt recording must still have no activation capability. */
public final class BoomerReceiptPermissionsTests {
 static int checks;static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 static JSONObject tap(String path)throws Exception{return new JSONObject().put("action","ui-tap").put("path",path);}
 public static void main(String[]args)throws Exception{
  BoomerReceiptNavigation scope=new BoomerReceiptNavigation();
  for(boolean preview:new boolean[]{false,true}){
   for(String path:new String[]{BoomerNavigationPolicy.HOME,BoomerNavigationPolicy.ENTRY,BoomerNavigationPolicy.AUTO,BoomerNavigationPolicy.DIALOG+"closeBtnN",BoomerNavigationPolicy.EVENT+"bottomCloseBtn"})expect(scope.permitsRequest(tap(path),preview),"Receipt may use exact navigation");
   for(String path:new String[]{BoomerNavigationPolicy.DIALOG+"autoJoinBtnN",BoomerNavigationPolicy.DIALOG+"stopBtn",BoomerNavigationPolicy.DIALOG+"eventItem1",BoomerNavigationPolicy.DIALOG+"buyBtn"})expect(!scope.permitsRequest(tap(path),preview),"Receipt never activates, disables, toggles or buys");
   expect(!scope.permitsRequest(tap(BoomerNavigationPolicy.AUTO).put("label","Activate"),preview),"No label substitution");
   expect(!scope.permitsRequest(tap(BoomerNavigationPolicy.AUTO).put("parent",0),preview),"No ancestor substitution");
   expect(!scope.permitsRequest(tap(BoomerNavigationPolicy.AUTO).put("child","other"),preview),"No arbitrary descendant");
   String card=BoomerNavigationPolicy.EVENT+"groupItems/372338/tabItems/40005/btn";
   for(String direction:new String[]{"left","right"}){
    JSONObject swipe=new JSONObject().put("action","ui-swipe").put("path",BoomerNavigationPolicy.EVENT+"tabScrollViewN").put("child","Viewport").put("direction",direction).put("eventCarousel",true).put("eventCardPath",card);
    expect(scope.permitsRequest(swipe,preview),"Bounded carousel route");
    expect(!scope.permitsRequest(new JSONObject(swipe.toString()).put("eventCarousel",false),preview),"Native carousel flag required");
    expect(!scope.permitsRequest(new JSONObject(swipe.toString()).put("eventCardPath",card.replace("40005","40006")),preview),"Exact event required");
   }
  }
  System.out.println("Auto Boomer receipt permissions: "+checks+" checks passed; live recording cannot activate");
 }
}
