const fs=require('fs'),vm=require('vm'),assert=require('assert');
const context=vm.createContext({});vm.runInContext(fs.readFileSync(__dirname+'/../gesture-geometry.js','utf8'),context);
const region=(view,blocks)=>context.clearMapRegion(view,blocks),gesture=(r,k,a)=>context.mapGesture(r,k,a);
let checks=0;
function check(view,blocks){const r=region(view,blocks);assert(r.left>=view.left&&r.right<=view.right&&r.top>=view.top&&r.bottom<=view.bottom);for(const b of blocks)assert(!(r.left<b.right&&r.right>b.left&&r.top<b.bottom&&r.bottom>b.top));for(const k of ['east','west','north','south','zoom']){const g=gesture(r,k,k==='zoom'?.24:0);const points=g.pinch?[[g.left,g.y],[g.right,g.y],[g.endLeft,g.y],[g.endRight,g.y]]:[[g.x,g.y],[g.endX,g.endY]];for(const [x,y]of points)assert(x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom);}checks++;return r;}
for(const [w,h]of [[320,640],[1080,2160],[2160,3840],[960,540]]){
 const v={left:0,right:w,top:0,bottom:h};check(v,[]);check(v,[{left:0,right:w,top:0,bottom:h*.2},{left:0,right:w,top:h*.8,bottom:h},{left:w*.8,right:w,top:h*.2,bottom:h*.6}]);
}
const v={left:10,right:1010,top:50,bottom:2050};check(v,[{left:400,right:600,top:700,bottom:1300}]);
assert.throws(()=>region(v,[{...v}]),/No clear/);checks++;
assert.throws(()=>region({...v,right:NaN},[]),/Invalid/);checks++;
assert.throws(()=>region(v,[{left:0,right:0,top:0,bottom:1}]),/Invalid/);checks++;
const r=region(v,[]);assert.throws(()=>gesture(r,'zoom',.3),/bound/);checks++;
assert.throws(()=>gesture(r,'diagonal'),/direction/);checks++;
assert(gesture(r,'east').endX<gesture(r,'east').x);assert(gesture(r,'west').endX>gesture(r,'west').x);checks++;
const inward=gesture(r,'zoom',.1),outward=gesture(r,'zoom',-.1);assert(inward.endLeft>inward.left&&inward.endRight<inward.right);assert(outward.endLeft<outward.left&&outward.endRight>outward.right);checks++;
console.log(`Passed ${checks} geometry scenarios`);
assert(context.unavailableStateMessage('State 22 is not yet open.'));
assert(context.unavailableStateMessage('This server is unavailable'));
assert(!context.unavailableStateMessage('I think this state is unavailable'));
assert(!context.unavailableStateMessage('State 22 is open'));
assert(context.unavailableStateMessage('The State you are searching for does not exist.'));
assert(!context.unavailableStateMessage('The player you are searching for does not exist.'));
assert(!context.unavailableStateMessage('Someone said: The State you are searching for does not exist.'));
console.log('Passed 7 unavailable-state text cases');
