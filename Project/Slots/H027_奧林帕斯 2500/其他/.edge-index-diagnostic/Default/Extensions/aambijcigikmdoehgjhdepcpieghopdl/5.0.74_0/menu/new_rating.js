/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

document.addEventListener("DOMContentLoaded", () => {
    let isWithSecure = false;
    chrome.storage.local.get(["port", "guid", "customization"], function (result) {
        isWithSecure = result.customization.ProductName.startsWith('WithSecure');
        parent.document.getElementById("footer-panel").style.removeProperty("display");
        document.querySelectorAll("input[name='safe-status']").forEach((input) => {
            input.addEventListener('change', (event) => {
                if (document.querySelector('input[name="safe-status"]:checked').value) {
                    document.getElementById("btn-new-rating-next").disabled = false;
                };
            });
        });
    });
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.runtime.onMessage.addListener( (result, sender, sendResponse) => {
            if (result.type == "pageinfo") {
                 if (result.isBank) {
                    document.getElementById("banking").parentElement.style.display = "none";
                }
                else if (result.status == "harmful") {
                    document.getElementById("harmful").parentElement.style.display = "none";
                }
                else if (result.status == "suspicious") {
                    document.getElementById("suspicious").parentElement.style.display = "none";
                }
                else if(result.status == "safe") {
                    document.getElementById("safe").parentElement.style.display = "none";
                }

                if (result.status == "category") {
                    document.getElementById("category-selector-label").innerText = chrome.i18n.getMessage(isWithSecure ? "page_wrong_category_ws" : "page_wrong_cat_2");
                }
                else {
					document.getElementById("category-selector-label").innerText = chrome.i18n.getMessage("page_wrong_cat_1");
                }

                let ratingNextButton = document.getElementById("btn-new-rating-next");
                if (ratingNextButton) {
                    ratingNextButton.addEventListener("click", () => {
                        switch(document.querySelector('input[name="safe-status"]:checked').value) {
                            case "banking":
                            case "harmful":
                            case "suspicious":
                            case "safe":
                                window.location.href = "confirmation.html?status=" + document.querySelector('input[name="safe-status"]:checked').value + "&url=" + result.url;
                                break;
                            case "category":
                                window.location.href = "categories.html?status=" + document.querySelector('input[name="safe-status"]:checked').value + "&url=" + result.url;
                                break;
                            default:
                                window.location.href = "success.html"; 
                        }
                    });
                }
            }
            sendResponse();
            return true;
        });

        chrome.runtime.sendMessage( {type: "getstatus", tab: tabs[0]});
    });

    let cancelButton = document.getElementById("btn-cancel-new-rating");
    if (cancelButton) {
        cancelButton.addEventListener("click", () => {
            window.location.href = "wrong_rating.html";
        });
    }    
})
