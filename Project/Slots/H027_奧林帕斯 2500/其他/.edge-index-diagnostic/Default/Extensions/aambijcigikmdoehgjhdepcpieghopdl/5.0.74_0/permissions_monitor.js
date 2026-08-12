/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

/*
    Safari does not allow access to all webpages even if the manifest requests so. This is not a bug, it's a privacy feature
    User is expected to allow extension access to some pages, all web pages or only temporarily (ex. for one day)
    If the user does not grant access to all websites, block pages will be shown only for pages access was granted to.
    This class contains logic to detect when user did not grant access to all websites and notifies the product to show the corresponding message in the UI
*/

class PermissionsMonitor {

    #allWebsiteOrigins = "*://*/*";
    #httpOrigins = "http://*/*";
    #httpsOrigins = "https://*/*";
    #onPermissionsChangedHandler;

    constructor(onPermissionsChangedHandler) {
        this.#onPermissionsChangedHandler = onPermissionsChangedHandler;
    }

    permissionsAllowed(permissions) {
        return this.#isAllowed(permissions, null);
    }

    originsAllowed(origins) {
        return this.#isAllowed(null, origins);
    }
    
    allWebsiteAccessAllowed() {
        return this.originsAllowed([this.#httpOrigins, this.#httpsOrigins]);
    }

    #isAllowed(permissions, origins) {
        return new Promise(resolve => {
            try {
                const query = permissions ? { permissions: permissions } : { origins: origins };
                chrome.permissions.contains(query, (result) => {
                    resolve(result);
                });
            } catch (error) {
                console.error(`Error checking permissions ${permissions} or origins ${origins}: ${error}`);
                resolve(false);
            }

        });
    }

    #onAddedPermissions(permissions) {
        const allWebsiteAccessAdded = (permissions && permissions.origins && permissions.origins.includes(this.#allWebsiteOrigins));
        if (allWebsiteAccessAdded) {
            console.debug("User has granted access to all websites");
            this.#onPermissionsChangedHandler(true);
        } else {
            console.debug(`User granted access to origins ${permissions.origins}`);
        }
    };

    #onRemovedPermissions(permissions) {
        const allWebsiteAccessRemoved = (permissions && permissions.origins.includes(this.#allWebsiteOrigins));
        if (allWebsiteAccessRemoved) {
            console.debug(`User revoked access to all websites`);
            this.#onPermissionsChangedHandler(false);
        } else {
            console.debug(`User revoked access to origins ${permissions.origins}`);
        }
    };

    #monitorPermissions() {
        chrome.permissions.onAdded.addListener((permissions) => { this.#onAddedPermissions(permissions) });
        chrome.permissions.onRemoved.addListener((permissions) => { this.#onRemovedPermissions(permissions) });
    }

    start() {
        this.#monitorPermissions();
        this.allWebsiteAccessAllowed().then(allWebsiteAllowed => {
            this.#onPermissionsChangedHandler(allWebsiteAllowed);
        });
    }
}
