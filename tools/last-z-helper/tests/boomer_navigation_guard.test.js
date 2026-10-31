const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../input-agent-tail.js'),'utf8'),context={};vm.runInNewContext(source.slice(source.indexOf('function boomerCardPath(')),context);
const e='UIManagerInstance/windows/UIActivityCenterTable/View/',d='UIManagerInstance/windows/UIAllianceAutoJoinRally/View/';
const paths={'home':'UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn','entry':'UIManagerInstance/windows/MainUI_SU/View/rightLayer/activityViewBtnSlg','card':e+'groupItems/372337/tabItems/40005/btn','dialog':e+'panelComponentList/40005/autoBtnN','close-dialog':d+'closeBtnN','close-event':e+'bottomCloseBtn'};let checks=0;
for(const [route,control] of Object.entries(paths)){
 const a={action:'ui-tap',path:control,boomerRoute:route},s={scene:route==='home'?2:1,modals:['entry','home'].includes(route)?0:route==='close-dialog'?2:1,baseState:2,centerState:2,dialogState:2,id:'40005',type:21,name:'Danger Lurks',event:'40005',panelEvent:'40005',knownWindows:true};
 assert.strictEqual(context.boomerNavigationGuard(a,s),true);checks++;
 for(const [key,value]of Object.entries({parent:1,action:'ui-swipe',path:d+'stopBtn',boomerRoute:'other',child:'other',label:'Activate'})){assert.throws(()=>context.boomerNavigationGuard({...a,[key]:value},s));checks++;}
 for(const [key,value]of Object.entries({scene:3,modals:4,knownWindows:false})){assert.throws(()=>context.boomerNavigationGuard(a,{...s,[key]:value}));checks++;}
 if(['entry','home'].includes(route)){assert.throws(()=>context.boomerNavigationGuard(a,{...s,baseState:1}));checks++;}
 else{assert.throws(()=>context.boomerNavigationGuard(a,{...s,centerState:1}));checks++;}
 if(['card','dialog','close-dialog'].includes(route))for(const [key,value]of Object.entries({id:'40006',type:23})){assert.throws(()=>context.boomerNavigationGuard(a,{...s,[key]:value}));checks++;}
 if(route==='card'){assert.throws(()=>context.boomerNavigationGuard(a,{...s,name:'Other'}));checks++;}
 if(['dialog','close-dialog'].includes(route))for(const key of ['event','panelEvent']){assert.throws(()=>context.boomerNavigationGuard(a,{...s,[key]:'40004'}));checks++;}
 if(route==='close-dialog'){assert.throws(()=>context.boomerNavigationGuard(a,{...s,dialogState:1}));checks++;}
}
assert.strictEqual(context.boomerRouteForPath(d+'autoJoinBtnN'),'');checks++;
assert.strictEqual(context.boomerRouteForPath(d+'stopBtn'),'');checks++;
// Production must invoke guards during measurement and again at dispatch.
assert.strictEqual((source.match(/checkBoomerNavigation\(\);checkBoomerActivation\(\);/g)||[]).length,2);checks++;
const viewport={left:180,right:1080,top:1900,bottom:2160},card={left:200,right:400,top:1950,bottom:2100};assert(context.eventCardVisible(card,viewport));checks++;
for(const change of [{left:170},{right:1081},{top:1899},{bottom:2161},{left:NaN},{right:Infinity},{right:200}]){assert.strictEqual(context.eventCardVisible({...card,...change},viewport),false);checks++;}
assert.strictEqual(context.eventCardVisible(card,{...viewport,right:100}),false);checks++;
const carousel={eventCardPath:e+'groupItems/372338/tabItems/40005/btn',action:'ui-swipe',path:e+'tabScrollViewN',eventCarousel:true,child:'Viewport',direction:'left'},carouselState={scene:1,centerState:2,modals:1,knownWindows:true};
assert(context.boomerNavigationGuard(carousel,carouselState));checks++;assert(context.boomerNavigationGuard({...carousel,direction:'right'},carouselState));checks++;
for(const [key,value]of Object.entries({action:'ui-tap',eventCarousel:false,child:'other',direction:'up'})){assert.throws(()=>context.boomerNavigationGuard({...carousel,[key]:value},carouselState));checks++;}
for(const [key,value]of Object.entries({scene:2,centerState:1,modals:2,knownWindows:false})){assert.throws(()=>context.boomerNavigationGuard(carousel,{...carouselState,[key]:value}));checks++;}
assert(context.boomerCardPath(e+'groupItems/372338/tabItems/40005/btn'));checks++;
assert.strictEqual(context.boomerRouteForPath(e+'groupItems/372338/tabItems/40005/btn'),'card');checks++;
for(const group of ['../other','0','x','1/other','12345678901234567']){assert.strictEqual(context.boomerCardPath(e+'groupItems/'+group+'/tabItems/40005/btn'),false);checks++;}
console.log(`Auto Boomer navigation: ${checks} checks passed`);
