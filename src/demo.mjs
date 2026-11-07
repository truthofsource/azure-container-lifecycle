import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createJournal} from './journal.mjs';
import {digest,importReport} from './import-cycle.mjs';
const directory=await mkdtemp(join(tmpdir(),'lifecycle-demo-'));
const journal=await createJournal(directory),release=await journal.lock();
try{
 const csv='Header\nFictional row\n';
 const adapter={async preview(type,bytes){return {importType:type,sourceFileSha256:digest(bytes),rowCount:1,reconciliation:{needsReview:0,conflict:0}}},async commit(){return {batchId:'11111111-1111-4111-8111-111111111111',status:'completed',rowCount:1,idempotentReplay:false}}};
 const preview=await importReport({type:'clients',csv,adapter,journal});
 const committed=await importReport({type:'clients',csv,adapter,journal,commit:true});
 const repeated=await importReport({type:'clients',csv,adapter,journal,commit:true});
 console.log(JSON.stringify({fictional:true,networkRequests:0,preview:preview.status,first:committed.status,repeated:repeated.status,rows:committed.rows,actualJournalAndImportRules:true}));
}finally{await release();await rm(directory,{recursive:true,force:true});}
