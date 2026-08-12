/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function fsQueryOrspRatingBackground(url, id, callback) {
    var request = {
        fsOlsRequest: url
    };

    var port = chrome.runtime.connect();
    port.postMessage(request);
    port.onMessage.addListener(function (response) {
        callback(id, response);
    });
}

