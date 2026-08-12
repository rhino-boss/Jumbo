/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

var fs_title_banking; // declare variable to ensure it is defined (may be missing if old resources are used)
var fs_status_info_svg; // declare variable to ensure it is defined (may be missing if old resources are used)

function fsOrspQueryCallback(id, rating, additionalCallback = null) {
    const icon = fsGetRatingResources(rating.rating_status).icon;
    var element = document.getElementById(id);
    if (element) {
        element.src = icon;
        element.dataset.rating = rating.rating_status;
        element.dataset.ext_name = rating.ext_name;
        element.dataset.domain = rating.domain;
        element.dataset.categories = rating.categories;
        element.dataset.trustworthiness = rating.trustworthiness;
        element.dataset.typeIcon = rating.typeIcon;
        element.classList.remove('fs-spin');
        if(additionalCallback !== null) {
            additionalCallback(element)
        }
    }
}

var fsProcessLinkElement = function (element, url, engineClass, additionalCallback = null) {
    const id = fsRatingIcon(element, url, engineClass);
    if (id.length === 0) {
        return;
    }

    if (window.location.protocol.indexOf('https:') === 0) {
        chrome.runtime.sendMessage({
            type: MessageName.RequestURLReputation,
            url: url
        }, (response) => {
            fsOrspQueryCallback(id, response, additionalCallback);
        });
    }
};

function observeGoogleSearchResults(node, callback) {
    if (node === null || node === undefined) {
        return;
    }
    function handleMutations(mutations) {
        callback();
        console.debug("Page changed. Checking for new links...");
    }

    var observer = new MutationObserver(handleMutations);
    var config = { childList: true, subtree: true};
    observer.observe(node, config);
    console.log("Observer attached!");
}

function observeDuckDuckGoResults(node, callback) {

    function handleMutations(mutations) {
        // check unprocessed results only
        const links = document.querySelectorAll('[data-testid="result-title-a"]');
        for (const element of links) {
            if (element.parentNode.getElementsByClassName("fs-bubble-info").length == 0) {
                callback();
                console.log("Updating results...");
            }
        }
    }

    var observer = new MutationObserver(handleMutations);
    var config = { attributes: true, childList: true, subtree: true };
    observer.observe(node, config);
    console.log("Observer attached!");
}

// Bing observer.
/*
Here is a trick:
        The main Bing logic is in JS, so we can not just observe a node with names like 'b_results' or even 'b_content',
    so the closest node is the 'body' node. This node we should observe and check if the mutation type is 'childList'
    and the added node is 'b_content'.

    Not a good way, but I haven't found a better one.
*/
function observeBingSearchResults(callback) {

    const nodeToMonitor = 'b_content'

    function handleMutations(mutations) {
        if(document.readyState === 'complete' ) {
            mutations
            .filter(mutation => mutation.type === 'childList')
            .forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if(nodeToMonitor === node.id) {
                        callback();
                    }
                });
            });
        }
    }

    var observer = new MutationObserver(handleMutations);
    var config = { childList: true }; // We don't need the 'subtree' here because Bing doesn't send it separately.
    observer.observe(document.body, config);
    console.log("Bing observer attached!");
}

// The search results appear always under 'g' div or 'r' h3
function fsGoogleSearchListener() {
    
    function iconTransformCallback(element) {
        // This span element transforms our icon. It has 'scaleY(-1)' so we have to scale it down.
        var transformSpan = element.closest('.V9tjod');
        if(transformSpan !== null) {
            element.style.transform = 'scaleY(-1)';
        }
    }

    function callback() {
        try {
            var links = document.querySelectorAll('div[class="g"], div[class="d4rhi"], div[class="yuRUbf"], div[class^="g "]:not(.g-blk), table div h3');
            fsGoogleSearchMarking(links, function (element, url, engineClass) {
                fsProcessLinkElement(element, url, engineClass, iconTransformCallback);
                fsExtraStyleGoogleSearch(element);
            });

        } catch (e) {
            console.log(e.message);
        }
    }

    callback();

    if ('MutationObserver' in window) {
        // monitoring changes of "People also ask" section
        observeGoogleSearchResults(document.querySelector('div[data-initq]'), callback);

        // monitoring changes which appear when user scrolls the page down (does not always get shown, could be AB testing)
        observeGoogleSearchResults(document.querySelector('#botstuff'), callback);
    }
}

function fsExtraStyleGoogleSearch(element) {
    // This is needed due to the new arrow introduced in Google search results
    // Not having this style causes an overlap between the url text and the arrow

    // We also need this check because sometimes the search results gives a table
    // with no arrow so we want to avoid applying the style if the table is present
    if (element.closest('table') === null) {
        var arrow = element.parentNode.lastElementChild;
        arrow.style.paddingLeft = '20px';

        var text = element.lastElementChild;
        text.style.left = '20px';
    }

    // This element is responsible for aligning the search result header.
    // for some reason the the code above doesnt work sometimes
    //
    // Hint:
    // class = "notranslate HGLrXd NJjxre iUh30 ojE3Fb" left here
    // next div = q0vns -- padding-left here
    var elements = element.getElementsByClassName('HGLrXd');
    for (var i = 0; i < elements.length; i++) {
        elements[i].style.left = '20px';
    }
}

function fsExtraStyleYahooJapanSearch() {
    // This is needed due to an absolute positioned url text in Yahoo Japan search results
    // Not having this style in each element with class 'sw-Card__titleCiteWrapper' causes
    // an overlap between rating icon and url text
    var elements = document.getElementsByClassName('sw-Card__titleCiteWrapper');
    for (var i = 0; i < elements.length; i++) {
        elements[i].style.left = '18px';
    }
}

function fsExtraStyleYahooSearch() {
    for (let element of document.getElementsByClassName('d-f overflowX')) {
        for (let card of element.getElementsByClassName('fs-bubble-info')) {
            card.style.top = "37px";
        }
    }
}

// The search results appear always under 'doc/bd/results/cols/left/main'
function fsYahooSearchListener() {
    try {
        var searchResults = document.getElementById('main');
        var links = getLinks(searchResults);
        fsYahooSearchMarking(links, fsProcessLinkElement);
        fsExtraStyleYahooSearch();
    } catch (e) {
        console.log(e.message);
    }
}

// The search results appear always under 'html/body/contents'
function fsYahooJapanSearchListener() {
    try {
        var searchResults = document.getElementById('contents');
        var links = getLinks(searchResults);
        fsYahooJapanSearchMarking(links, fsProcessLinkElement);
        fsExtraStyleYahooJapanSearch();
    } catch (e) {
        console.log(e.message);
    }
}

function fsBingSearchListener() {
    /*
        b_mcw - sponsored links
        b_results - main result frame
    */
    const nodesToMonitor = ['b_results', 'b_mcw']

    function callback() {
        nodesToMonitor.forEach((nodeName) => {
            try {
                const node = document.getElementById(nodeName);
                if(!node) {
                    return;
                }
                const elements = node.getElementsByTagName('h2');
                fsBingSearchMarking(elements, fsProcessLinkElement);
            } catch (e) {
                console.log(`${nodeName}: ${e.message}`);
            }
        })
    }

    callback();

    if ('MutationObserver' in window) {
        observeBingSearchResults(callback);
    }
}

function fsExtraStyleDuckDuckGoSearch() {
    let elements = document.getElementsByClassName('LQNqh2U1kzYxREs65IJu');
    for (let element of elements) {
        element.style.display = "inline";
    }
}

// The search results appear always under 'links_wrapper' div
function fsDuckDuckGoSearchListener() {
    function callback() {
        try {
            const links = document.querySelectorAll('[data-testid="result-extras-url-link"]');
            fsDuckDuckGoSearchMarking(links, fsProcessLinkElement);
            const sublinks = document.getElementsByClassName('f3uDrYrWF3Exrfp1m3Og');
            fsDuckDuckGoSearchMarking(sublinks, fsProcessLinkElement);
            fsExtraStyleDuckDuckGoSearch();
        } catch (e) {
            console.log(e.message);
        }
    }

    callback();

    // DuckDuckGo "More results" button does not trigger any kind of load event, we have to monitor the page contents
    if ('MutationObserver' in window) {
        observeDuckDuckGoResults(document.getElementById('react-layout'), callback);
    }
}

function fsGetSearchListener() {
    console.log("Injecting search listener");

    var hostName = window.location.hostname;
    if (GoogleDomains.includes(hostName)) {
        console.log("Google detected");
        return fsGoogleSearchListener;
    }

    if (BingDomains.includes(hostName)) {
        console.log("Bing detected");
        return fsBingSearchListener;
    }

    if (YahooDomainsJapan.includes(hostName)) {
        console.log("Yahoo Japan detected");
        return fsYahooJapanSearchListener;
    }

    if (YahooDomains.includes(hostName)) {
        console.log("Yahoo detected");
        return fsYahooSearchListener;
    }

    if (DuckDuckGoDomains.includes(hostName)) {
        console.log("DuckDuckGo detected");
        return fsDuckDuckGoSearchListener;
    }

    return null;
}

function isSearchPage() {
    let hostName = window.location.hostname;
    if(GoogleDomains.includes(hostName) ||
        BingDomains.includes(hostName) ||
        YahooDomains.includes(hostName) ||
        YahooDomainsJapan.includes(hostName) ||
        DuckDuckGoDomains.includes(hostName)) {
            return true;
        }
    return false;
}

const schemaMonitor = new FsSchemaMonitor();
schemaMonitor.start();

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        if (request.type == MessageName.BankingSessionActive) {
            if (request.bankingActive) {
                startBPLoop();
            }
            else {
                endBPLoops();
            }
        }
        sendResponse();
        return true;
    }
);

chrome.storage.local.set({browserInfo: navigator.userAgent});

function modificationHook() {
    chrome.runtime.sendMessage(
        { type: MessageName.GetBankingMode},
        function (response) {
            if (response) {
                startBPLoop();
            }
        }
    );
}

// attach content script only when native messaging host connection is activated
chrome.runtime.sendMessage({ type: MessageName.Init}, response => {
    modificationHook();
    if (response === InitResult.Success && isSearchPage()) {
        console.log("Rating script attached!");
        if (document.readyState === "complete") {
            fsGetSearchListener()();
        } else {
            document.onreadystatechange = function () {
                if (document.readyState === "complete" || document.readyState === "interactive") {
                    document.onreadystatechange = null;
                    fsGetSearchListener()();
                }
            };
        }
    }
});
