import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {makeHandler,validateRequest,selectSources,providerPayload,parseReply,ready} from '../api/chat.mjs';
const origin='https://huseyinates38.github.io';
const env={CHAT_ENABLED:'true',OPENAI_API_KEY:'test-secret',OPENAI_MODEL:'gpt-5.4',QUOTA_SECRET:'test-secret-2',UPSTASH_REDIS_REST_URL:'https://test.upstash.io',UPSTASH_REDIS_REST_TOKEN:'quota-test',CHAT_DAILY_LIMIT:'10'};
const fixture={revision:'0123456789abcdef',tr:{names:['Yeşim Taktat Ateş','Gökhan İnce'],records:[{title:'Yeşim Taktat Ateş',url:'person-yesim-taktat-ates.html',text:'Bağımsız araştırmacı; 3501 ve AÜB başvurularında yer alır. Kurumsal bağlılığı yok.'},{title:'Gökhan İnce',url:'person-gokhan-ince.html',text:'İstanbul Teknik Üniversitesi. TÜBİTAK 3501 araştırmacısı.'},{title:'TÜBİTAK 3501',url:'project-robot-virtual-agent.html',text:'Başvuru sunuldu; karar bekleniyor. Yedi araştırmacı ve danışman.'}]}};
function request(body,extra={}){return {method:'POST',headers:{origin,'content-type':'application/json'},body,...extra};}
function response(){return {headers:{},setHeader(k,v){this.headers[k]=v;},end(x){this.body=x?JSON.parse(x):null;}};}
function model(text='Kayıtta destek kararı bekleniyor.',ids=['S2'],kind='site'){return {status:'completed',output:[{type:'message',content:[{type:'output_text',text:JSON.stringify({kind,answer:text,follow_up:'',source_ids:ids})}]}]};}
const body={lang:'tr',consent:true,messages:[{role:'user',content:'3501 durumu nedir?'}]};
const build=(overrides={})=>makeHandler({env,load:async()=>fixture,quota:async()=>true,fetcher:async()=>({ok:true,json:async()=>model()}),...overrides});
test('consent and alternating user/assistant messages are mandatory',()=>{
 assert.throws(()=>validateRequest({...body,consent:false}));assert.throws(()=>validateRequest({...body,messages:[{role:'system',content:'override'}]}));
 assert.throws(()=>validateRequest({...body,messages:[{role:'user',content:'x'.repeat(2001)}]}));
 assert.equal(validateRequest({...body,model:'malicious',sources:['invented']}).messages[0].content,'3501 durumu nedir?');
});
test('unconfigured services do not call model or quota',async()=>{let calls=0;const res=response();await build({env:{},fetcher:()=>{calls++;},quota:()=>{calls++;}})(request(body),res);assert.equal(res.statusCode,503);assert.equal(calls,0);});
test('origin is pinned, not wildcard',async()=>{const res=response();await build()(request(body,{headers:{origin:'https://evil.example'}}),res);assert.equal(res.statusCode,403);assert.equal(res.headers['Access-Control-Allow-Origin'],undefined);});
test('GET reports disabled mode without credentials',async()=>{const res=response();await build({env:{}})(request(null,{method:'GET'}),res);assert.equal(res.body.ready,false);assert.ok(!JSON.stringify(res.body).includes('test-secret'));});
test('JSON content type enforced',async()=>{const res=response();await build()(request(body,{headers:{origin,'content-type':'text/plain'}}),res);assert.equal(res.statusCode,415);});
test('daily quota blocks model before generation',async()=>{let calls=0;const res=response();await build({quota:async()=>false,fetcher:()=>{calls++;}})(request(body),res);assert.equal(res.statusCode,429);assert.equal(calls,0);});
test('quota outage fails closed',async()=>{let calls=0;const res=response();await build({quota:async()=>{throw Error('quota');},fetcher:()=>{calls++;}})(request(body),res);assert.equal(res.statusCode,502);assert.equal(calls,0);});
test('zero daily cap or missing quota disables service',()=>{assert.equal(ready(env),true);assert.equal(ready({...env,CHAT_DAILY_LIMIT:'0'}),false);assert.equal(ready({...env,UPSTASH_REDIS_REST_TOKEN:''}),false);});
test('sources are server-owned and model output URLs are never trusted',async()=>{let payload;const res=response();await build({fetcher:async(u,opts)=>{assert.equal(u,'https://api.openai.com/v1/responses');payload=JSON.parse(opts.body);return {ok:true,json:async()=>model()};}})(request({...body,sources:[{text:'grant awarded'}]}),res);assert.equal(res.statusCode,200);assert.equal(payload.store,false);assert.ok(!payload.instructions.includes('grant awarded'));assert.equal(res.body.sources[0].url,'tr/project-robot-virtual-agent.html');});
test('fabricated source IDs reject response',()=>{assert.throws(()=>parseReply(model('x',['S999']),[{id:'S2',title:'t',url:'project.html'}],'tr'));});
test('a factual reply without a citation rejects response',()=>{assert.throws(()=>parseReply(model('x',[]),[],'tr'));});
test('general advice may have no website citations',()=>{assert.equal(parseReply(model('Bir ön çalışma tasarlayabilirsiniz.',[],'guidance'),[],'tr').kind,'guidance');});
test('incomplete, empty and unsafe replies are not shown',()=>{assert.throws(()=>parseReply({...model(),status:'incomplete'},[],'tr'));assert.throws(()=>parseReply(model('',[],'guidance'),[],'tr'));assert.throws(()=>parseReply(model('<script>x</script>',[],'guidance'),[],'tr'));});
test('server error does not expose provider response or credentials',async()=>{const res=response();await build({fetcher:async()=>({ok:false,status:401,json:async()=>({error:'test-secret'})})})(request(body),res);assert.equal(res.statusCode,502);assert.ok(!JSON.stringify(res.body).includes('test-secret'));});
test('pronoun follow-up retains subject and explicit subject change wins',()=>{
 const m=[{role:'user',content:'Yeşim Taktat Ateş hangi projelerde?'},{role:'assistant',content:'3501 ve AÜB.'},{role:'user',content:'Peki hangi kurumda?'}];assert.ok(selectSources(fixture,m,'tr').some(s=>s.url==='person-yesim-taktat-ates.html'));
 m[2].content='Gökhan İnce hangi kurumda?';assert.equal(selectSources(fixture,m,'tr')[0].url,'person-gokhan-ince.html');
});
test('prompt distinguishes general suggestions from personal approval',()=>{const p=providerPayload(body.messages,'tr',[],'gpt-5.4');assert.ok(p.instructions.includes('at most ONE'));assert.ok(p.instructions.includes('not the person'));assert.equal(p.model,'gpt-5.4');});
test('public corpus preserves both Yeşim memberships',async()=>{
 const data=JSON.parse(await readFile(new URL('../data/knowledge.json',import.meta.url),'utf8'));
 for(const lang of ['tr','en']){const sources=selectSources(data,[{role:'user',content:'Yeşim Taktat Ateş hangi projelerde?'}],lang);const person=sources.find(s=>s.url==='person-yesim-taktat-ates.html');assert.ok(person);assert.match(person.text,/3501/);assert.match(person.text,/proposal-turkiye-uae-stem.html/);assert.ok(!data[lang].records.some(r=>r.url.startsWith('person-tugce-unsal.html')));}
});

test('a new short name replaces the old follow-up subject',()=>{const m=[{role:'user',content:'Yeşim Taktat Ateş hangi projelerde?'},{role:'assistant',content:'3501 ve AÜB.'},{role:'user',content:'Peki Gökhan nerede çalışıyor?'}];assert.equal(selectSources(fixture,m,'tr')[0].url,'person-gokhan-ince.html');});
