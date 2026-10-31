const assert=require('node:assert/strict');const {sceneColliderCandidate:candidate}=require('../scene-geometry');let checks=0;
function sample(){return {width:100,height:200,near:1,far:100,layerVisible:true,viewport:{x:0,y:0,width:100,height:200},safeArea:{left:0,right:100,top:0,bottom:200},blockers:[],projected:[{x:40,y:80,z:10},{x:60,y:80,z:10},{x:40,y:100,z:10},{x:60,y:100,z:10},{x:41,y:81,z:12},{x:59,y:81,z:12},{x:41,y:99,z:12},{x:59,y:99,z:12}]};}
function rejects(change){const g=sample();change(g);assert.throws(()=>candidate(g));checks++;}
let c=candidate(sample());assert.equal(c.x,50);assert.equal(c.y,90);assert.equal(c.requiresRaycast,true);checks++;
rejects(g=>g.layerVisible=false);rejects(g=>g.projected[0].z=0);rejects(g=>g.projected[0].z=1);rejects(g=>g.projected[0].z=100);rejects(g=>g.projected[0].x=-1);rejects(g=>g.projected[0].y=201);rejects(g=>g.projected[0].x=NaN);rejects(g=>g.projected.pop());rejects(g=>delete g.blockers);rejects(g=>g.blockers=[{left:49,right:51,top:89,bottom:91}]);rejects(g=>g.blockers=[{left:51,right:49,top:89,bottom:91}]);rejects(g=>g.safeArea.left=45);rejects(g=>g.viewport.width=30);rejects(g=>g.projected.forEach(p=>{p.x=50;p.y=90;}));rejects(g=>g.near=-1);rejects(g=>g.far=1);
const g=sample();g.blockers=[{left:0,right:20,top:0,bottom:20}];assert.equal(candidate(g).requiresRaycast,true);checks++;
console.log(`Passed ${checks} scene-candidate geometry scenarios`);

const {sceneReferenceIdentity:identity}=require('../scene-geometry');let identityChecks=0;
function reference(){return {tag:7,userValues:1,bytes:4,index:5447,poolLength:32768,stride:16,next:-2,objectType:'Transform',allowedTypes:['Transform']};}
assert.equal(identity(reference()),5447);identityChecks++;
for(const change of [r=>r.tag=5,r=>r.userValues=0,r=>r.bytes=8,r=>r.index=-1,r=>r.index=r.poolLength,r=>r.index=1.5,r=>r.poolLength=0,r=>r.poolLength=262145,r=>r.stride=8,r=>r.next=-1,r=>r.next=0,r=>r.objectType='DeletedObject',r=>r.allowedTypes=null]){const r=reference();change(r);assert.throws(()=>identity(r));identityChecks++;}
console.log(`Passed ${identityChecks} scene-reference lifecycle scenarios`);

const {luaIntegerKeyMatches:keyMatches}=require('../scene-geometry');let keyChecks=0;
for(const [tag,raw,key,expected] of [[3,'1256861624241766514','#1256861624241766514',true],[3,'1256861624241766515','#1256861624241766514',false],[19,'1256861624241766514','#1256861624241766514',false],[3,'1','#1',true],[3,'1','#01',false],[3,'9223372036854775807','#9223372036854775807',true],[3,'9223372036854775808','#9223372036854775808',false],[3,1256861624241766514,'#1256861624241766514',false]]){assert.equal(keyMatches(tag,raw,key),expected);keyChecks++;}
console.log(`Passed ${keyChecks} exact Lua integer-key scenarios`);
