package dev.codex.lastzhelper;
public final class BoomerNavigationTests {
 static int checks;static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 public static void main(String[]args){String card=BoomerNavigationPolicy.EVENT+"groupItems/372337/tabItems/40005/btn";
  for(String path:new String[]{BoomerNavigationPolicy.HOME,BoomerNavigationPolicy.ENTRY,card,BoomerNavigationPolicy.AUTO,BoomerNavigationPolicy.DIALOG+"closeBtnN",BoomerNavigationPolicy.EVENT+"bottomCloseBtn"}){
   expect(BoomerNavigationPolicy.permits("ui-tap",path,true),"Preview may navigate");expect(BoomerNavigationPolicy.permits("ui-tap",path,false),"Live may navigate");expect(!BoomerNavigationPolicy.permits("ui-swipe",path,false),"No arbitrary swipe");
  }
  expect(!BoomerNavigationPolicy.permits("ui-tap",BoomerNavigationPolicy.DIALOG+"autoJoinBtnN",true),"Preview cannot activate");expect(BoomerNavigationPolicy.permits("ui-tap",BoomerNavigationPolicy.DIALOG+"autoJoinBtnN",false),"Live exact activate");
  for(String path:new String[]{BoomerNavigationPolicy.DIALOG+"stopBtn",BoomerNavigationPolicy.DIALOG+"eventItem1",BoomerNavigationPolicy.DIALOG+"buyBtn",card+"/other",""})expect(!BoomerNavigationPolicy.permits("ui-tap",path,false),"No Off/options/purchase/arbitrary descendant");
  String path=BoomerNavigationPolicy.EVENT+"tabScrollViewN";expect(BoomerNavigationPolicy.carousel("ui-swipe",path,"Viewport","left",true),"Exact native carousel");
  expect(!BoomerNavigationPolicy.carousel("ui-tap",path,"Viewport","left",true),"No viewport tap");expect(!BoomerNavigationPolicy.carousel("ui-swipe",path,"Viewport/Content","left",true),"No arbitrary descendant");expect(!BoomerNavigationPolicy.carousel("ui-swipe",path,"Viewport","up",true),"No other direction");expect(!BoomerNavigationPolicy.carousel("ui-swipe",path,"Viewport","left",false),"Native guard required");
  expect(BoomerNavigationPolicy.carousel("ui-swipe",path,"Viewport","right",true),"Exact native reverse carousel");
  expect(BoomerNavigationPolicy.card(BoomerNavigationPolicy.EVENT+"groupItems/372338/tabItems/40005/btn"),"Group changes retain exact event identity");
  expect(!BoomerNavigationPolicy.card(BoomerNavigationPolicy.EVENT+"groupItems/../other/tabItems/40005/btn"),"No path escape");
  System.out.println("Auto Boomer request scope: "+checks+" checks passed");
 }
}
