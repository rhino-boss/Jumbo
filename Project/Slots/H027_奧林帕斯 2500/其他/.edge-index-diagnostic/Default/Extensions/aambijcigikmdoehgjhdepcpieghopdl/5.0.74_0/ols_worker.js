/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

const NativeHost = new MessagingHostFactory().getMessageHost();

var Settings = {
    safe_search: false,
    search_results: true,
    block_ads: false,
    trusted_shopping: false
};

function getBrowserName() {
    if (isSafari()) {
        return "safari";
    }
    if (navigator.userAgent.indexOf("Edg") > -1) {
        return "edge";
    }
    if (navigator.userAgent.match(/chrome|chromium|crios/i)) {
        return "chrome";
    }
    if (chrome.runtime.getURL('').startsWith('moz-extension://')) {
        return "firefox";
    }
    return "";
}

function bypassRequest(details) {
    if (details.frameId !== undefined && details.frameId != 0) {
        return true;
    }
    const parsedUrl = new URL(details.url);
    if (parsedUrl.hostname == "localhost" || parsedUrl.hostname.startsWith("localhost:")) {
        return true;
    }
    
    // safari extension internal pages
    if (parsedUrl.protocol == "safari-web-extension:") {
        return true;
    }
    
    return false;
}

function getReferrer(details) {
    if (details.initiator && details.initiator != "null") {
        const parsedInitiator = new URL(details.initiator);
        if (["http:", "https:"].includes(parsedInitiator.protocol) && parsedInitiator.hostname != "localhost" && !parsedInitiator.hostname.startsWith("localhost:")) {
            return details.initiator;
        }
    }

    return "";
}

async function getUrlInfo(url) {
    return await worker.orspInfoMessage(url);
}

// A wrapper to work properly with both MV2 and MV3
function BrowserAction() {
    if (chrome.action) {
        return chrome.action;
    }
    else {
        return chrome.browserAction;
    }
}

function GetValueIfObjectExists(obj, id) {
    if (id in obj) {
        return obj[id];
    }
    return null;
}

const Action = new BrowserAction();

var TabUrl = {};

class OlsWorker {

    #browserInfo = {}
    #platform = {}
    #userInfo = {}
    #customizationLoaded = false;
    #nativeMessagingStatus = ConnectionStatus.Unknown;
    #permissionsMonitor;
    #isSafari = false;
    #bankingMode = false;
    #connectionStatusRequests = []
    
    constructor(isSafari) {
        this.#isSafari = isSafari;
        if (this.#isSafari) {
            this.#permissionsMonitor = new PermissionsMonitor(this.#sendAllWebsiteAccessChanged);
            this.#permissionsMonitor.start();
        }
    }

    get bankingMode() {
        return this.#bankingMode;
    }

    init() {

        const extName = chrome.runtime.getManifest().name;
        console.log("Initialize extension");
        console.log("Extension version:", chrome.runtime.getManifest().version);
        console.log("Extension id:", chrome.runtime.id);
        console.log("Extension name:", extName);
        console.log("Browser name:", getBrowserName());
        chrome.runtime.getPlatformInfo(platform => {
            console.log("Platform info:", JSON.stringify(platform));
            this.#platform = platform;
        });

        chrome.storage.local.get(["browserInfo", "userAdServingDomains"], (result) => {
            console.log("Browser info:", result.browserInfo);
            let domainListCount = result.userAdServingDomains ? result.userAdServingDomains.length : 0;
            console.log("User's ad serving domains count:", domainListCount);
            this.#userInfo["adServingDomainsSize"] = domainListCount;
            this.#browserInfo = result.browserInfo;
        });

        this.safeSearchOption = new SafeSearchOption(this.#isSafari);
        this.adBlocker = new AdBlocker();
        this.referrerCache = new ReferrerCache();

        NativeHost.setSettingsChangedCallback((settings) => { this.onSettingsChanged(settings); });
        NativeHost.setBankingModeChangedCallback((bankingMode) => { this.onBankingModeChanged(bankingMode); });
        NativeHost.setServerRestartedCallback(() => { this.referrerCache.Clear(); });

        this.initCommsAddListeners();
    }
    
    #getOpenTabs() {
        return new Promise(resolve => {
            (async () => {
                if (this.#isSafari && this.#permissionsMonitor) {
                    const allWebsiteAccessAllowed = await this.#permissionsMonitor.allWebsiteAccessAllowed();
                    if (!allWebsiteAccessAllowed) {
                        // Safari does not allow calling "chrome.tabs.query" API before the user grants extension access to all websites in the settings
                        resolve([]);
                        return;
                    }
                }
                chrome.tabs.query({}, tabs => {
                    resolve(tabs);
                });
            })()
        });
    }

    initCommsAddListeners() {
        this.#getOpenTabs().then(tabs => {
            var tabInfos = tabs.map(tab => ({id: tab.id, url: tab.url}))
            console.log("Tab infos", JSON.stringify(tabInfos));
            
            const info = {
                type: MessageName.Init,
                browserInfo: this.#browserInfo,
                platform: this.#platform,
                userInfo: this.#userInfo,
                browserName: getBrowserName(),
                extId: chrome.runtime.id,
                tabs: tabInfos,
                extensionVersion: chrome.runtime.getManifest().version
            };

            NativeHost.postMessage(info).then((result, resolve) => {
                this.setExtensionOkMode();
                this.setTheme();
                if (result.customization && Object.keys(result.customization).length > 0) {
                    this.#customizationLoaded = true;
                }
                chrome.storage.local.set({
                              guid: result.guid,
                              port: result.port,
                              customization: result.customization,
                              settings: result.settings,
                              platform: this.#platform
                          }, () => {
                    console.log("Port:", result.port, "Guid:", result.guid, "Customization:", JSON.stringify(result.customization));
                });

                if (result.settings) {
                    this.onSettingsChanged(result.settings);
                }
                else {
                    console.log("No settings in init response");
                    this.scanMessage("https://withsecure.com"); // send dummy scan message to get settings (to be deprecated)
                }

                this.addListeners();
            });
        });
    }

    addListeners() {
        console.log("Adding listeners");
        chrome.webNavigation.onCompleted.addListener((details) => { this.onCompleted(details) }, { "url": [{"schemes": ["https", "http"]}] });
        chrome.webNavigation.onCommitted.addListener((details) => { this.onCommitted(details) }, { "url": [{"schemes": ["https", "http"]}] });

        chrome.tabs.onUpdated.addListener((tabId, details) => { this.onTabUpdated(tabId, details) });
        chrome.tabs.onRemoved.addListener((tabId, details) => { this.onTabRemoved(tabId, details) });
        chrome.tabs.onReplaced.addListener((addedTabId, removedTabId) => { this.onTabReplaced(addedTabId, removedTabId) });

        if (chrome.runtime.getManifest().manifest_version == 3) {
            chrome.webRequest.onBeforeRequest.addListener((details) => { this.onBeforeRequestMV3(details) }, {urls: ["http://*/*", "https://*/*"], types: ["main_frame", "sub_frame", "stylesheet", "script", "image", "xmlhttprequest", "media"]});
        }
        else {
            // webRequestBlocking is not available in Safari. So checking dynamically and applying only if the browser supports it
            if (this.#isSafari) {
                console.error("webRequestBlocking permission is not available for Safari. Not proceeding with adding webRequest listeners");
                return;
            }
            const onBeforeSendHeadersOptions = ["requestHeaders", "blocking"];
            const onBeforeRequestOptions = ["blocking"];
            chrome.webRequest.onBeforeSendHeaders.addListener((details) => this.onBeforeSendHeaders(details), { urls: YoutubeUrls, types: ["main_frame", "xmlhttprequest"] }, onBeforeSendHeadersOptions);
            chrome.webRequest.onBeforeRequest.addListener((details) => this.onBeforeRequestMV2(details), { urls: ["http://*/*", "https://*/*"], types: ["main_frame", "sub_frame", "stylesheet", "script", "image", "xmlhttprequest", "media"] }, onBeforeRequestOptions);
        }
    }

   onBeforeSendHeaders (details) {
        if (Settings.safe_search) {
            const strictMode = { name: "YouTube-Restrict", value: "Strict" };
            details.requestHeaders.push(strictMode);
        }
        return { requestHeaders: details.requestHeaders };
    }

    getNativeMessagingStatus(callback) {
        if (this.#nativeMessagingStatus != ConnectionStatus.Unknown) {
            // state is known. responding right away
            callback(this.#nativeMessagingStatus);
            return;
        }
        
        // content script asks for status before background script established connection to native messaging host
        // storing the callback and will respond once the state is known
        this.#connectionStatusRequests.push(callback);
    }
    
    #clearConnectionStatusRequestQueue(status) {
        this.#connectionStatusRequests.forEach((callback) => {
            callback(status);
        });
        this.#connectionStatusRequests = [];
    }

    setStatus(status) {
        this.#nativeMessagingStatus = status;
        this.setTheme();
        this.#clearConnectionStatusRequestQueue(status);
    }

    setTheme() {
        chrome.storage.local.get(["schema"], (result) => {
            if (!result || !result.schema) {
                return;
            }
            const isDarkMode = result.schema === Schema.Dark;
            const isConnected = this.#nativeMessagingStatus === ConnectionStatus.Connected;
            if (isDarkMode) {
                Action.setIcon({ path: isConnected ? ExtensionIconsDarkOk : ExtensionIconsDarkError });
            } else {
                Action.setIcon({ path: isConnected ? ExtensionIconsLightOk : ExtensionIconsLightError });
            }
        });
    }

    setExtensionErrorMode() {
        this.setStatus(ConnectionStatus.Error);
        Settings.safe_search = false;
        Settings.search_results = false;
        Settings.block_ads = false;
        Action.setTitle( {title: chrome.i18n.getMessage("error_ca_text_p1")} );
        Action.setPopup( {popup: "menu/error_status.html"} );
    }

    setExtensionOkMode() {
        this.setStatus(ConnectionStatus.Connected);
        Action.setTitle( {title: chrome.i18n.getMessage("popup_status_ok")} );
        Action.setPopup( {popup: "menu/popup_rating.html"} );
    }

    setExtensionNoConsent() {
        this.setStatus(ConnectionStatus.Error);
        Action.onClicked.addListener(consentListener);
    }

    onCompleted(details) {
        console.log("onCompleted", JSON.stringify(details));
        if (details.frameId == 0) {
            this.tabInfoMessage(TabAction.Complete, details.tabId, details.url, []);
        };
    }

    adBlockerStats(details) {
        let domain = new URL(details.url).hostname;
        if (this.adBlocker.domains.includes(domain)) {
            console.log("Ad blocker has blocked the url:", details.url);
            this.adBlockedMessage();
        }
        else if (details.frameType == "sub_frame" && details.type != "main_frame") {
            chrome.storage.local.get(["userAdServingDomains"], (result) => {
                let domains = [];
                if (Array.isArray(result.userAdServingDomains)) {
                    domains = result.userAdServingDomains;
                }
                if (!domains.includes(domain)) {
                    this.orspInfoMessage(domain).then( (info) => {
                        info.categories.forEach( (cats) => {
                            if (Object.keys(cats).includes("adserving") || Object.keys(cats).includes("fso_adserving")) {
                                if (Array.isArray(result.userAdServingDomains)) {
                                    domains = result.userAdServingDomains;
                                }
                                // Skip dynamic ad serving domains in production
                                if (chrome.runtime.getManifest().name == chrome.i18n.getMessage("ext_name"))
                                {
                                    return;
                                }
                                domains.push(domain);
                                chrome.storage.local.set({userAdServingDomains: domains}, () => {
                                    console.info("New user ad serving domain list:", JSON.stringify(domains));
                                    this.adBlocker.applyRule();
                                });  
                                return;
                            }
                        });
                    });
                }
            });
        }
    }

    onBeforeRequestMV3(details) {
        if (Settings.block_ads) {
            this.adBlockerStats(details);
        }

        if (!bypassRequest(details)) {
            const referrer = getReferrer(details);
            if (details.type == "main_frame") {
                this.safeSearchOption.enableStrictMode(Settings.safe_search);
                this.scanMessage(details.url, details.tabId, referrer);
            }
            else {  
                if (referrer && this.mustSendReferrerMessage(details.url, referrer)) {
                    this.referrerMessage(details.url, referrer);
                }
            }
        }
    }

    onBeforeRequestMV2 (details) {
        let domain = new URL(details.url).hostname;
        if (Settings.block_ads &&
            (this.adBlocker.domains.includes(domain) || details.url.includes("bing.com/aclick")))
        {
            console.log("Ad blocker has blocked the url:", details.url);
            this.adBlockedMessage();
            return {cancel: true};
        }

        var result = true;
        if (!bypassRequest(details)) {
            const referrer = getReferrer(details);
            if (details.type == "main_frame") {
                result = this.scanMessage(details.url, details.tabId, referrer);
                console.log(`Scanning ${details.url}`);
            }
            else if (referrer && this.mustSendReferrerMessage(details.url, referrer)) {
                this.referrerMessage(details.url, referrer);
            }
        }

        if (Settings.safe_search == true) {
            let url = new URL(details.url);
            if (GoogleDomains.includes(url.hostname)) {
                if (url.searchParams.get("safe") != "vss") {
                    url.searchParams.set("safe", "vss");
                    return { redirectUrl: url.href };
                }
            }
            else if (BingDomains.includes(url.hostname)) {
                if (url.searchParams.get("adlt") != "strict") {
                    url.searchParams.set("adlt", "strict");
                    return { redirectUrl: url.href };
                }
            }
            else if (YahooDomains.includes(url.hostname) || YahooDomainsJapan.includes(url.hostname)) {
                if (url.searchParams.get("vm") != "r") {
                    url.searchParams.set("vm", "r");
                    return { redirectUrl: url.href };
                }
            }
            else if (DuckDuckGoDomains.includes(url.hostname)) {
                if (url.searchParams.get("kp") != "1") {
                    url.searchParams.set("kp", "1");
                    return { redirectUrl: url.href };
                }
            }
        }

        return result;
    }

    mustSendReferrerMessage(url, referrer) {
        if (!NativeHost.isServerIdValid()) {
            return true; // ReferrerCache proper reset not available, so don't use it
        }

        return this.referrerCache.Process(referrer, url);
    }

    onCommitted(details) {
        console.log("onCommitted", JSON.stringify(details));
        if (details.transitionQualifiers.includes("server_redirect")) {
            console.log("Redirected to:", details.url);
            if (!bypassRequest(details)) {
                this.scanMessage(details.url, details.tabId, "");
            }
        }
    }

    onTabUpdated(tabId, details) {
        console.log(`onTabUpdated: ${tabId}, ${JSON.stringify(details)}`);
        this.tabInfoMessage(TabAction.Open, tabId, details.url, []);
        
        // onBeforeRequest does not contain tabId in case of Safari. This prevents block page from being shown when the user navigates directly to unsafe page
        // sending scan message for Safari here
        if (this.#isSafari && !bypassRequest(details)) {
            const referrer = getReferrer(details);
            this.scanMessage(details.url, tabId, referrer);
        }

    }

    onTabRemoved(tabId, details) {
        console.log("onTabRemoved", tabId, JSON.stringify(details));

        chrome.tabs.query({}, tabs => {
            var openTabs = tabs.map(tab => (tab.id));
            console.log("open tabs:", JSON.stringify(openTabs));
            this.tabInfoMessage(TabAction.Close, tabId, details.url, openTabs);
        });
    }

    onTabReplaced(addedTabId, removedTabId) {
        console.log("onTabReplaced", removedTabId, "->", addedTabId);
    }

    tabInfoMessage(tabAction, tabId, url, openTabs) {
        if (tabId != chrome.tabs.TAB_ID_NONE && url) {
            const info = {
                type: MessageName.TabInfo,
                "tabinfo": {
                    "action": tabAction,
                    "tabId": tabId,
                    "url": url
                }
            };

            NativeHost.postMessage(info);
        }
        else if (tabAction == TabAction.Close) {
            const info = {
                type: MessageName.TabInfo,
                "tabinfo": {
                    "action": tabAction,
                    "tabId": tabId,
                    "openTabs": openTabs
                }
            };

            NativeHost.postMessage(info);
        }
    }

    isShoppingWebsite(categories) {
        if (!categories) {
            return false;
        }
        for (let cat in categories) {
            if (Object.keys(categories[cat])[0] == "shopping") {
                if (categories[cat]["shopping"] == 100) {
                    return true;
                }
            }
            if (Object.keys(categories[cat])[0] == "shopping_and_auctions") {
                if (categories[cat]["shopping_and_auctions"] == 100) {
                    return true;
                }
            }
        }
        return false;
    }

    getShoppingRating(categories) {
        if (!categories) {
            return -1;
        }
        for (let cat in categories) {
            if (Object.keys(categories[cat])[0] == "trustworthiness") {
                return categories[cat]["trustworthiness"];
            }
        }
        return -1;
    }

    scanMessage(url, tabId, referrer) {
        return new Promise(resolve => {
            var query = {
                type: MessageName.ScanRequest,
                scanrequest: {
                    url: url,
                    tabId: tabId,
                    rqtype: ScanRequestType.PrimaryNoBanking,
                    extVer: chrome.runtime.getManifest().version,
                    extName: chrome.runtime.getManifest().name
                }
            };
            if (referrer) {
                query.scanrequest.referer = referrer; // typo (query.referer) intentional
            }

            NativeHost.postMessage(query)
                .then(result => {
                    console.log("Scan result", JSON.stringify(result));

                    let blockPageUrl;
                    let tabUrl = url;

                    if (result.block) {
                        blockPageUrl = this.getBlockPage(result.block);
                        if (!chrome.runtime.lastError && tabId) {
                            chrome.tabs.update(tabId, { url: blockPageUrl });
                        }
                        if (result.block.url) {
                            tabUrl = result.block.url;
                        }
                    }

                    if ("settings" in result) {
                        if ("safe_search" in result.settings) {
                            Settings.safe_search = result.settings.safe_search;
                        }
                        if ("search_results" in result.settings) {
                            Settings.search_results = result.settings.search_results;
                        }
                    }

                    if("id" in result && Object.keys(result).length == 1) {
                        console.warn("Empty response");
                        this.setExtensionErrorMode();
                    }
                    else {
                        this.setExtensionOkMode();
                    }

                    TabUrl[tabId] = { url: tabUrl, block: result.block, orsp: result.ORSPData, referrer: referrer};

                    resolve();
               });
        });
    }

    orspInfoMessage(url) {
        return new Promise(resolve => {
            var query = {
                type: MessageName.ORSPInfo,
                orspinfo: {
                    url: url
                }
            };

            NativeHost.postMessage(query)
                .then(result => {
                    var info = {
                        categories: result.categories,
                        url: result.url,
                        isWhitelisted: result.isWhitelisted
                    };
                    resolve(info);
               });
        });
    }

    referrerMessage(url, referrer) {
        const message = {
            type: MessageName.Referrer,
            url: url,
            referrer: referrer
        };

        NativeHost.postMessage(message);
    }

    adBlockedMessage() {
        const message = {
            type: MessageName.AdBlock,
        };

        NativeHost.postMessage(message);
    }

    userRating(url, verdict, categories, notes) {
        const message = {
            type: "userrating",
            userrating: {
                url: url,
                verdict: verdict,
                categories: categories,
                notes: notes
            }
        };

        NativeHost.postMessage(message);
    }

    devToolsOpened(url) {
        const query = {
            type: "devToolsOpened",
            devToolsOpened: {
                url: url
            }
        };
        NativeHost.postMessage(query);
    }

    allowDomainMessage(url) {
        const query = {
            type: "allowdomain",
            allowdomain: {
                url: url
            }
        };
        NativeHost.postMessage(query);
    }

    openExceptionsMessage(url) {
        const query = {
            type: "openexceptions"
        };
        NativeHost.postMessage(query);
    }

    checkWhitelistMessage(url) {
        return new Promise(resolve => {
            const query = {
                type: "checkwhitelist",
                checkwhitelist: {
                    url: url
                }
            };

            NativeHost.postMessage(query)
                .then(result => {
                    const info = {
                        whitelisted: result.info.whitelisted,
                        url: result.info.url
                    };
                    resolve(info);
               });
        });
    }

    checkURLReputation(url) {
        return new Promise(resolve => {
            const query = {
                type: "ratingrequest",
                ratingrequest: {
                    "url": url
                }
            };

            NativeHost.postMessage(query)
                .then(result => {
                    result.ext_name = chrome.runtime.getManifest().name;
                    result.domain = new URL(url).hostname;
                    result.typeIcon = "";
                    if (result.categories) {
                        result.typeIcon = chrome.runtime.getURL('img/ic_18+.svg');
                    }

                    if (this.isShoppingWebsite(result.orspData)) {
                        result.typeIcon = chrome.runtime.getURL("img/ic_place_onlineshop.svg");
                        if (Settings.trusted_shopping) {
                            result.trustworthiness = this.getShoppingRating(result.orspData);
                            if (result.trustworthiness == 1) {
                                result.rating_status = "shoppingUnsafe";
                            }
                        }
                    }
                    resolve(result);
                });
        });
    }

    getBlockPage(block) {
        // if customization is missing, show general block page
        if (!this.#customizationLoaded) {
            block.type = "general";
        }
        return chrome.runtime.getURL(BlockPages[block.type] + "?data=" + encodeURIComponent(JSON.stringify(block)));
    }

    onSettingsChanged(settings) {

        console.log("onSettingsChanged:", JSON.stringify(settings));
        chrome.storage.local.set({settings: settings});
        if (typeof settings.safe_search != "undefined") {
            Settings.safe_search = settings.safe_search;
            this.safeSearchOption.enableStrictMode(Settings.safe_search);
        }
        if (typeof settings.search_results != "undefined") {
            Settings.search_results = settings.search_results;
        }
        if (typeof settings.block_ads != "undefined") {
            Settings.block_ads = settings.block_ads;
            this.adBlocker.configure(Settings.block_ads);
        }
        if (typeof settings.trusted_shopping != "undefined") {
            Settings.trusted_shopping = settings.trusted_shopping;
        }
    }

    onBankingModeChanged(bankingMode) {
        console.log("onBankingModeChanged:", JSON.stringify(bankingMode));
        if (bankingMode) {
            this.#bankingMode = bankingMode.active;
            chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
                const url = tabs[0].url;
                if (url.startsWith("https://") || url.startsWith("http://")) {
                    chrome.tabs.sendMessage(tabs[0].id, {type: MessageName.BankingSessionActive, bankingActive: bankingMode.active});
                }
            });
        }
    }

    #sendAllWebsiteAccessChanged(granted) {
        const query = {
            type: "allWebsiteAccessRequest",
            extensionVersion: chrome.runtime.getManifest().version,
            allWebsiteAccessRequest: {
                "granted": granted
            }
        };
        NativeHost.postMessage(query);
    }
}

