const assert=require('node:assert/strict');const C=require('./core.js');
const row={permission:'uncertain',block_justification:'uncertain',format:'uncertain',policy_clause:'Clause 1',prefix_evidence:'Message 2',rationale:'Missing fact'};
assert(C.complete(row));assert(!C.complete({...row,rationale:' '}));assert(!C.complete({...row,permission:'yes'}));
const state={packet_sha256:'abc',reviewer:'QA',experience:'test',relationship:'external',independent:true,attest:false,rows:{CASE001:row}};
const migrated=C.validate(state,[{case_id:'CASE001'}],'abc');assert.equal(migrated.rows,state.rows);assert.equal(migrated.reviewer,'QA');assert.equal(migrated.schema_version,2);for(const key of ['experience','relationship','independent','attest'])assert(!(key in migrated));assert.deepEqual(C.validate(migrated,[{case_id:'CASE001'}],'abc'),migrated);
for(const bad of [{...state,packet_sha256:'bad'},{...state,reviewer:{}},{...state,rows:{CASE002:row}},{...state,rows:{CASE001:{...row,case_id:'CASE002'}}}])assert.throws(()=>C.validate(bad,[{case_id:'CASE001'}],'abc'));
const csv=C.csv([{case_id:'CASE001',...row,rationale:'=1+1,"quoted"\nnext'}]);assert(csv.includes('"\'=1+1,""quoted""\nnext"'));
console.log('Review validation, completeness, packet separation and CSV escaping passed.');
