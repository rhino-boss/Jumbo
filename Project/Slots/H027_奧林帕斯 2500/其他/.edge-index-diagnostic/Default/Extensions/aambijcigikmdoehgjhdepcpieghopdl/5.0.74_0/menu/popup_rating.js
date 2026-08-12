/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

class RatingPopup {
    #port;
    #guid;
    #uuid;
    #status = StatusType.Unknown;
    #isBank = false;
    #customization;
    #platform;
    #url;
    #categories = [];
    #isWithSecure = false;

    constructor(port, guid, customization, platform) {
        this.#port = port;
        this.#guid = guid;
        this.#customization = customization;
        this.#platform = platform;

        if (this.#customization && this.#customization.ProductName) {
            this.#isWithSecure = this.#customization.ProductName.startsWith('WithSecure');
        }
    }

    get isRunningOnMac() {
        return this.#platform.os === 'mac' || this.#platform.os === 'cros';
    }

    getI18nMessage(stringId, substitute = "") {
        var msg = "";
        if (this.#isWithSecure) {
            msg = chrome.i18n.getMessage(stringId + "_ws", substitute);
            if (msg) {
                return msg;
            }
        }
        msg = chrome.i18n.getMessage(stringId, substitute);
        return msg ? msg : (">" + stringId);
    }

    #getHostnameFromRegex(url) {
        const matches = url.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i);
        if (matches) {
            return matches[1];
        }
        else {
            return new URL(url).hostname;
        }
    }

    setInfo(info) {
        if (this.#url == info.url) {
            return;
        }

        this.#url = info.url;
        if (!info.url.startsWith("http://") && !info.url.startsWith("https://")) {
            this.#status = StatusType.Invalid;
        }
        else if (info.block && info.block.type == "banking") {
            this.#status = StatusType.Banking;
        }
        else
        {
            if (info.categories.length == 0) {
                this.#status = StatusType.Unknown;
            }
            else {
                const showIllustration = this.#customization.HideIllustration == "False";
                let categories = document.getElementById("categories");
                let categoriesStr = "";
                if (showIllustration) {
                    var span = document.createElement("span");
                    categories.appendChild(span);
                }
                else {
                    categories.style.setProperty("margin-left", "0px");
                    categories.style.setProperty("text-align", "center");
                    let el = document.getElementById("status-icon");
                    this.showElement(el, false);
                    el.style.width = "0px";
                }
                const sortedCats = getSortedCategories(false);
                info.categories.forEach( (el) => {
                    this.#categories.push(Object.keys(el)[0]);
                    sortedCats.forEach( (sorted) => {
                        if (sorted.id == Object.keys(el)[0]) {
                            if (showIllustration) {
                                let img = document.createElement("img");
                                img.setAttribute("src", sorted.logo);
                                img.style.height = "16px";
                                img.style.margin = "2px";
                                img.alt = sorted.name;
                                img.title = sorted.name;
                                span.appendChild(img);
                            }
                            else {
                                if (categoriesStr) {
                                    categoriesStr += ", ";
                                }
                                categoriesStr += sorted.name;
                            }
                            return;
                        }
                    });
                });
                categories.innerText = categoriesStr;

                this.#setStatusWithCategories(info.categories, info.isWhitelisted, info.rating);

                // if page is blocked, keep the same status
                if (info.block) {
                    this.#status = info.block.type;
                }

                // if we have trusted shopping rating, show it
                if (info.rating && info.rating > 0) {
                    document.getElementById("trusted-shopping-rating").appendChild(htmlToElem(this.getTrustedShoppingTemplate(info.rating))); 
                }
                
                if (info.shoppingWebsite) {
                    document.getElementById("fs-strip-img").src = chrome.runtime.getURL("img/ic_place_onlineshop.svg");
                }

                if (!document.getElementById("fs-strip-img").src) {
                    document.getElementById("fs-hostname").style.marginLeft = "16px";
                }
                
            }
        }
    }

    #getVerdict(categoryName, categories) {
      const categoryEntry = categories.filter(category => categoryName in category);
      return categoryEntry.length > 0 ? categoryEntry[0][categoryName] : -1;
  }

    #setStatusWithCategories(categories, isWhitelisted, trustworthiness) {
        if (isWhitelisted) {
            this.#status = StatusType.Allowed;
            return;
        }

        // this whole resolution should happen on the product side

        const safeVerdict = this.#getVerdict('safe', categories);
        const fsoBankingVerdict = this.#getVerdict('fso_banking', categories);
        const illegalVerdict = this.#getVerdict('illegal', categories);

        if (fsoBankingVerdict === 100) {
            this.#isBank = true;
        }

        if (illegalVerdict === 100) {
            this.#status = StatusType.Illegal;
            return;
        }

        switch (safeVerdict) {
            case -100:
            case -80:
                this.#status = StatusType.Harmful;
                break;
            case -20:
                this.#status = StatusType.Suspicious;
                break;
            case 0:
                this.#status = StatusType.Unknown;
                break;
            case 100:
                this.#status = StatusType.Safe;
                break;
            default:
                break;
        }


        if (trustworthiness && trustworthiness > 0) {
            if (this.#status == StatusType.Safe) {
                this.#status = this.#getShoppingRatingSafe(trustworthiness);
            }
            if (this.#status == StatusType.Suspicious) {
                this.#status = this.#getShoppingRatingSuspiciuos(trustworthiness);
            }
        }
    }

    #getShoppingRatingSuspiciuos(trustworthiness) {
        switch (trustworthiness) {
            case 1:
                return StatusType.TrustedShopping1;
            case 2:
            case 3:
            case 4:
            case 5:
                return StatusType.TrustedShopping2;
            default:
                return StatusType.Unknown;
        }
    }

    #getShoppingRatingSafe(trustworthiness) {
        switch (trustworthiness) {
            case 1:
                return StatusType.TrustedShopping1;
            case 2:
                return StatusType.TrustedShopping2;
            case 3:
                return StatusType.TrustedShopping3;
            case 4:
                return StatusType.TrustedShopping4;
            case 5:
                return StatusType.TrustedShopping5;
            default:
                return StatusType.Unknown;
        }
    }

    get localhostPath() {
        return `http://localhost:${this.#port}`;
    }

    get status() {
        return this.#status;
    }

    get isBank() {
        return this.#isBank;
    }

    get url() {
        return this.#url;
    }

    get categories() {
        return this.#categories;
    }

    setSafeContent() {
        if (this.isBank) {
            document.getElementById("status-icon").src = StatusBank;
            document.getElementById("status-text-p1").innerText = this.getI18nMessage("search_rating_isbank");
        }
        else {
            document.getElementById("status-icon").src = StatusSafe;
            document.getElementById("status-text-p1").innerText = this.getI18nMessage("search_rating_safe_p1");
            document.getElementById("status-text-p2").innerText = this.getI18nMessage("search_rating_safe_p2");
        }
        document.getElementById("fs-strip").style.backgroundColor = "#C2F2D2";
        document.getElementById("fs-hostname").innerText = this.#getHostnameFromRegex(this.#url);
    }

    setShoppingRating5() {
        document.getElementById("status-icon").src = StatusSafe;
        document.getElementById("status-text-p1").innerText = this.getI18nMessage("search_rating_safe_p1");
        document.getElementById("status-text-p2").innerText = this.getI18nMessage("search_rating_safe_p2");
        document.getElementById("fs-strip").style.backgroundColor = "#C2F2D2";
        document.getElementById("fs-hostname").innerText = this.#getHostnameFromRegex(this.#url);
    }

    setShoppingRating4() { 
        this.#setStatusContent(StatusSuspicious, "search_rating_shopping_warn", "search_rating_suspicious_p2");
        document.getElementById("fs-strip").style.backgroundColor = "#FFEECC";
        document.getElementById("fs-hostname").innerText = this.#getHostnameFromRegex(this.#url);
    }

    setShoppingRating2() {
        this.#setStatusContent(StatusSuspicious, "search_rating_shopping_suspicious", "search_rating_suspicious_p2");
        document.getElementById("fs-strip").style.backgroundColor = "#FFEECC";
        document.getElementById("fs-hostname").innerText = this.#getHostnameFromRegex(this.#url);
    }

    setShoppingRating1() {
        this.#setStatusContent(StatusHarmful, "search_rating_harmful_p1", "search_rating_suspicious_p2");
        document.getElementById("fs-strip").style.backgroundColor = "#FFCCCC";
        document.getElementById("fs-hostname").innerText = this.#getHostnameFromRegex(this.#url);
    }

    #setStatusContent(status, msg1, msg2) {
        document.getElementById("status-icon").src = status;
        document.getElementById("fs-hostname").innerText = this.#getHostnameFromRegex(this.#url);
        document.getElementById("status-text-p1").innerText = this.getI18nMessage(msg1);
        if (msg2) {
            document.getElementById("status-text-p2").innerText = this.getI18nMessage(msg2);
        }
    }

    setHarmfulContent() {
        this.#setStatusContent(StatusHarmful, "search_rating_harmful_p1", "search_rating_harmful_p2");
        document.getElementById("fs-strip").style.backgroundColor = "#FFCCCC";
    }

    setSuspiciousContent() {
        this.#setStatusContent(StatusSuspicious, "search_rating_suspicious_p1", "search_rating_suspicious_p2");
        document.getElementById("fs-strip").style.backgroundColor = "#FFEECC";
    }

    setCategoryContent() {
        this.#setStatusContent(StatusHarmful, "search_rating_category_status");
        document.getElementById("fs-strip").style.backgroundColor = "#FFCCCC";
    }

    setUnknownContent() {
        this.#setStatusContent(StatusUnknown, "search_rating_unknown");
        document.getElementById("fs-strip").style.backgroundColor = "#F2F2F2";
    }

    setAllowedContent() {
        this.#setStatusContent(StatusInfo, "search_rating_allowed");
        document.getElementById("fs-strip").style.backgroundColor = "#C2F2D2";
    }

    setBankingBlockedContent() {
        this.#setStatusContent(StatusInfo, "banking_blocked_status");
        document.getElementById("content-iframe").src = "banking_blocked.html";
        document.getElementById("fs-strip").style.backgroundColor = "#FFEECC";
    }

    setSharedContent() {
        document.getElementById("logo").src = this.isRunningOnMac ? this.#customization.ProductLogo : `${this.localhostPath}/${ProductLogo}`;
    }

    setNotAvailableContent() {
        this.#setStatusContent(StatusUnknown, "page_not_available");
        document.getElementById("content-iframe").src = "not_available.html"
        document.getElementById("fs-strip").style.backgroundColor = "#F2F2F2";
    }

    setIllegalContent() {
        this.#setStatusContent(StatusHarmful, "page_prohibited");
        document.getElementById("fs-strip").style.backgroundColor = "#C2F2D2";
    }

    getTrustedShoppingTemplate(rating) {
		const actionIcon = chrome.runtime.getURL("img/ic_action_sms.svg");
		const iconEmoji1 = chrome.runtime.getURL("img/ic_emoji_status_1.svg");
		const iconEmoji2 = chrome.runtime.getURL("img/ic_emoji_status_2.svg");
		const iconEmoji3 = chrome.runtime.getURL("img/ic_emoji_status_3.svg");
		const iconEmoji4 = chrome.runtime.getURL("img/ic_emoji_status_4.svg");
		const iconEmoji5 = chrome.runtime.getURL("img/ic_emoji_status_5.svg");

		const reviewText = chrome.i18n.getMessage("trusted_shopping_review");

		let p1 = chrome.i18n.getMessage("trusted_shopping_safe_p1");
		let p2 = chrome.i18n.getMessage("trusted_shopping_safe_p2");
		let bgColor;
		let opacityIconEmoji1 = "0.3", opacityIconEmoji2 = "0.3", opacityIconEmoji3 = "0.3", opacityIconEmoji4 = "0.3", opacityIconEmoji5 = "0.3";
		switch (rating) {
			case 5:
				bgColor = "#C2F2D2";
				opacityIconEmoji5 = "1";
				break;
			case 4:
				bgColor = "#FFE6CC";
				p1 = chrome.i18n.getMessage("trusted_shopping_warning_p1");
				p2 = chrome.i18n.getMessage("trusted_shopping_suspicious_p2");
				opacityIconEmoji4 = "1";
				break;
			case 3:
				bgColor = "#FFE6CC";
				p1 = chrome.i18n.getMessage("trusted_shopping_suspicious_p1");
				p2 = chrome.i18n.getMessage("trusted_shopping_suspicious_p2");
				opacityIconEmoji3 = "1";
				break;
			case 2:
				bgColor = "#FFE6CC";
				p1 = chrome.i18n.getMessage("trusted_shopping_suspicious_p1");
				opacityIconEmoji2 = "1";
				break;
			case 1:
				bgColor = "#FFE6CC";
				p1 = chrome.i18n.getMessage("trusted_shopping_suspicious_p1");
				opacityIconEmoji1 = "1";
				break;
			default:
				p1 = chrome.i18n.getMessage("trusted_shopping_unknown_p1");
				bgColor = "#F2F2F2";
		}
		return `
		<div class="fs-grid-container" style="width: 300px; margin: 8px;">
		  	<div class="fs-grid-item" style="display: initial; text-align: left;">
				<div style="font-size: 16px; margin-top: 18px;">${p1}</div>
				<div style="margin-top: 24px; margin-bottom: 24px; text-align: left;">
					<span style="margin-left: 22px"><img style="vertical-align:middle; height: 40px; opacity: ${opacityIconEmoji1}; display: initial;" src="${iconEmoji1}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 40px; opacity: ${opacityIconEmoji2}; display: initial;" src="${iconEmoji2}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 40px; opacity: ${opacityIconEmoji3}; display: initial;" src="${iconEmoji3}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 40px; opacity: ${opacityIconEmoji4}; display: initial;" src="${iconEmoji4}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 40px; opacity: ${opacityIconEmoji5}; display: initial;" src="${iconEmoji5}"/></span>
				</div>
				<div><span><img style="vertical-align:middle;margin-bottom: 3px; margin-right: 4px; display: initial;" src="${actionIcon}"/></span><span>${reviewText}</span></div>
			<div>
		</div>
		`;
	}

    showElement(el, show) {
        if (el) {
            if (show) {
                el.style.visibility = "visible";
                el.style.display = "block";
            }
            else {
                el.style.visibility = "hidden";
                el.style.display = "none";
            }
        }
    }

    setContent() {
        this.setSharedContent();
        switch (this.#status) {
            case StatusType.Harmful:
                this.setHarmfulContent();
                break;
           case StatusType.Illegal:
                this.setIllegalContent();
                break;
            case StatusType.Category:
                this.setCategoryContent();
                break;
            case StatusType.Suspicious:
                this.setSuspiciousContent();
                break;
            case StatusType.Unknown:
                this.setUnknownContent();
                break;
            case StatusType.Banking:
                this.setBankingBlockedContent();
                break;
            case StatusType.Safe:
                this.setSafeContent();
                break;
            case StatusType.Allowed:
                this.setAllowedContent();
                break;
case StatusType.TrustedShopping5:
                this.setShoppingRating5();
                break;
            case StatusType.TrustedShopping3:
            case StatusType.TrustedShopping4:
                this.setShoppingRating4();
                break;
            case StatusType.TrustedShopping2:
                this.setShoppingRating2();
                break;
            case StatusType.TrustedShoppingUnsafe:
            case StatusType.TrustedShopping1:
                this.setShoppingRating1();
                break;
            default:
                this.setNotAvailableContent();
        }
    }

    setElementsVisibility() {
        this.showElement(document.querySelector(".content-panel"), !this.isRunningOnMac);
    }
}


document.addEventListener("DOMContentLoaded", function(event) {
    chrome.storage.local.get(["port", "guid", "customization", "platform"], (storageResult) => {
        const page = new RatingPopup(storageResult.port, storageResult.guid, storageResult.customization, storageResult.platform);
        chrome.runtime.onMessage.addListener( (request, sender, sendResponse) => {
            if (request.type == "infopopup") {
                page.setInfo(request.info);
                page.setContent();
                page.setElementsVisibility();
                page.showElement(document.getElementById("footer-panel"), storageResult.customization.UseBrandPromise == "True");
                sendResponse();
            }
            else if (request.type == "getstatus") {
                chrome.runtime.sendMessage( {type: "pageinfo", status: page.status, isBank: page.isBank, url: page.url, categories: page.categories} );
            }
            return true;
        });
    });
})