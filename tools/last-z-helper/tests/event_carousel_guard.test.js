const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(__dirname,'../input-agent-tail.js'),'utf8');const at=source.indexOf('function eventCarouselGesture(');assert(at>=0);const context={};vm.runInNewContext(source.slice(at),context);
const args={action:'ui-swipe',eventCarousel:true,direction:'left',path:'UIManagerInstance/windows/UIActivityCenterTable/View/tabScrollViewN',child:'Viewport'},state={scene:1,modals:1,windowState:2,name:'Danger Lurks',id:'40005',type:21},bounds={left:187,right:1080,y:2046};let checks=0;
const g=context.eventCarouselGesture(args,state,bounds);assert(g.x>g.endX&&g.y===g.endY&&g.x<1080&&g.endX>187);checks++;
for(const [key,value] of Object.entries({action:'ui-tap',eventCarousel:false,direction:'up',path:'wrong',child:'wrong'})){assert.throws(()=>context.eventCarouselGesture({...args,[key]:value},state,bounds));checks++;}
for(const [key,value] of Object.entries({scene:2,modals:2,windowState:1,name:'Other',id:'40004',type:23})){assert.throws(()=>context.eventCarouselGesture(args,{...state,[key]:value},bounds));checks++;}
for(const b of [{...bounds,left:NaN},{...bounds,right:Infinity},{...bounds,right:200},{...bounds,y:NaN}]){assert.throws(()=>context.eventCarouselGesture(args,state,b));checks++;}
console.log(`Event carousel guard: ${checks} checks passed`);
