package dev.codex.lastzhelper;
import android.app.*;import android.os.*;import android.content.*;import android.widget.*;import android.view.*;import java.io.*;import java.util.*;import org.json.*;
/** Account and maintenance selection. Opens no game until the user presses a run/setup control. */
public final class RotationActivity extends Activity implements JobRunner.Listener {
 LinearLayout body;TextView status;EditText minutes;RotationProfiles profiles;final List<View> controls=new ArrayList<>();final Map<CheckBox,JSONObject> accounts=new LinkedHashMap<>();final Map<CheckBox,String> featureIds=new LinkedHashMap<>();final Map<CheckBox,JSONObject> featureOwners=new LinkedHashMap<>();
 void label(String value){TextView t=new TextView(this);t.setText(value);t.setPadding(0,12,0,8);body.addView(t);}
 void button(String label,Runnable action,boolean controlled){Button b=new Button(this);b.setText(label);b.setOnClickListener(v->action.run());body.addView(b);if(controlled)controls.add(b);}
 CheckBox check(String label,boolean selected){CheckBox b=new CheckBox(this);b.setText(label);b.setChecked(selected);body.addView(b);controls.add(b);return b;}
 public void onCreate(Bundle state){super.onCreate(state);ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);body.setPadding(20,12,20,24);scroll.addView(body);setContentView(scroll);
  label("Bot accounts and features");label("Opens each selected game, runs its enabled tasks, then visits the next game and repeats until STOP. Trucks and World-map bounty finding run separately.");
  button("Find games (inspect accounts)",()->run(true,true),true);label("Setup opens registered Last Z shortcuts and reads character identities only. It does not claim rewards. Then reopen this screen to choose games.");
  try{profiles=new RotationProfiles(new File(getFilesDir(),"rotation-profiles.json"));for(int n=0;n<profiles.profiles.length();n++){
    JSONObject p=profiles.profiles.getJSONObject(n);CheckBox account=check(p.getString("name")+" — "+p.getJSONObject("launch").getString("shortcutId")+"\nUID "+p.getString("uid"),p.getBoolean("selected"));accounts.put(account,p);
    String[] labels={"VIP free rewards","Alliance Help","Alliance Gifts","Collect finished troops","Collect finished Wanted rewards"};
    for(int f=0;f<RotationPolicy.FEATURES.length;f++){String id=RotationPolicy.FEATURES[f];CheckBox b=check("    "+labels[f],p.getJSONObject("features").getBoolean(id));featureIds.put(b,id);featureOwners.put(b,p);}
    button("Enable all features for "+p.getString("name"),()->allFeatures(p,true),true);button("Disable all features for "+p.getString("name"),()->allFeatures(p,false),true);
    button("Forget setup for "+p.getString("name"),()->forget(p),true);
   }if(profiles.profiles.length()==0)label("No games enrolled. Use Find games first; new games are unselected until you choose them.");
  }catch(Exception e){label("Account settings need attention: "+e);profiles=null;}
  label("Maximum visit duration (minutes)");minutes=new EditText(this);minutes.setSingleLine(true);minutes.setInputType(2);minutes.setText(""+getSharedPreferences("runs",0).getInt("rotationMinutes",20));body.addView(minutes);controls.add(minutes);
  label("Run bot performs selected work and repeats. Preview bot inspects one round without claims. New available features start enabled; your choices are saved.");
  button("Run bot",()->run(false,false),true);button("Preview bot",()->run(false,true),true);button("STOP",()->JobRunner.stop(this),false);
  label("Forgetting setup removes only its rotation profile, never the game or claim/share histories.");
  button("Back to floating controls",()->{try{if(!JobRunner.busy&&profiles!=null)save();startForegroundService(new Intent(this,HelperService.class).setAction("bubble"));finish();moveTaskToBack(true);}catch(Exception e){Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();}},false);
  status=new TextView(this);status.setTextIsSelectable(true);body.addView(status);JobRunner.listeners.add(this);update(JobRunner.state,JobRunner.detail,JobRunner.busy);
 }
 void allFeatures(JSONObject profile,boolean enabled){for(CheckBox b:featureIds.keySet())if(featureOwners.get(b)==profile)b.setChecked(enabled);}
 void save()throws Exception{if(profiles==null)throw new IOException("Account settings cannot be loaded");for(Map.Entry<CheckBox,JSONObject> e:accounts.entrySet())e.getValue().put("selected",e.getKey().isChecked());for(CheckBox b:featureIds.keySet())featureOwners.get(b).getJSONObject("features").put(featureIds.get(b),b.isChecked());profiles.save();}
 void forget(JSONObject profile){if(JobRunner.busy)return;try{save();for(int n=0;n<profiles.profiles.length();n++)if(profiles.profiles.getJSONObject(n)==profile){profiles.profiles.remove(n);profiles.save();recreate();return;}}catch(Exception e){Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();}}
 public void onBackPressed(){try{if(!JobRunner.busy&&profiles!=null)save();}catch(Exception e){Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();}super.onBackPressed();}
 void run(boolean enroll,boolean preview){if(JobRunner.busy)return;try{
   JSONObject o=JobRunner.options(this);if(enroll)o.put("dryRun",true);else{int value=RotationPolicy.minutes(Integer.parseInt(minutes.getText().toString()));save();profiles.selected();getSharedPreferences("runs",0).edit().putInt("rotationMinutes",value).putBoolean("rotationPreview",preview).apply();o=BotRun.options(this,preview).put("visitMinutes",value);}
   startForegroundService(new Intent(this,HelperService.class).setAction(enroll?"maintenance-enroll":"maintenance-rotation").putExtra("options",o.toString()));finish();moveTaskToBack(true);
  }catch(Exception e){Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();}}
 public void update(String s,String detail,boolean busy){if(status!=null)status.setText(s+"\n"+detail);for(View v:controls)v.setEnabled(!busy);}
 public void onDestroy(){JobRunner.listeners.remove(this);super.onDestroy();}
}
