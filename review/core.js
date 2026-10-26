const ReviewCore = (() => {
  const fields = ['case_id','permission','block_justification','format','policy_clause','prefix_evidence','rationale'];
  const choices = {permission:['required','permitted','forbidden','uncertain'],block_justification:['justified','unnecessary','uncertain'],format:['compliant','breach','uncertain']};
  function complete(row) { return row && Object.entries(choices).every(([k,v])=>v.includes(row[k])) && fields.slice(4).every(k=>typeof row[k]==='string' && row[k].trim()); }
  function validate(state, cases, hash) {
    if (!state || state.packet_sha256!==hash || !state.rows || typeof state.rows!=='object' || Array.isArray(state.rows)) throw Error('This checkpoint belongs to a different review packet.');
    for (const k of ['reviewer','experience','relationship']) if (typeof state[k]!=='string') throw Error('Invalid reviewer profile.');
    for (const k of ['independent','attest']) if (typeof state[k]!=='boolean') throw Error('Invalid declaration.');
    const allowed=new Set(cases.map(c=>c.case_id));
    for (const [id,row] of Object.entries(state.rows)) {
      if (!allowed.has(id) || !row || typeof row!=='object' || Array.isArray(row) || Object.keys(row).some(k=>!fields.slice(1).includes(k))) throw Error('Unknown case in checkpoint.');
      for (const k of fields.slice(1)) if (row[k]!==undefined && (typeof row[k]!=='string'||row[k].length>50000)) throw Error('Invalid response field.');
      for (const [k,opts] of Object.entries(choices)) if (row[k] && !opts.includes(row[k])) throw Error('Invalid label in checkpoint.');
    }
    return state;
  }
  function csv(rows) {
    const cell=x=>{let s=String(x??'');if (/^[=+@-]/.test(s)) s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
    return [fields,...rows.map(r=>fields.map(f=>r[f]??''))].map(row=>row.map(cell).join(',')).join('\r\n')+'\r\n';
  }
  return {fields,choices,complete,validate,csv};
})();
if (typeof module!=='undefined') module.exports=ReviewCore;
