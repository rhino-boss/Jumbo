/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

const PopupLocalizedCategories = {
    adult: "category_adult",
    alcohol_and_tobacco: "category_alcohol_and_tobacco",
    anonymizers: "category_anonymizers",
    artificial_intelligence: "category_artificial_intelligence",
    dating: "category_dating",
    disturbing: "category_disturbing",
    drugs: "category_drugs",
    gambling: "category_gambling",
    hate: "category_hate",
    illegal: "category_illegal",
    shopping_and_auctions: "category_shopping_and_auctions",
    social_networking: "category_social_networks",
    streaming_media: "category_streaming_media",
    warez: "category_illegal_downloads",
    violence: "category_violence",
    weapons: "category_weapons",
    unknown: "category_unknown"
};

const StatusHarmful = "../img/fs_status_denied.svg";
const StatusSafe = "../img/fs_status_ok.svg";
const StatusUnknown = "../img/fs_status_unknown.svg";
const StatusSuspicious = "../img/fs_status_warning.svg";
const StatusBank = "../img/ic_place_bank_ok.svg";
const StatusInfo = "../img/ic_status_info_filled.svg";
const ProductLogo = "images/logo.png";
const schemaMonitor = new FsSchemaMonitor();

function getSortedCategories(skipUnknown = true) {
    let catList = [];
    Object.keys(PopupLocalizedCategories).forEach( (category) => {
        if (category == "unknown" && skipUnknown) {
            return;
        }
        let catObj = {};
        catObj.id = category;
        let loc = chrome.i18n.getMessage(`search_rating_${PopupLocalizedCategories[category]}`);
        catObj.name = loc || PopupLocalizedCategories[category];
        catObj.logo = `../img/categories/${category}.svg`;
        if (loc) {
            catList.push(catObj);
        }
    });
    return catList.sort((a, b) => a.name.localeCompare(b.name));
};

function loadLocalization() {
    chrome.storage.local.get(["customization"], (result) => {
        let isWithSecure = false;
        let productName;
        if (result.customization && result.customization.ProductName) {
            productName = result.customization.ProductName;
            isWithSecure = productName.startsWith('WithSecure');
        }
        document.querySelectorAll('[data-locale]').forEach(elem => {
            if (isWithSecure) {
                elem.innerText = (elem.id == "extension-name") ? productName : chrome.i18n.getMessage(elem.dataset.locale + "_ws", productName);
            }
            if (!elem.innerText) {
                elem.innerText = chrome.i18n.getMessage(elem.dataset.locale, productName);
            }
        });
    });
};

document.addEventListener("DOMContentLoaded", () => {
    loadCommonStyles();
    loadLocalization();
    let contentFrame = document.getElementById("content-iframe");
    if (contentFrame) {
        contentFrame.addEventListener("load", () => {
                document.getElementById("content-panel").style.height = contentFrame.contentWindow.document.body.scrollHeight + 20 + "px";
                // On Firefox retry again in 100ms for several times, since sometimes the height isn't properly calculated 
                for (let i = 1; i < 6; i++) {
                    setTimeout(() => {
                        document.getElementById("content-panel").style.height = contentFrame.contentWindow.document.body.scrollHeight + 20 + "px";
                    }, i * 100)
                }

        })
    }
    schemaMonitor.setSchemaChangedCallback(isDarkMode => {
        if (isDarkMode) {
            document.documentElement.style.setProperty("color-scheme", "dark");
            document.documentElement.style.color = "white";
        } else {
            document.documentElement.style.setProperty("color-scheme", "light");
            document.documentElement.style.color = "black";
        }
    });
    schemaMonitor.start();
})

function htmlToElem(html) {
	let temp = document.createElement('template');
	html = html.trim();
	temp.innerHTML = html;
	return temp.content.firstChild;
}