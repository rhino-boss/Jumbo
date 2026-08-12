/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

/*
*
*
* WARNING! An attempt to modify page content during banking session.
*
*
*/


var BPInterval;

function startBPLoop()
{
    BPInterval = setInterval( () => {
        const minResponse = 100;
        const before = new Date().getTime();
        debugger;
        const after = new Date().getTime();
        if (after - before > minResponse) {
            chrome.runtime.sendMessage( {type: MessageName.DevToolsOpened, url: window.location.href} );
            location.reload();
        }
    }, 100);
};

function endBPLoop()
{
    clearInterval(BPInterval);
};