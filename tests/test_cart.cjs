const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const html = fs.readFileSync(__dirname + '/../app/webpage/cart.html', 'utf8');
const start = html.indexOf('function checkoutSelected()');
const end = html.indexOf('// Process selectAll', start);
const source = html.slice(start, end);
async function scenario(response, checked, reject = false) {
  const original = [{ProductID:'A', Quantity:2, ListedPrice:10}, {ProductID:'B', Quantity:1, ListedPrice:20}];
  const data = new Map([['cart', JSON.stringify(original)], ['isRegistered','true'], ['userType','customer'], ['CustomerID','C1']]);
  const messages = [];
  const context = {JSON, Map, Math, console, alert: text => messages.push(text),
    localStorage: {getItem:key=>data.get(key), setItem:(key,value)=>data.set(key,value)},
    document:{querySelectorAll:()=>checked.map(value=>({checked:value}))}, window:{location:{href:''}},
    fetch:async()=>{if(reject) throw Error('Network failed'); return {ok:response.ok, json:async()=>response.body};}};
  vm.createContext(context);
  vm.runInContext(source + ';checkoutSelected();', context);
  await new Promise(resolve=>setImmediate(resolve));
  return {cart:JSON.parse(data.get('cart')), messages, location:context.window.location.href, original};
}
(async()=>{
  for(const response of [{ok:false,body:{success:false,message:'Database failed'}}, {ok:true,body:{success:false,message:'Rejected'}}]) {
    const result = await scenario(response,[true,false]);
    assert.deepStrictEqual(result.cart,result.original);
    assert.strictEqual(result.location,'');
    assert(!result.messages.includes('Order(s) confirmed!'));
  }
  const network = await scenario({},[true,false],true);
  assert.deepStrictEqual(network.cart,network.original);
  const success = await scenario({ok:true,body:{success:true}},[true,false]);
  assert.deepStrictEqual(success.cart,[success.original[1]]);
  assert.strictEqual(success.location,'order.html');
  const empty = await scenario({ok:true,body:{success:true}},[false,false]);
  assert.deepStrictEqual(empty.cart,empty.original);
  assert.strictEqual(empty.location,'');
  // Parse every inline script without executing browser side effects.
  for(const file of fs.readdirSync(__dirname+'/../app/webpage').filter(name=>name.endsWith('.html'))) {
    const text = fs.readFileSync(__dirname+'/../app/webpage/'+file,'utf8');
    for(const match of text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) new vm.Script(match[1],{filename:file});
  }
  console.log('PASS: 5 cart scenarios and syntax checks for all inline page scripts');
})().catch(error=>{console.error(error); process.exitCode=1;});
