const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../input-agent-tail.js'),'utf8'),context={};vm.runInNewContext(source.slice(source.indexOf('function boomerRouteForPath(')),context);
const e='UIManagerInstance/windows/UIActivityCenterTable/View/',d='UIManagerInstance/windows/UIAllianceAutoJoinRally/View/';
const paths={'entry':'UIManagerInstance/windows/MainUI_SU/View/rightLayer/activityViewBtnSlg','card':e+'groupItems/372337/tabItems/40005/btn','dialog':e+'panelComponentList/40005/autoBtnN','close-dialog':d+'closeBtnN','close-event':e+'bottomCloseBtn'};let checks=0;
for(const [route,control] of Object.entries(paths)){
 const a={action:'ui-tap',path:control,boomerRoute:route},s={scene:1,modals:route==='entry'?0:route==='close-dialog'?2:1,baseState:2,centerState:2,dialogState:2,id:'40005',type:21,name:'Danger Lurks',event:'40005',panelEvent:'40005',knownWindows:true};
 assert.strictEqual(context.boomerNavigationGuard(a,s),true);checks++;
 for(const [key,value]of Object.entries({action:'ui-swipe',path:d+'stopBtn',boomerRoute:'other',child:'other',label:'Activate'})){assert.throws(()=>context.boomerNavigationGuard({...a,[key]:value},s));checks++;}
 for(const [key,value]of Object.entries({scene:2,modals:4,knownWindows:false})){assert.throws(()=>context.boomerNavigationGuard(a,{...s,[key]:value}));checks++;}
 if(route==='entry'){assert.throws(()=>context.boomerNavigationGuard(a,{...s,baseState:1}));checks++;}
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
console.log(`Auto Boomer navigation: ${checks} checks passed`);
