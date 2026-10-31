package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Opt-in diagnostic counters; disabled in normal app runs. */
final class Perf {
 static boolean enabled;static long reads,bytes,fieldHits,fieldMisses;static final Map<String,long[]> times=new LinkedHashMap<>();
 static long begin(){return enabled?System.nanoTime():0;}
 static void end(String name,long start){if(start==0)return;long[] v=times.get(name);if(v==null){v=new long[2];times.put(name,v);}v[0]++;v[1]+=System.nanoTime()-start;}
 static void read(int n){if(enabled){reads++;bytes+=n;}}
 static void reset(){reads=bytes=fieldHits=fieldMisses=0;times.clear();}
 static JSONObject report()throws Exception{JSONObject result=new JSONObject().put("memoryReads",reads).put("memoryBytes",bytes).put("fieldCacheHits",fieldHits).put("fieldCacheMisses",fieldMisses),t=new JSONObject();for(Map.Entry<String,long[]> e:times.entrySet())t.put(e.getKey(),new JSONObject().put("count",e.getValue()[0]).put("ms",e.getValue()[1]/1e6));return result.put("timings",t);}
}
