const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(__dirname+'/../input-agent-tail.js','utf8');
const context=vm.createContext({});vm.runInContext(source.slice(0,source.indexOf('function execute(')),context);
const lookup=context.cachedLuaStringField,mem=new Map(),strings=new Map();let reads=0,checks=0;
class Pointer{
 constructor(address){this.address=address;}
 add(n){return new Pointer(this.address+n);}
 readU8(){reads++;return mem.get(this.address)||0;}
 readPointer(){reads++;return new Pointer(mem.get(this.address)||0);}
 equals(other){return this.address===other.address;}
 toString(){return '0x'+this.address.toString(16);}
}
const pointer=n=>new Pointer(n),table=pointer(100),slots=new Map();
function layout(nodes,log=8){mem.set(111,log);mem.set(124,nodes);}
function field(nodes,index,key,value,tag=5){const at=nodes+index*24,keyAt=100000+at;mem.set(at,value);mem.set(at+8,tag);mem.set(at+9,4);mem.set(at+16,keyAt);strings.set(keyAt,key);}
let readString=p=>{reads++;if(!strings.has(p.address))throw Error('Invalid string');return strings.get(p.address);};
function get(key='uid'){return lookup(table,key,p=>readString(p),slots).address;}
function check(condition){assert(condition);checks++;}
layout(1000);field(1000,240,'uid',7);
reads=0;check(get()===7);const cold=reads;reads=0;check(get()===7);check(reads<cold/10);
// The location is cached, but the UID/state value must always be read again.
mem.set(1000+240*24,8);check(get()===8);
// A rehash replaces the node pointer, even when the hash size stays the same.
layout(20000);field(20000,220,'uid',9);check(get()===9);
// Same allocation, new field position/key: reject the old slot and search afresh.
field(20000,220,'other',1);field(20000,221,'uid',10);check(get()===10);
// Nil/deleted values cannot pass through an old cached field.
mem.set(20000+221*24+8,0);assert.throws(()=>get(),/field missing/);checks++;
field(20000,221,'uid',11);check(get()===11);
// Key-type changes and log changes invalidate the cached location.
mem.set(20000+221*24+9,3);assert.throws(()=>get(),/field missing/);checks++;
layout(20000,9);field(20000,300,'uid',12);check(get()===12);
// Reusing a table address with a different key/value must not return an old UID.
field(20000,300,'new-key',13);assert.throws(()=>get(),/field missing/);checks++;
// A rehash while validating a cached key is retried against the current layout.
layout(40000);field(40000,2,'uid',14);check(get()===14);
const normal=readString;let changed=false;
readString=p=>{const key=normal(p);if(!changed){changed=true;layout(60000);field(60000,4,'uid',15);}return key;};
check(get()===15);readString=normal;
// An unstable table exhausts the bounded retry rather than returning a stale slot.
slots.clear();readString=p=>{const key=normal(p);layout(mem.get(124)===60000?40000:60000);return key;};
assert.throws(()=>get(),/table changed/);checks++;readString=normal;
layout(60000,19);assert.throws(()=>get(),/table bound/);checks++;
// Per-request cache growth remains bounded without suppressing missing-field errors.
layout(60000,8);slots.clear();for(let i=0;i<140;i++)field(60000,i,'field'+i,i+1);
for(let i=0;i<140;i++)check(get('field'+i)===i+1);
check(slots.size<=128);assert.throws(()=>get('absent'),/field missing/);checks++;
console.log(`Passed ${checks} native field-cache checks; warm lookup reads bounded independently of hash capacity`);
