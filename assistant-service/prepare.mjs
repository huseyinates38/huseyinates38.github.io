import {mkdir,writeFile} from 'node:fs/promises';
const url='https://huseyinates38.github.io/assets/assistant-context.json';
const response=await fetch(url,{redirect:'error',signal:AbortSignal.timeout(20000)});
if(!response.ok)throw Error('Published knowledge is unavailable; deploy the Pages update first.');
const text=await response.text();if(text.length>5000000)throw Error('Knowledge too large');
const data=JSON.parse(text);
if(!/^[a-f0-9]{16}$/.test(data.revision||''))throw Error('Invalid knowledge revision');
for(const lang of ['en','tr']){
 if(!Array.isArray(data[lang]?.records)||data[lang].records.length<100)throw Error('Knowledge incomplete');
 for(const r of data[lang].records)if(typeof r.text!=='string'||typeof r.title!=='string'||!(/^[a-z0-9-]+\.html(?:#[\w-]+)?$/).test(r.url)||r.url.startsWith('person-tugce-unsal.html'))throw Error('Invalid or excluded knowledge record');
}
await mkdir('data',{recursive:true});await writeFile('data/knowledge.json',text);
await mkdir('public',{recursive:true});await writeFile('public/index.html','<!doctype html><meta charset="utf-8"><title>Academic conversation service</title><p>API service for the academic website. Chat requires explicit consent and owner-enabled quota.</p>');
console.log('Knowledge revision:',data.revision);
