package dev.codex.lastzhelper;
import android.content.Context;import android.widget.*;
final class SharingControls {
 static RadioGroup create(Context context,String destination,boolean floating){RadioGroup group=new RadioGroup(context);group.setOrientation(RadioGroup.VERTICAL);
  for(int id=1;id<=2;id++){RadioButton button=new RadioButton(context);button.setId(id);button.setText(id==1?"Trucks group":"World Chat");if(floating)button.setTextColor(0xffffffff);group.addView(button);}
  group.check(ShareDestination.GROUP.equals(ShareDestination.checked(destination))?1:2);
  group.setOnCheckedChangeListener((view,id)->context.getSharedPreferences("runs",0).edit().putString("shareDestination",selected(view)).apply());return group;
 }
 static String selected(RadioGroup group){int id=group.getCheckedRadioButtonId();if(id!=1&&id!=2)throw new IllegalArgumentException("Choose a share destination");return id==1?ShareDestination.GROUP:ShareDestination.WORLD;}
 static void enabled(RadioGroup group,boolean enabled){if(group!=null)for(int i=0;i<group.getChildCount();i++)group.getChildAt(i).setEnabled(enabled);}
}
