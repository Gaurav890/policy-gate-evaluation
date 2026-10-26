const assert=require('node:assert/strict');const C=require('./core.js');
const row={permission:'uncertain',block_justification:'uncertain',format:'uncertain',policy_clause:'Clause 1',prefix_evidence:'Message 2',rationale:'Missing fact'};
assert(C.complete(row));assert(!C.complete({...row,rationale:' '}));assert(!C.complete({...row,permission:'yes'}));
const state={packet_sha256:'abc',reviewer:'QA',experience:'test',relationship:'external',independent:true,attest:false,rows:{CASE001:row}};
assert.equal(C.validate(state,[{case_id:'CASE001'}],'abc'),state);
for(const bad of [{...state,packet_sha256:'bad'},{...state,experience:{}},{...state,rows:{CASE002:row}},{...state,rows:{CASE001:{...row,case_id:'CASE002'}}}])assert.throws(()=>C.validate(bad,[{case_id:'CASE001'}],'abc'));
const csv=C.csv([{case_id:'CASE001',...row,rationale:'=1+1,"quoted"\nnext'}]);assert(csv.includes('"\'=1+1,""quoted""\nnext"'));
console.log('Review validation, completeness, packet separation and CSV escaping passed.');
