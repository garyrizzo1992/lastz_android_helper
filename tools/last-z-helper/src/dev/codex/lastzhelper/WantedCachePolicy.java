package dev.codex.lastzhelper;

import java.util.List;

/**
 * Interprets a hidden shortcut's already-loaded personal cache without declaring
 * server completeness. The reader must first validate row types and UUID links.
 */
final class WantedCachePolicy {
 enum Decision { VISIBLE, NO_READY_IN_LOADED_CACHE, BLOCKED }

 static Decision classify(boolean shortcutHidden,boolean previouslyLoaded,List<String> rowDecisions){
  if(!shortcutHidden)return Decision.VISIBLE;
  if(!previouslyLoaded||rowDecisions==null||rowDecisions.isEmpty()||rowDecisions.size()>64)return Decision.BLOCKED;
  for(String decision:rowDecisions){
   if(!"ALREADY_RECEIVED".equals(decision)&&!"WAITING".equals(decision))return Decision.BLOCKED;
  }
  return Decision.NO_READY_IN_LOADED_CACHE;
 }
}
