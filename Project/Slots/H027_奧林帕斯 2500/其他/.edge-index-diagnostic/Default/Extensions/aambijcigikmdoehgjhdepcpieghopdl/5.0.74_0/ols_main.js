/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function isSafari() {
    const userAgent = navigator.userAgent;
    const isChrome = userAgent.indexOf('Chrome') > -1;
    const isSafari = userAgent.indexOf('Safari') > -1;

    // Chrome and Edge include the string "Safari" in the user-agent. Firefox does not.
    return (isSafari && !isChrome);
}

async function checkResourceExists(path) {
    const url = chrome.runtime.getURL(path);
    try {
        const response = await fetch(url, { method: 'HEAD' });
        return response.ok;
    } catch (e) {
        return false;
    }
}

function isTrustedShoppingRequestValid(url, referrer) {
    if (!Settings.trusted_shopping) {
        return false;
    }
    var isInRefferer = function(url, referrer)
    {
        if (!referrer) {
            return false;
        }
        if (new URL(url).hostname == new URL(referrer).hostname) {
            return true;
        }
        return false;
    }

    if (isInRefferer(url, referrer)) {
        return false;
    }

    return true;
}

const worker = new OlsWorker(isSafari());

NativeHost.setOnPortDisconnectCallback(() => {
    console.error('Native port disconnected!');
    if (chrome.runtime.lastError) {
        console.error(`Error from runtime: ${chrome.runtime.lastError.message}`);
    }
    worker.setExtensionErrorMode();
});

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        switch(request.type) {
        case MessageName.Init:
            if (Settings.search_results) {
                worker.getNativeMessagingStatus((status) => {
                    const response = (status === ConnectionStatus.Connected) ? InitResult.Success : InitResult.Failure;
                    sendResponse(response);
                });
            } else {
                sendResponse(InitResult.Failure);
            }
            break;
        case MessageName.UserRating:
            worker.userRating(request.info.url, request.info.verdict, request.info.categories, request.info.notes);
            sendResponse();
            break;
        case MessageName.Popup:
            let url = request.tab.url;
            if (TabUrl[request.tab.id]) {
                url = TabUrl[request.tab.id].url;
            }
            let info = getUrlInfo(url);
            info.then( (result) => {
                let info = result;
                if (TabUrl[request.tab.id] && TabUrl[request.tab.id].block) {
                    info.block = TabUrl[request.tab.id].block;
                }
                if (TabUrl[request.tab.id]) {
                    const categories = TabUrl[request.tab.id].orsp;
                    if (worker.isShoppingWebsite(categories)) {
                        info.shoppingWebsite = true;
                        if (Settings.trusted_shopping) {
                            info.rating = worker.getShoppingRating(categories);
                        }
                    }
                }
                chrome.runtime.sendMessage( {type: "infopopup", info: info} );
            })
            sendResponse();
            break;
        case MessageName.ConsentDecline:
            console.log("Uninstalling extension");
            chrome.management.uninstallSelf(() => {
                console.log('Uninstall is complete');
            });
            sendResponse();
            break;
        case MessageName.SetConsent:
            console.log("Consent accepted");
            chrome.storage.local.set( {consentAccepted: true} );
            worker.init();
            sendResponse();
            break;
        case MessageName.AllowDomain:
            worker.allowDomainMessage(request.url);
            sendResponse();
            break;
        case MessageName.OpenExceptions:
            worker.openExceptionsMessage();
            sendResponse();
            break;
        case MessageName.CheckWhitelist:
            const whitelistInfo = worker.checkWhitelistMessage(request.url);
            worker.checkWhitelistMessage(request.url).then(whitelistInfo => {
                sendResponse(whitelistInfo);
            });
            break;
        case MessageName.GetPlatformInfo:
            chrome.runtime.getPlatformInfo(platform => {
                sendResponse(platform);
            });
            break;
        case MessageName.RequestURLReputation:
            worker.checkURLReputation(request.url).then((response) => {
                sendResponse(response);
            });
            break;
        case MessageName.SchemaChanged:
            chrome.storage.local.set({ schema: request.schema }, () => {
                worker.setTheme();
                sendResponse();
            });
        case MessageName.GetBankingMode:
                sendResponse(worker.bankingMode);
            break;
        case MessageName.DevToolsOpened:
            worker.devToolsOpened(request.url);
            break;
        case MessageName.ShoppingWebsite:
            let orspData = getUrlInfo(request.url);
            orspData.then( (result) => {
                if (isTrustedShoppingRequestValid(request.url, request.referrer) && worker.isShoppingWebsite(result.categories)) {
                    const rating = worker.getShoppingRating(result.categories);
                    console.log("Shopping website detected, rating", rating);
                    if (rating >= 0) {
                        sendResponse({rating: rating});
                    }
                    else {
                        sendResponse();
                    }
                }
                else {
                    sendResponse();
                }
            })
            break;
        }
        return true; // required for async sendResponse object lifetime
    }
);

const consentListener = () => {
    showConsent(true);
    Action.onClicked.removeListener(consentListener);
};

function showConsent() {
    return new Promise(resolve => {
        // for Edge/Chrome/Safari consent is included into a product onboarding flow, show it just for Firefox
        if (typeof browser === "undefined" || isSafari()) {
            chrome.storage.local.set( {consentAccepted: true}, () => {
               resolve();
            });
            return;
        }

        // Chromium can be detected as FF when the user agent is changed manually.
        checkResourceExists(OnboardingUrl).then(exists => {
            if (exists) {
                // do not show consent if already shown
                chrome.tabs.query({}, tabs => {
                    tabs.forEach((tab) => {
                        if (tab.url == OnboardingUrl) {
                            resolve();
                            return;
                        }
                    });
                    // check if consent has been accepted already
                    chrome.storage.local.get("consentAccepted", (result) => {
                        if (!result.consentAccepted) {
                            console.warn("Please, see consent page");
                            const url = chrome.runtime.getURL(OnboardingUrl);
                            chrome.tabs.create({ url });
                            worker.setExtensionNoConsent();
                        }
                        resolve();
                    });
                });
            } else {
                console.warn("Onboarding page not found:", OnboardingUrl);
                chrome.storage.local.set( {consentAccepted: true}, () => {
                    resolve();
                });
                return;
            }
        });
    });
}

// Show consent also when script fired (to handle incognito mode switch)
showConsent().then(() => {
    chrome.storage.local.get("consentAccepted", (result) => {
        if (result.consentAccepted) {
            // We start listeners here, when consent is accepted
            worker.init();
        } else {
            worker.setExtensionNoConsent();
        }
    });
});
