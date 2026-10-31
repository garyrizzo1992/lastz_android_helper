package dev.codex.lastzhelper;
import java.io.*;
/** Group IDs vary between Event Center instances; event identity must not. */
final class BoomerEventTarget {
 static String find(GameMemory m)throws Exception{
  String found=null;int count=0;
  for(TruckDiscoveryProbe.Value group:GameMemory.rows(m.path(BoomerNavigationPolicy.EVENT+"groupItems"))){
   if(++count>256)throw new IOException("Event Center group bound");if((group.tag&15)!=5)continue;
   long tabs=GameMemory.optional(group.raw,"tabItems");if(tabs==0)continue;long tab=GameMemory.optional(tabs,"40005");if(tab==0)continue;
   long data=GameMemory.f(tab,"data");if(!"40005".equals(GameMemory.string(data,"id"))||GameMemory.number(data,"type")!=21||!"Danger Lurks".equals(GameMemory.string(data,"name")))throw new IOException("Danger Lurks event identity changed");
   String path=BoomerNavigationPolicy.EVENT+"groupItems/"+group.key+"/tabItems/40005/btn";if(!BoomerNavigationPolicy.card(path)||found!=null)throw new IOException("Ambiguous Danger Lurks event route");found=path;
  }
  if(found==null)throw new IOException("Danger Lurks event is unavailable");return found;
 }
}
