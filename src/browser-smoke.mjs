import assert from 'node:assert/strict';
import {chromium} from 'playwright';
if(process.getuid)assert.notEqual(process.getuid(),0,'Run the image as its unprivileged user');
const channel=process.env.LIFECYCLE_BROWSER_CHANNEL;
const browser=await chromium.launch({headless:true,...(channel?{channel}:{})});
let attempted=0;
try{
 const context=await browser.newContext();
 await context.route('**/*',route=>{attempted++;return route.abort()});
 const page=await context.newPage();await page.setContent('<title>Fictional worker check</title><button>Ready</button>');
 assert.equal(await page.getByRole('button').textContent(),'Ready');assert.equal(attempted,0);
 console.log(JSON.stringify({syntheticBrowser:'passed',externalRequests:0,unprivileged:process.getuid?true:'not_checked_on_windows',runtime:channel?'local-installed-browser':'image-chromium'}));
 await context.close();
}finally{await browser.close();}
