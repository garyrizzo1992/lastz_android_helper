// Pure conservative candidate projection. This does NOT authorize an input:
// a fresh native raycast must confirm the intended collider, plus UID/focus/scene guards.
function sceneColliderCandidate(g) {
 const finite=Number.isFinite;
 if(!g||!finite(g.width)||!finite(g.height)||g.width<=0||g.height<=0||g.layerVisible!==true||!finite(g.near)||!finite(g.far)||g.near<=0||g.far<=g.near)throw Error('Invalid scene camera');
 if(!Array.isArray(g.projected)||g.projected.length!==8||!Array.isArray(g.blockers))throw Error('Incomplete scene projection or blockers');
 const v=g.viewport,s=g.safeArea;if(!v||!s||![v.x,v.y,v.width,v.height,s.left,s.right,s.top,s.bottom].every(finite)||v.width<=0||v.height<=0)throw Error('Invalid scene viewport');
 const view={left:Math.max(0,v.x,s.left),right:Math.min(g.width,v.x+v.width,s.right),top:Math.max(0,g.height-v.y-v.height,s.top),bottom:Math.min(g.height,g.height-v.y,s.bottom)};
 if(view.right<=view.left||view.bottom<=view.top)throw Error('Empty scene viewport');
 for(const p of g.projected)if(!p||![p.x,p.y,p.z].every(finite)||p.z<=g.near||p.z>=g.far||p.x<=view.left||p.x>=view.right||p.y<=view.top||p.y>=view.bottom)throw Error('Collider clipped or outside camera');
 const xs=g.projected.map(p=>p.x),ys=g.projected.map(p=>p.y),left=Math.min(...xs),right=Math.max(...xs),top=Math.min(...ys),bottom=Math.max(...ys);
 if(right-left<1||bottom-top<1)throw Error('Degenerate collider projection');
 const x=xs.reduce((a,b)=>a+b,0)/xs.length,y=ys.reduce((a,b)=>a+b,0)/ys.length;
 for(const b of g.blockers){if(!b||![b.left,b.right,b.top,b.bottom].every(finite)||b.right<b.left||b.bottom<b.top)throw Error('Invalid UI blocker');if(x>=b.left&&x<=b.right&&y>=b.top&&y<=b.bottom)throw Error('Scene candidate covered by UI');}
 return {x,y,left,right,top,bottom,requiresRaycast:true};
}
function sceneReferenceIdentity(r){
 if(!r||r.tag!==7||r.userValues!==1||r.bytes!==4||!Number.isInteger(r.index)||!Number.isInteger(r.poolLength)||r.poolLength<1||r.poolLength>262144||r.index<0||r.index>=r.poolLength||r.stride!==16||r.next!==-2||typeof r.objectType!=='string'||!Array.isArray(r.allowedTypes)||!r.allowedTypes.includes(r.objectType))throw Error('Invalid or retired scene reference');
 return r.index;
}
function luaIntegerKeyMatches(tag,raw,key){
 if(tag!==3||typeof raw!=='string'||typeof key!=='string'||!/^#[1-9][0-9]{0,18}$/.test(key))return false;
 const expected=key.slice(1);if(expected.length===19&&expected>'9223372036854775807')return false;
 return raw===expected;
}
if(typeof module!=='undefined')module.exports={sceneColliderCandidate,sceneReferenceIdentity,luaIntegerKeyMatches};
