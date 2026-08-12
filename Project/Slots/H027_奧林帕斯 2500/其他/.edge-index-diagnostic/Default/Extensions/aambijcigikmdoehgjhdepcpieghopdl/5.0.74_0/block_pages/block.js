/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

class BlockPage {
    #port;
    #guid;
    #uuid;
    #url;
    #customization;
    #allowDisabled;
    #platform;
    #intervalId = 0;
    #isWithSecure = false;

    constructor(port, guid, url, uuid, allowDisabled, customization, platform) {
        this.#port = port;
        this.#guid = guid;
        this.#uuid = uuid;
        this.#url = url;
        this.#customization = customization;
        this.#allowDisabled = allowDisabled;
        this.#platform = platform;

        if (this.#customization && this.#customization.ProductName) {
            this.#isWithSecure = this.#customization.ProductName.startsWith('WithSecure');
        }
    }

    get isRunningOnMac() {
        //todo: change to Chrome OS Specific thing
        return this.#platform.os === 'mac' || this.#platform.os === 'cros';
    }

    get localhostPath() {
        return `http://localhost:${this.#port}`;
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

    loadCSS() {
        return new Promise(resolve => {
            let head = document.getElementsByTagName('head')[0];
            let style = document.createElement('link');
            const embeddedFilePath = chrome.runtime.getURL('block_pages/block.css');
            style.href = this.isRunningOnMac ? embeddedFilePath : `${this.localhostPath}/block.css`;
            style.type = 'text/css'
            style.rel = 'stylesheet'
            style.onload = function() {
                console.debug(`block.css was loaded successfully`);
                resolve();
            };
            style.onerror = function() {
                console.error(`block.css failed to load`);
                resolve();
            };
            head.append(style);
        });
    }

    loadImages() {
        document.getElementById('logo').src = this.isRunningOnMac ? this.#customization.ProductLogo : `${this.localhostPath}/images/logo.png`;
        if (this.isRunningOnMac) {
            // hiding Windows shield icon on Mac
            let element = document.querySelector('.shield_icon')
            if(element)
                element.style.visibility = 'hidden';
        }
    }

    loadLocalization() {
        document.querySelectorAll('[data-locale]').forEach(elem => {
            elem.innerText = this.getI18nMessage(elem.dataset.locale, this.#customization.ProductName);
        });
    }

    sendRequest(action) {
        this.isRunningOnMac ? this.sendRequestMac(action) : this.sendRequestWindows(action);
    }

    sendRequestMac(action) {
        switch (action) {
        case BlockPageAction.Allow:
            chrome.runtime.sendMessage({
                type: MessageName.AllowDomain,
                url: this.#url
            });
            break;
        case BlockPageAction.OpenExceptions:
            chrome.runtime.sendMessage({
                type: MessageName.OpenWebExceptions
            });
            break;
        case BlockPageAction.CheckWhitelist:
            chrome.runtime.sendMessage({
                type: MessageName.CheckWhitelist,
                url: this.#url
            }, (info) => {
                if (info && info.whitelisted && info.url) {
                    clearInterval(this.#intervalId);
                    window.location.href = this.#url;
                }
            });
            break;
        }
    }

    sendRequestWindows(action) {
		if (this.#guid && this.#uuid) {
            var xhr = new XMLHttpRequest();
            let url = this.#url;
            let intervalId = this.#intervalId;
            xhr.open('GET', `${this.localhostPath}/${this.#guid}/blockpageapi?action=${action}&id=${this.#uuid}`);
            xhr.setRequestHeader('Content-Type', 'text/plain');
            xhr.onreadystatechange = function() {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    if (this.responseText === 'refresh' && url) {
                        clearInterval(intervalId);
                        window.location.href = url;
                    }
                }
            };
            xhr.send(null);
        }
    }

    makeElementsVisible() {
        this.showElement(document.querySelector(".header"), true);
        this.showElement(document.querySelector(".wrapper"), true);
    }

    showElement(el, show) {
        if (el) {
            if (show) {
                el.style.visibility = "visible";
            }
            else {
                el.style.visibility = "hidden";
            }
        }
    }

    setContent() {
        if (document.getElementById("url")) {
            document.getElementById("url").innerText = this.#url;
        }
        
        if (document.getElementById("report-link")) {
            document.getElementById("report-link").href = `${this.#customization.SampleSubmitUrl}?a=url&suspicious_url=${this.#url}`;
        }

        if (document.getElementById("allow_button")) {
            document.getElementById("allow_button").addEventListener("click", () => this.sendRequest(BlockPageAction.Allow));
        }

        if (document.getElementById("allowed-list")) {
            document.getElementById("allowed-list").addEventListener("click", () => this.sendRequest(BlockPageAction.OpenExceptions));
        }
        
        this.showElement(document.querySelector(".allow_website"), !this.#allowDisabled);
        this.showElement(document.querySelector(".fp_after_allow_website"), this.#customization.OLSSubmitEnable == "True");
        this.showElement(document.querySelector(".bg-harmful"), this.#customization.HideIllustration == "False");
        this.showElement(document.querySelector(".bg-banking"), this.#customization.HideIllustration == "False");
        this.showElement(document.querySelector(".bg-parental"), this.#customization.HideIllustration == "False");
        this.showElement(document.querySelector(".bg-denied"), this.#customization.HideIllustration == "False");
        this.showElement(document.querySelector(".bg-by-fsecure"), this.#customization.UseBrandPromise == "True");

        this.#intervalId = setInterval(() =>this.sendRequest(BlockPageAction.CheckWhitelist), 2000);
    }

    setCategories(categories) {
        var container = document.getElementById('categories-container');
        const showIllustration = this.#customization.HideIllustration == "False";
        var thiz = this;

        categories.forEach(function(category) {
            if (showIllustration) {
                var element = document.createElement('img');
                element.className = 'category';

                if (LocalizedCategories[category] !== undefined) {
                    element.title = thiz.getI18nMessage(LocalizedCategories[category]);
                } else {
                    element.title = `#${category}`; // display the non-localized category.
                }

                element.alt = category;
                element.src = '../img/categories/' + category + '.svg';
                container.appendChild(element);
            }
            else {
                if (container.textContent.length) {
                    container.textContent += ", ";
                }
                if (LocalizedCategories[category] !== undefined) {
                    container.textContent += thiz.getI18nMessage(LocalizedCategories[category]);
                } else {
                    container.textContent += `#${category}`; // display the non-localized category.
                }
            }
        });
    }

    CreateChildUrlList(allowedUrls) {
        var container = document.getElementById("links-container");
        allowedUrls.forEach(function(url) {
            var match = url.match(/^(?:https?:\/\/)?([^\/\?]+)/i);
            var hostname = match ? match[1] : "";

            if ((url.substr(0, 7) !== 'http://') && (url.substr(0, 8) !== 'https://')) { // IE does not support String.startsWith
                url = 'http://' + url;
            }

            var linkImage = document.createElement('img');
            linkImage.className = 'link-image';
            linkImage.src = 'http://' + hostname + '/favicon.ico';
            linkImage.onerror = function () {
                this.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNOCAxNS41QzMuOSAxNS41LjUgMTIuMS41IDhTMy45LjUgOCAuNXM3LjUgMy40IDcuNSA3LjUtMy40IDcuNS03LjUgNy41em0wLTE0QzQuNCAxLjUgMS41IDQuNCAxLjUgOHMyLjkgNi41IDYuNSA2LjUgNi41LTIuOSA2LjUtNi41UzExLjYgMS41IDggMS41eiIgZmlsbD0iIzk5OSIgLz4KICA8cGF0aCBkPSJNMTQuMSA0LjlsLTEuOS0yLjUtLjctLjEtLjEgMS4yLjcuNHYuNWwtLjQuMi0uNS4zLS41Ljl2LjdsLjUuMi44LS40LjItLjUuOC0uMyAxLjYuNi4zIDEuMy0xLjEtLjRoLS43bC0uNC0uM2gtMS4zbC0xIDEuNi4yIDEuMy42LjYgMS4zLS4xLjEgMS42LTEuMiAyLjEgMS42LTEuMSAxLjktNC0uOC0zLjh6TTQuNiAyTDIuMSA0LjhsLS40IDEuOS0uNCAyLjEgMS4xLjJMNCAxMHYxLjJsMS4yIDEuMy43IDIgLjUuMiAxLjQtMS45LjYtMS4zLTEuOC0xLjctMi4zLS41LS41LjQtMS4xLTEuNC0uNy4zVjcuNWwuNi0uMi42LjcuMy0uMi0uMS0uOCAxLjctMS40TDYuNCA1IDQuNyAzLjNsLS44IDEuNUwzIDMuNmwxLjUtMS41IDEgMS4zLjUtLjYtLjYtMS4ySDd2MS41bC42LjYuMi0uN0w5IDIuNWwuMi0xLjEtLjMtLjItNC4zLjh6bTYuMSAxdi44SDEwbC4yLjkuNS0uM3YuOGwuNy0uNi0uNS0xLjZoLS4yeiIgZmlsbD0iIzk5OSIgLz4KPC9zdmc+';
            };

            var linkAnchor = document.createElement('a');
            var linkText = document.createTextNode(url);
            linkAnchor.href = url;
            linkAnchor.title = url;
            linkAnchor.appendChild(linkText);

            var linkContainer = document.createElement('div');
            linkContainer.className = 'link-anchor-container';
            linkContainer.appendChild(linkAnchor);

            var linkItem = document.createElement('div');
            linkItem.className = 'link-item';
            linkItem.appendChild(linkImage);
            linkItem.appendChild(linkContainer);
            container.appendChild(linkItem);
        });

        if (allowedUrls.length < 3) {
            container.style.justifyContent = "center";
        }
    }

    SetChildDescription(allowedUrls) {
        var element = document.getElementById('child-description');
        var description = this.getI18nMessage("blockpage_child_description");
        if (allowedUrls.length == 0) {
            description = this.getI18nMessage("blockpage_child_empty_list_description");
        }
        element.textContent = description;
    }

    SetDomainInfo(registeredAt) {
        var element = document.getElementById('domain-description');
        var description = this.getI18nMessage("blockpage_newly_registered_domain_registered_at");
        if (registeredAt) {
            const date = new Date(registeredAt * 1000);
            description = description + date.toLocaleDateString();
        }
        else {
            description = "";
        }
        element.textContent = description;
    }

}

document.addEventListener("DOMContentLoaded", function(event) {
    chrome.storage.local.get(["port", "guid", "customization", "platform"], async function (result) {
        try {
            const data = JSON.parse(new URLSearchParams(location.search).get("data"));
            const page = new BlockPage(result.port, result.guid, data.url, data.uuid, data.allowDisabled, result.customization, result.platform);
            await page.loadCSS();
            page.loadLocalization();
            page.loadImages();
            page.setContent();
            await loadCommonStyles();

            switch(data.type) {
              case "category":
                page.setCategories(data.categories);
                break;
              case "child":
                page.CreateChildUrlList(data.allowedUrls);
                page.SetChildDescription(data.allowedUrls);
                break;
            case "newly_registered":
                page.SetDomainInfo(data.registeredAt);
                break;
            }

            page.makeElementsVisible();
            
        }
        catch (e) {
            console.error(e);
        }
    }); 
})