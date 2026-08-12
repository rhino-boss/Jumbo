/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function getStatusIcon(status, isBank) {
    if (isBank || status == "banking") {
        return StatusBank;
    }
    else if (status == "harmful" || status == "illegal"  || status == "category" ) {
        return StatusHarmful;
    }
    else if (status == "suspicious") {
        return StatusSuspicious;
    }
    else if (status == "safe") {
        return StatusSafe;
    }
    else {
        return StatusUnknown;
    }
}

function getTextByIcon(icon) {
    switch(icon) {
        case StatusBank:
            return chrome.i18n.getMessage("page_banking");
        case StatusHarmful:
            return chrome.i18n.getMessage("page_harmful");
        case StatusSuspicious:
            return chrome.i18n.getMessage("page_suspicious");
        case StatusSafe:
            return chrome.i18n.getMessage("page_safe");
        default:
            return chrome.i18n.getMessage("search_rating_category_unknown");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    let reportButton = document.getElementById("btn-report");
    let backButton = document.getElementById("btn-back");


    backButton.addEventListener("click", () => {
        window.location.href = "new_rating.html";
    });

    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const status = urlParams.get("status");
    const url = urlParams.get("url");
    if (status == "suspicious") {
        document.getElementById("note-suspisous").style.display = "block";
    }
        
    reportButton.addEventListener("click", () => {
        let info = {
            url: url,
            verdict: status,
            categories: [],
            notes: document.getElementById("susp-info").value
        }
        chrome.runtime.sendMessage( {type: "userRating", info: info});
        window.location.href = "success.html";
    });

    document.getElementById("new-status-icon").src = getStatusIcon(status);
    document.getElementById("new-status-icon").title = getTextByIcon(getStatusIcon(status));

    document.getElementById("confirmation-text").innerText = chrome.i18n.getMessage(`page_report_${status}`);

    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.runtime.onMessage.addListener( (result, sender, sendResponse) => {
            if (result.type == "pageinfo") {
                 document.getElementById("old-status-icon").src = getStatusIcon(result.status, result.isBank);
                 document.getElementById("old-status-icon").title = getTextByIcon(getStatusIcon(result.status, result.isBank));
            }
            sendResponse();
            return true;
        });
        chrome.runtime.sendMessage( {type: "getstatus", tab: tabs[0]} );
    });
})
