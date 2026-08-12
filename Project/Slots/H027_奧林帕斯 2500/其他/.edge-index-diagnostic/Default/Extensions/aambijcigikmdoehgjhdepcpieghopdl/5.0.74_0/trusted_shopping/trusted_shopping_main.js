/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

(async () => {
    const response = await chrome.runtime.sendMessage( {type: MessageName.ShoppingWebsite, url: window.location.href, referrer: document.referrer} );
    if (response) {
        const rating = response.rating;
        chrome.storage.local.get(["customization"], (storageResult) =>{
            const popup = new TrustedShoppingPopup(rating, storageResult.customization);
            popup.inject();
            popup.show();
		});
    }
  })();