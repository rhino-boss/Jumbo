/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

class SafeSearchOption {
    
    #isSafari = false;
    
    constructor(isSafari) {
        this.#isSafari = isSafari;
    }

    isAlreadyApplied() {
        return new Promise((resolve) => {
            const rules = chrome.declarativeNetRequest.getDynamicRules();
            rules.then( (rules) => {
                const safeSearchRules = rules.filter(rule => rule.id <= RuleId.SafeSearchMax);
                if (safeSearchRules.length > 0) {
                    resolve(true);
                }
                else {
                    resolve(false);
                }
            });
        });
    }

    /* Do not remove it. It's for tests purposes
    #dropAllDynamicRules() {
        (async () => {
            try {
                const currentRules = await chrome.declarativeNetRequest.getDynamicRules();
                const ruleIds = currentRules.map(rule => rule.id);
                await chrome.declarativeNetRequest.updateDynamicRules({
                    removeRuleIds: ruleIds,
                    addRules: []
                });

                console.log("Deactivating dynamic rules. All done");
            } catch (error) {
                console.error("Failed to deactivate dynamic rules: ", error);
            }
        })();
    }
    */

    enableDuckDuckGoRule(enable) {
        const rules = [
                    {
                        id: RuleId.DuckDuckGo,
                        priority: 1,
                        action: {
                            type: 'redirect',
                            "redirect": {
                                "transform": {
                                    "queryTransform": {
                                        "addOrReplaceParams": [{"key": "kp", "value": "1"}]
                                    }
                                }
                            }
                        },
                        condition: { "urlFilter" : "duckduckgo.com", "resourceTypes" : ["main_frame"] },
        }
        ];
        this.#updateDynamicRules(rules, enable);
    }

    enableYahooRule(enable) {
        const rules = [
            {
                id: RuleId.YahooExclude,
                priority: 2, // Higer priority
                action: {
                    type: 'allow' // allow this request. no changes 
                },
                condition: { 
                    // see https://withsecure.atlassian.net/browse/CSBP-35268 
                    // travel.yahoo.co.jp doesn't support vm=r parameter and just redirects the page back 
                    //      => dead loop.
                    "urlFilter" : "*://travel.yahoo.co.jp/*", 
                    "resourceTypes" : ["main_frame"]
                },
            },
            {
                id: RuleId.Yahoo,
                priority: 1,
                action: {
                    type: 'redirect',
                    "redirect": {
                        "transform": {
                            "queryTransform": {
                                "addOrReplaceParams": [{"key": "vm", "value": "r"}]
                            }
                        }
                    }
                },
                condition: { "urlFilter" : "*.yahoo.*", "resourceTypes" : ["main_frame"] },
            },
        ];
        this.#updateDynamicRules(rules, enable);
    }

    enableBingRule(enable) {
        const rules = [
                    {
                        id: RuleId.Bing,
                        priority: 1,
                        action: {
                            type: 'redirect',
                            "redirect": {
                                "transform": {
                                    "queryTransform": {
                                        "addOrReplaceParams": [{"key": "adlt", "value": "strict"}]
                                    }
                                }
                            }
                        },
                        condition: {
                            "urlFilter" : "www*.bing.com",
                            "resourceTypes" : ["main_frame"]
                        },
                    },
        ];
        // Disable Bing safe search for Edge
        this.#updateDynamicRules(rules, enable && FS_NATIVE_MESSAGING_APP != "app.withsecure_edge_https");
    }

    enableGoogleRule(enable) {
        const rules = [
        {
            id: RuleId.Gmail,
            priority: 1,
            action: { type: 'allow' },
            condition: { 'urlFilter': "google.com/gmail", 'resourceTypes': ['main_frame']}
            },
        {
            id: RuleId.Google,
            priority: 1,
            action: {
                type: 'redirect',
                "redirect": {
                    "transform": {
                        "queryTransform": {
                            "addOrReplaceParams": [{"key": "safe", "value": "active"}]
                        }
                    }
                }
            },
            condition: this.googleRuleCondition(),
        },
        ];
        this.#updateDynamicRules(rules, enable);
    }

    enableYoutubeRule(enable) {

        // Safari raises "The header `YouTube-Restrict` is not recognized" error
        if (this.#isSafari) {
            return;
        }
        const rules = [
        {
            id: RuleId.Youtube,
            priority: 1,
            action: {
                type: 'modifyHeaders',
                requestHeaders: [{
                    header: 'YouTube-Restrict',
                    operation: 'set',
                    value: 'Strict'
                }]
            },
            condition: { "requestDomains": ["youtube.com", "youtube-nocookie.com", "googleapis.com"] }
        }
        ];
        this.#updateDynamicRules(rules, enable);
    }

    #updateDynamicRules(rules, enable) {
        const ruleIDs = rules.map(rule => rule.id);
        let ruleOptions = {
            removeRuleIds: ruleIDs
        };
        if (enable) {
            ruleOptions.addRules = rules;
        }
        chrome.declarativeNetRequest.updateDynamicRules(ruleOptions, () => {
                    if (chrome.runtime.lastError) {
                        console.error(chrome.runtime.lastError);
                    }
        });
    }

    enableStrictMode(enable) {
        if (!chrome.declarativeNetRequest) {
            console.log("chrome.declarativeNetRequest is not supported");
            return;
        }
        this.isAlreadyApplied().then( (result) => {
            if (!result && !enable) {
                return;
            }
            console.log("Applying strict mode rules, enable:", enable);
            this.enableGoogleRule(enable);
            this.enableBingRule(enable);
            this.enableDuckDuckGoRule(enable);
            this.enableYahooRule(enable);
            this.enableYoutubeRule(enable);
        });
    }
    
    googleRuleCondition() {
        return {
            "requestDomains" : ["www.google.com",
                                "www.google.ad",
                                "www.google.ae",
                                "www.google.com.af",
                                "www.google.com.ag",
                                "www.google.com.ai",
                                "www.google.al",
                                "www.google.am",
                                "www.google.co.ao",
                                "www.google.com.ar",
                                "www.google.as",
                                "www.google.at",
                                "www.google.com.au",
                                "www.google.az",
                                "www.google.ba",
                                "www.google.com.bd",
                                "www.google.be",
                                "www.google.bf",
                                "www.google.bg",
                                "www.google.com.bh",
                                "www.google.bi",
                                "www.google.bj",
                                "www.google.com.bn",
                                "www.google.com.bo",
                                "www.google.com.br",
                                "www.google.bs",
                                "www.google.bt",
                                "www.google.co.bw",
                                "www.google.by",
                                "www.google.com.bz",
                                "www.google.ca",
                                "www.google.cd",
                                "www.google.cf",
                                "www.google.cg",
                                "www.google.ch",
                                "www.google.ci",
                                "www.google.co.ck",
                                "www.google.cl",
                                "www.google.cm",
                                "www.google.cn",
                                "www.google.com.co",
                                "www.google.co.cr",
                                "www.google.com.cu",
                                "www.google.cv",
                                "www.google.com.cy",
                                "www.google.cz",
                                "www.google.de",
                                "www.google.dj",
                                "www.google.dk",
                                "www.google.dm",
                                "www.google.com.do",
                                "www.google.dz",
                                "www.google.com.ec",
                                "www.google.ee",
                                "www.google.com.eg",
                                "www.google.es",
                                "www.google.com.et",
                                "www.google.fi",
                                "www.google.com.fj",
                                "www.google.fm",
                                "www.google.fr",
                                "www.google.ga",
                                "www.google.ge",
                                "www.google.gg",
                                "www.google.com.gh",
                                "www.google.com.gi",
                                "www.google.gl",
                                "www.google.gm",
                                "www.google.gr",
                                "www.google.com.gt",
                                "www.google.gy",
                                "www.google.com.hk",
                                "www.google.hn",
                                "www.google.hr",
                                "www.google.ht",
                                "www.google.hu",
                                "www.google.co.id",
                                "www.google.ie",
                                "www.google.co.il",
                                "www.google.im",
                                "www.google.co.in",
                                "www.google.iq",
                                "www.google.is",
                                "www.google.it",
                                "www.google.je",
                                "www.google.com.jm",
                                "www.google.jo",
                                "www.google.co.jp",
                                "www.google.co.ke",
                                "www.google.com.kh",
                                "www.google.ki",
                                "www.google.kg",
                                "www.google.co.kr",
                                "www.google.com.kw",
                                "www.google.kz",
                                "www.google.la",
                                "www.google.com.lb",
                                "www.google.li",
                                "www.google.lk",
                                "www.google.co.ls",
                                "www.google.lt",
                                "www.google.lu",
                                "www.google.lv",
                                "www.google.com.ly",
                                "www.google.co.ma",
                                "www.google.md",
                                "www.google.me",
                                "www.google.mg",
                                "www.google.mk",
                                "www.google.ml",
                                "www.google.com.mm",
                                "www.google.mn",
                                "www.google.ms",
                                "www.google.com.mt",
                                "www.google.mu",
                                "www.google.mv",
                                "www.google.mw",
                                "www.google.com.mx",
                                "www.google.com.my",
                                "www.google.co.mz",
                                "www.google.com.na",
                                "www.google.com.ng",
                                "www.google.com.ni",
                                "www.google.ne",
                                "www.google.nl",
                                "www.google.no",
                                "www.google.com.np",
                                "www.google.nr",
                                "www.google.nu",
                                "www.google.co.nz",
                                "www.google.com.om",
                                "www.google.com.pa",
                                "www.google.com.pe",
                                "www.google.com.pg",
                                "www.google.com.ph",
                                "www.google.com.pk",
                                "www.google.pl",
                                "www.google.pn",
                                "www.google.com.pr",
                                "www.google.ps",
                                "www.google.pt",
                                "www.google.com.py",
                                "www.google.com.qa",
                                "www.google.ro",
                                "www.google.ru",
                                "www.google.rw",
                                "www.google.com.sa",
                                "www.google.com.sb",
                                "www.google.sc",
                                "www.google.se",
                                "www.google.com.sg",
                                "www.google.sh",
                                "www.google.si",
                                "www.google.sk",
                                "www.google.com.sl",
                                "www.google.sn",
                                "www.google.so",
                                "www.google.sm",
                                "www.google.sr",
                                "www.google.st",
                                "www.google.com.sv",
                                "www.google.td",
                                "www.google.tg",
                                "www.google.co.th",
                                "www.google.com.tj",
                                "www.google.tl",
                                "www.google.tm",
                                "www.google.tn",
                                "www.google.to",
                                "www.google.com.tr",
                                "www.google.tt",
                                "www.google.com.tw",
                                "www.google.co.tz",
                                "www.google.com.ua",
                                "www.google.co.ug",
                                "www.google.co.uk",
                                "www.google.com.uy",
                                "www.google.co.uz",
                                "www.google.com.vc",
                                "www.google.co.ve",
                                "www.google.vg",
                                "www.google.co.vi",
                                "www.google.com.vn",
                                "www.google.vu",
                                "www.google.ws",
                                "www.google.rs",
                                "www.google.co.za",
                                "www.google.co.zm",
                                "www.google.co.zw",
                                "www.google.cat"],
            "resourceTypes" : ["main_frame"]
        };
    }
};

