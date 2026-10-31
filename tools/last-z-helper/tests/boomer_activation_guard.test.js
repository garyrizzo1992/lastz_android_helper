const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');const s=fs.readFileSync(path.join(__dirname,'../input-agent-tail.js'),'utf8'),at=s.indexOf('function boomerActivationGuard('),c={};assert(at>=0);vm.runInNewContext(s.slice(at),c);
const a={action:'ui-tap',path:'UIManagerInstance/windows/UIAllianceAutoJoinRally/View/autoJoinBtnN',boomerAction:'activate',boomerExpiry:0,boomerOption1:true,boomerOption2:true},state={scene:1,modals:2,centerState:2,dialogState:2,event:'40005',panelEvent:'40005',id:'40005',type:21,expiry:0,type1:1,type2:2,option1:true,option2:true};let checks=0;assert(c.boomerActivationGuard(a,state));checks++;
for(const [k,v] of Object.entries({child:'other',label:'Activate',parent:1,action:'ui-bounds',path:'UIManagerInstance/windows/UIAllianceAutoJoinRally/View/stopBtn',boomerAction:'off',boomerExpiry:1,boomerOption1:false,boomerOption2:undefined})){assert.throws(()=>c.boomerActivationGuard({...a,[k]:v},state));checks++;}
for(const [k,v] of Object.entries({scene:2,modals:1,centerState:1,dialogState:1,event:'40004',panelEvent:'40004',id:'40004',type:23,expiry:1793436399939,type1:2,type2:1,option1:false,option2:false})){assert.throws(()=>c.boomerActivationGuard(a,{...state,[k]:v}));checks++;}
assert.throws(()=>c.boomerActivationGuard({...a,boomerOption1:false,boomerOption2:false},{...state,option1:false,option2:false}));checks++;assert.throws(()=>c.boomerActivationGuard({...a,boomerExpiry:'0'},state));checks++;
assert.strictEqual(c.boomerActivationRequired({action:'ui-bounds',path:a.path}),false);checks++;
assert.strictEqual(c.boomerActivationRequired(a),true);checks++;
assert.strictEqual(c.boomerActivationRequired({...a,action:'ui-bounds'}),true);checks++;
assert.strictEqual(c.boomerActivationRequired({action:'ui-swipe',path:a.path}),true);checks++;
assert.strictEqual(c.boomerActivationRequired({action:'ui-bounds',path:'other'}),false);checks++;
assert(c.boomerActivationLabels(['Auto Team-Up','Auto-Join Duration:Disabled','Activate']));checks++;
for(const labels of [['Auto Team-Up','Auto-Join Duration:Disabled','Buy'],['Auto Team-Up','Auto-Join Duration:09:00:00','Activate'],['Other','Auto-Join Duration:Disabled','Activate'],[],['Auto Team-Up','Auto-Join Duration:Disabled','Activate','Purchase']]){assert.throws(()=>c.boomerActivationLabels(labels));checks++;}
console.log(`Auto Boomer native activation: ${checks} checks passed`);
