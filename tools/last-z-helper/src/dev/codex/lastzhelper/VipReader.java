package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Paths below were observed on the pinned phone build, not inferred from screenshots. */
final class VipReader {
 static final String VIEW="UIManagerInstance/windows/UIVip/View/";
 static final String ENTRY="UIManagerInstance/windows/MainUI_SU/View/topLayer/vip_btn";
 static final class Unit {
  final String id,button;final JSONObject control;final VipPolicy.State state;final long seconds,observedMs;
  Unit(String id,String button,JSONObject control,JSONObject opened,JSONObject unopened,JSONObject caption,JSONObject timer,boolean freebies)throws Exception{
   this.id=id;this.button=button;this.control=control;observedMs=timer.getLong("timestampMs");seconds=timer.optBoolean("active")?VipPolicy.countdown(timer.optString("text",null)):-1;
   state=VipPolicy.state(opened.getBoolean("active"),unopened.getBoolean("active"),control.getBoolean("active"),control.getBoolean("interactable"),caption.optString("text",null),seconds>0?timer.getString("text"):null,freebies);
  }
  JSONObject json()throws Exception{return new JSONObject().put("id",id).put("state",state.name()).put("cooldownSeconds",seconds).put("observedMs",observedMs).put("buttonInstanceId",control.getInt("instanceId"));}
 }
 static final class Snapshot {
  final long revision,score,days;final int level;final Unit points,freebies;
  Snapshot(long revision,long score,long days,int level,Unit points,Unit freebies){this.revision=revision;this.score=score;this.days=days;this.level=level;this.points=points;this.freebies=freebies;}
  Unit unit(String id){return "daily_points".equals(id)?points:"daily_freebies".equals(id)?freebies:null;}
  JSONObject json()throws Exception{return new JSONObject().put("revision",revision).put("score",score).put("loginDays",days).put("level",level).put("points",points.json()).put("freebies",freebies.json());}
  long nextDue(){return Math.min(VipPolicy.nextDue(points.observedMs,points.seconds),VipPolicy.nextDue(freebies.observedMs,freebies.seconds));}
 }
 final MaintenanceContext context;VipReader(MaintenanceContext c){context=c;}
 JSONObject control(String name)throws Exception{return context.input.action(new JSONObject().put("action","ui-bounds").put("path",VIEW+name).put("stateOnly",true));}
 Snapshot read()throws Exception{
  context.active();long revision,score,days;int level;
  try(GameMemory m=new GameMemory(context.controller.cache)){
   if(!m.open("UIVip"))throw new IOException("VIP panel is not open");long info=m.path("DataCenter/VIPManager/vipinfo");level=(int)GameMemory.number(info,"level");score=GameMemory.number(info,"score");days=GameMemory.number(info,"loginDays");revision=(long)GameMemory.decimal(info,"lastUpdateTime");
   if(level<0||level>100||revision<=0||GameMemory.number(m.path(VIEW.substring(0,VIEW.length()-1)),"selectVipLevel")!=level)throw new IOException("VIP level/revision changed; no claim sent");
  }
  Unit points=new Unit("daily_points","box_btn",control("box_btn"),control("boxOpened"),control("boxUnOpened"),control("box_btn_text"),control("box_btn_text"),false);
  JSONObject title=control("free_text");if(!title.getBoolean("active")||!"Daily Freebies".equals(title.optString("text")))throw new IOException("Daily Freebies identity not confirmed");
  Unit freebies=new Unit("daily_freebies","free_btn",control("free_btn"),control("freeOpened"),control("freeUnOpened"),control("free_btn_text"),control("free_des_text"),true);
  context.active();try(GameMemory m=new GameMemory(context.controller.cache)){if(!m.open("UIVip")||GameMemory.number(m.path("DataCenter/VIPManager/vipinfo"),"level")!=level)throw new IOException("VIP panel changed while reading");}
  return new Snapshot(revision,score,days,level,points,freebies);
 }
}
