const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(__dirname,'../input-agent-tail.js'),'utf8');
const start=source.indexOf('    function checkAllianceMenu(){'),end=source.indexOf('    function checkTruckHide()',start);
assert(start>=0&&end>start);let checks=0;
function fixture(){
 const guild='a'.repeat(32),item={type:3,name:'Help'},win={State:2,View:{_allianceMain:{_buttonListInType:{'#7':{_itemData:item}}}}};
 const tree={UIManagerInstance:{windows:{UIAllianceMainTable:win},windowStack:{length:1}},DataCenter:{AllianceBaseDataManager:{allianceBaseData:{uid:guild}},PlayerInfoDataManager:{selfPlayerData:{allianceId:guild}}}};
 const args={action:'ui-tap',path:'UIManagerInstance/windows/UIAllianceMainTable/View/_allianceMain/_buttonListInType/#7/_btn',allianceMenuType:3,allianceMenuName:'Help',allianceMenuGuild:guild};
 const scope={args,globals:()=>tree,field:(t,k)=>{if(!(k in t))throw Error('missing field');return t[k];},number:(t,k)=>t[k],luaString:x=>x};vm.createContext(scope);vm.runInContext(source.slice(start,end),scope);
 return {args,tree,win,item,run:()=>scope.checkAllianceMenu()};
}
function passes(change=()=>{}){const f=fixture();change(f);assert.doesNotThrow(f.run);checks++;}
function fails(change){const f=fixture();change(f);assert.throws(f.run);checks++;}
passes();passes(f=>{f.args.allianceMenuType=4;f.args.allianceMenuName='Alliance Gifts';f.item.type=4;f.item.name='Alliance Gifts';});
fails(f=>delete f.args.allianceMenuType);fails(f=>delete f.args.allianceMenuGuild);fails(f=>f.item.type=4);fails(f=>f.item.name='Other');fails(f=>f.args.allianceMenuType=9);fails(f=>f.args.action='ui-swipe');fails(f=>f.win.State=3);fails(f=>f.tree.UIManagerInstance.windowStack.length=2);fails(f=>f.tree.DataCenter.PlayerInfoDataManager.selfPlayerData.allianceId='b'.repeat(32));fails(f=>f.tree.DataCenter.AllianceBaseDataManager.allianceBaseData.uid='b'.repeat(32));fails(f=>delete f.win.View._allianceMain._buttonListInType['#7']);
console.log(`Alliance menu guard: ${checks} checks passed`);
