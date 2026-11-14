/* Inference runs locally. No prompt, history or generated answer is sent to an API.
 * Official WebLLM runtime, pinned release; official Qwen3 MLC model weights.
 */
let engine=null,working=false;
self.onmessage=async({data})=>{
 if(working)return;
 working=true;
 try{
  if(data.type==='init'){
   const {CreateMLCEngine}=await import('https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.88/lib/index.js');
   engine=await CreateMLCEngine('Qwen3-0.6B-q4f16_1-MLC',{
    initProgressCallback:r=>self.postMessage({type:'progress',progress:r.progress}),logLevel:'ERROR'
   },{context_window_size:4096});
   self.postMessage({type:'ready'});
  }else if(data.type==='ask'&&engine){
   await engine.resetChat();
   const stream=await engine.chat.completions.create({
    messages:data.messages,stream:true,max_tokens:450,temperature:0.2,top_p:0.9,
    extra_body:{enable_thinking:false}
   });
   for await(const part of stream){const text=part.choices?.[0]?.delta?.content;if(text)self.postMessage({type:'token',text});}
   self.postMessage({type:'done'});
  }
 }catch{self.postMessage({type:'error'});}
 finally{working=false;}
};
