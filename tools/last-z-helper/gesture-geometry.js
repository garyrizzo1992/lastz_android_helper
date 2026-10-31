// Pure native-pixel geometry. Fractions describe gesture travel, never button positions.
function clearMapRegion(view,blockers){
 const valid=r=>r&&['left','right','top','bottom'].every(k=>Number.isFinite(r[k]))&&r.right>r.left&&r.bottom>r.top;
 if(!valid(view)||!Array.isArray(blockers)||blockers.some(b=>!valid(b)))throw Error('Invalid viewport/blocker geometry');
 const cols=24,rows=32,w=(view.right-view.left)/cols,h=(view.bottom-view.top)/rows,heights=Array(cols).fill(0);let best=null,area=0;
 for(let row=0;row<rows;row++){
  for(let col=0;col<cols;col++){
   const l=view.left+col*w,r=l+w,t=view.top+row*h,b=t+h;
   heights[col]=blockers.some(o=>o.left<r&&o.right>l&&o.top<b&&o.bottom>t)?0:heights[col]+1;
  }
  for(let l=0;l<cols;l++){let high=rows;for(let r=l;r<cols;r++){
   high=Math.min(high,heights[r]);const width=(r-l+1)*w,height=high*h;
   if(width<(view.right-view.left)*.45||height<(view.bottom-view.top)*.1||width*height<=area)continue;
   area=width*height;best={left:view.left+l*w,right:view.left+(r+1)*w,top:view.top+(row-high+1)*h,bottom:view.top+(row+1)*h};
  }}
 }
 if(!best)throw Error('No clear live map gesture region');
 // Inset within the fully clear cells, away from graphic edges.
 const dx=(best.right-best.left)*.04,dy=(best.bottom-best.top)*.04;
 return {left:best.left+dx,right:best.right-dx,top:best.top+dy,bottom:best.bottom-dy};
}
function mapGesture(region,kind,amount){
 if(!region||!['left','right','top','bottom'].every(k=>Number.isFinite(region[k]))||region.right<=region.left||region.bottom<=region.top)throw Error('Invalid gesture region');
 const w=region.right-region.left,h=region.bottom-region.top,cx=(region.left+region.right)/2,cy=(region.top+region.bottom)/2;
 if(kind==='zoom'){
  if(!Number.isFinite(amount)||Math.abs(amount)<.0001||Math.abs(amount)>.24)throw Error('Zoom fraction bound');
  const travel=Math.abs(amount)*w,outer=w*.35,inner=outer-travel;
  return {pinch:true,y:cy,left:cx-(amount>0?outer:inner),right:cx+(amount>0?outer:inner),endLeft:cx-(amount>0?inner:outer),endRight:cx+(amount>0?inner:outer)};
 }
 const shifts={east:[-.3,0],west:[.3,0],north:[0,.3],south:[0,-.3]},v=shifts[kind];if(!v)throw Error('Unknown map direction');
 return {pinch:false,x:cx-v[0]*w,y:cy-v[1]*h,endX:cx+v[0]*w,endY:cy+v[1]*h};
}
function unavailableStateMessage(text){
 const value=String(text).replace(/<[^>]*>/g,'').trim();
 return /^The State you are searching for does not exist\.$/i.test(value)||/^(?:(?:this|the)\s+)?(?:state|server|warzone)(?:\s+\d+)?\s+(?:is\s+)?(?:currently\s+)?(?:unavailable|not\s+(?:yet\s+)?(?:open(?:ed)?|available))(?:[.!]|$)/i.test(value);
}
