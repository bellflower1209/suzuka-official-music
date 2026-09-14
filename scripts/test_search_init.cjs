/* Reproduce URL-query initialization before the separate catalog fetch resolves. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../assets/search-v31.js'), 'utf8');
(async () => {
  for (const query of ['神代煌牙','魔法が解けても','榎本魅愛','百万告','Streaming Release','Hello Hello Halloween','Over Drive','September Blue']) {
    const listeners = {}, field = {value: ''}, root = {innerHTML: '', textContent: ''};
    const form = {elements:{q:field},addEventListener(){}};
    let completeFetch;
    const response = new Promise(resolve => {completeFetch=resolve;});
    const context = {URLSearchParams,location:{search:'?q='+encodeURIComponent(query)},
      document:{querySelector:selector=>selector==='[data-search-form]'?form:root},
      window:{addEventListener:(name,callback)=>{listeners[name]=callback;}},fetch:()=>response};
    vm.runInNewContext(source, context);
    assert.equal(field.value, query, 'query must be set before either data response');
    completeFetch({json:async()=>({documents:[{title:query,description:'confirmed',type:'Upcoming',contentType:'upcoming',url:'releases/example/',keywords:[]}]})});
    await new Promise(resolve=>setImmediate(resolve));
    assert.ok(root.innerHTML.includes(query),query);
    context.location.search='?q=not-found';listeners.popstate();
    assert.ok(root.innerHTML.includes('該当する公式コンテンツはありません'));
  }
  console.log('Search URL initialization and history regression passed: 8 queries, independent of catalog response order.');
})();
