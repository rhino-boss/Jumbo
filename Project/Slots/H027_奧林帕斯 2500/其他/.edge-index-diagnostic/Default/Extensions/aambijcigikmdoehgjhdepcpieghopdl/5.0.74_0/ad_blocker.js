/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

class AdBlocker {

    #domains = []


    get domains() {
        return this.#domains;
    }

    applyRule() {
        chrome.storage.local.get(["userAdServingDomains"], (result) => {
            this.#domains = AdServingDomains;
            if (Array.isArray(result.userAdServingDomains)) {
                this.#domains = this.#domains.concat(result.userAdServingDomains);
            }
            if (!chrome.declarativeNetRequest) {
                return;
            }
            chrome.declarativeNetRequest.updateDynamicRules({
                addRules: [
                    {
                        id: RuleId.AdBlock,
                        priority: 1,
                        action: {
                            type: 'block',
                        },
                        condition: { "requestDomains": this.#domains, "resourceTypes" : ["main_frame", "sub_frame"] },
                    },
                    {
                        id: RuleId.AdBlockBing,
                        priority: 1,
                        action: {
                            type: 'block',
                        },
                        condition: { "urlFilter": "bing.com/aclick", "resourceTypes" : ["main_frame", "sub_frame"] },
                    },
                ],
                removeRuleIds: [RuleId.AdBlock, RuleId.AdBlockBing]
            },
                () => {
                    if (chrome.runtime.lastError) {
                        console.error(chrome.runtime.lastError.message);
                    }
                }
            );
        });
    }

    configure(enable) {
        console.log("AdBlocker:", enable);
        if (enable) {
            this.applyRule();
        }
        else {
            if (!chrome.declarativeNetRequest) {
                return;
            }
            chrome.declarativeNetRequest.updateDynamicRules({
                removeRuleIds: [RuleId.AdBlock, RuleId.AdBlockBing]
            },
                () => {
                    if (chrome.runtime.lastError) {
                        console.error(chrome.runtime.lastError.message);
                    }

                }
            );
        }
    }
};

