/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

var fsGoogleRedirectUrl = /https?:\/\/[\w]*\.google\.[a-z\.]{2,6}\/url\?\S*(?:url|q)=([^&]{4,})/i;
var fsYahooRedirectUrl = /https?:\/\/[\w]*ri*\.search\.yahoo\.[a-z\.]{2,6}\/.*\/ru=([^\/]{4,})/i;
var Balloon = new FsOlsBalloon();

function fsRetrieveRedirectUrl(url, regEx) {
    var match = regEx.exec(url);
    if (match && match.length >= 2) {
        return decodeURIComponent(match[1]);
    }

    return url;
}

function isValidUrl(string) {
    let url;
  
    try {
        url = new URL(string);
    } catch (_) {
        return false;  
    }

    return url.protocol == "http:" || url.protocol == "https:";
}

var getLinks = function(element, parentEl) {
    const links = []
const parentElLowerCase = parentEl ? parentEl.toLowerCase() : null;
    for (link of element.getElementsByTagName("a")) {
        if (isValidUrl(link.href)) {
            // get link if it has specific parent el only
            if (!parentEl || (link.parentElement.nodeName.toLowerCase() == parentElLowerCase)) {
                                    links.push(link);
            }
                    }
    }
    return links;
}

var fsGoogleSearchMarking = function (links, callback) {
    for (var i = 0; i < links.length; ++i) {
        // fl class entries are translate links for which we don't want rating icons
        var link = links[i].querySelector('a:not(.fl)');
        if (link) {
            var realUrl = fsRetrieveRedirectUrl(link.href, fsGoogleRedirectUrl);
            callback(link, realUrl, 'fs-google');
        }
    }
    Balloon.inject();
};

var fsBingSearchMarking = function (elements, callback) {
    for (let elem of elements) {
        const a = elem.querySelector('a');
            if (!a || !isValidUrl(a.href)) {
            continue;
        }
                
                // if href is direct URL then we can use it, else need to get redirect url from 'u=' parameter
        let resultUrl = a.href;
        const url = new URL(resultUrl);
        if (url.hostname.endsWith("bing.com")) {
            let redirectUrl = url.searchParams.get('u');
                    if (redirectUrl) {
                if (redirectUrl.startsWith('a1')) {
                        redirectUrl = redirectUrl.slice(2);
                    }
                    try {
                    resultUrl = decodeURIComponent(atob(redirectUrl));
                }
                catch (e) {
                    console.log(e.message);
                    continue;
                }
            }
        }

        if (!isValidUrl(resultUrl)) {
            console.log("url is not valid: ", resultUrl);
            continue;
        }

        callback(a, resultUrl, 'fs-bing');
    }
    Balloon.inject();
};

var fsYahooSearchMarking = function (links, callback) {
    for (var i = 0; i < links.length; ++i) {
        if (fsMatchParentNode(links[i], 'algo-sr', false, 5)) {
            var realUrl = fsRetrieveRedirectUrl(links[i].href, fsYahooRedirectUrl);
            callback(links[i], realUrl, 'fs-yahoo');
        }
    }
    Balloon.inject();
};

var fsYahooJapanSearchMarking = function (links, callback) {
    for (var i = 0; i < links.length; ++i) {
        if (fsMatchClass(links[i], 'sw-Card__titleInner', true)) {
            callback(links[i], links[i].href, 'fs-yahoo-jp');
        }
    }
    Balloon.inject();
};

var fsDuckDuckGoSearchMarking = function (links, callback) {
    for (var i = 0; i < links.length; ++i) {
        callback(links[i], links[i].href, 'fs-ddg');
    }
    Balloon.inject();
};
