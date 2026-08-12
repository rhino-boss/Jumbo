/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

class TrustedShoppingPopup {

	#popup;
	#popupTitle;
	#rating;
	#customization;

	constructor(rating, customization) {
		this.#rating = rating;
		this.#customization = customization;
	}

	inject() {
		const host = location.hostname;
		const root = htmlToElem(`<div style="all: initial"><div class="fs-ols-shopping-popup" id="fs-ols-shopping-popup">${this.getTemplate(host, this.#rating )}</div></div>`);
		document.body.appendChild(root);
		this.#popup = document.getElementById("fs-ols-shopping-popup");
		this.#popupTitle = document.getElementById("fs-shopping-popup-panel-header");
		document.getElementById("fs-close-shopping-panel-btn").addEventListener("click", () => {
			this.hide();
		});
	}

	getTemplate (hostname, rating) {
		const headerBgColor = this.#customization.MainColor;
		const extName = chrome.runtime.getManifest().name;

		const closeIcon = chrome.runtime.getURL("img/ic_close.svg");
		const shoppingIcon = chrome.runtime.getURL("img/ic_place_onlineshop.svg");
		const actionIcon = chrome.runtime.getURL("img/ic_action_sms.svg");
		const iconEmoji1 = chrome.runtime.getURL("img/ic_emoji_status_1.svg");
		const iconEmoji2 = chrome.runtime.getURL("img/ic_emoji_status_2.svg");
		const iconEmoji3 = chrome.runtime.getURL("img/ic_emoji_status_3.svg");
		const iconEmoji4 = chrome.runtime.getURL("img/ic_emoji_status_4.svg");
		const iconEmoji5 = chrome.runtime.getURL("img/ic_emoji_status_5.svg");

		const closeTitle = chrome.i18n.getMessage("close_btn");
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
				p2 = chrome.i18n.getMessage("trusted_shopping_suspicious_p2");
				opacityIconEmoji2 = "1";
				break;
			case 1:
				bgColor = "#FFE6CC";
				p1 = chrome.i18n.getMessage("trusted_shopping_suspicious_p1");
				p2 = chrome.i18n.getMessage("trusted_shopping_suspicious_p2");
				opacityIconEmoji1 = "1";
				break;
			default:
				p1 = chrome.i18n.getMessage("trusted_shopping_unknown_p1");
				p2 = chrome.i18n.getMessage("trusted_shopping_unknown_p2");
				bgColor = "#F2F2F2";
		}
		return `
		<div class="fs-grid-container">
		  	<div class="fs-grid-item" id="fs-shopping-popup-panel-header" style="background: ${headerBgColor}; height: 52px; color: white; border-top-left-radius: 5px; border-top-right-radius: 5px;"><span style="width: 100%;text-align: left;">${extName}</span>
				<span id="fs-close-shopping-panel-btn" style="cursor: pointer;">
			  	<img style="vertical-align:middle;" title="${closeTitle}" src="${closeIcon}"/></span></div>
		  	<div class="fs-grid-item" style="background: ${bgColor}; height: 32px; font-size: 14px;"><span><img style="vertical-align:middle;" src="${shoppingIcon}"/></span><span style="color: black; margin-left: 8px">${hostname}</span></div>
		  	<div class="fs-grid-item" style="color: black; display: initial; text-align: left;">
				<div style="font-size: 16px; font-weight: bold; margin-top: 18px;">${p1}</div>
				<div style="font-size: 14px; margin-top: 8px;">${p2}</div>
				<div style="margin-top: 24px; margin-bottom: 24px; text-align: left;">
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 50px; opacity: ${opacityIconEmoji1}; display: initial;" src="${iconEmoji1}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 50px; opacity: ${opacityIconEmoji2}; display: initial;" src="${iconEmoji2}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 50px; opacity: ${opacityIconEmoji3}; display: initial;" src="${iconEmoji3}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 50px; opacity: ${opacityIconEmoji4}; display: initial;" src="${iconEmoji4}"/></span>
					<span style="margin-left: 11px"><img style="vertical-align:middle; height: 50px; opacity: ${opacityIconEmoji5}; display: initial;" src="${iconEmoji5}"/></span>
				</div>
				<div><span><img style="vertical-align:middle;margin-bottom: 3px; margin-right: 4px; display: initial;" src="${actionIcon}"/></span><span>${reviewText}</span></div>
			<div>
		</div>
		`;
	}

	hide() {
        this.#popup.style.display = 'none';
	}

	async show(timeout=5000) {
		let interval = null;
		let pos = 0;
		let popup = this.#popup;
		const topPos = 340;
		const rightPos = 400;
		popup.style.top = window.innerHeight;
		popup.style.left = window.innerWidth - rightPos + "px";
		popup.style.display = 'block';
		clearInterval(interval);
		interval = setInterval(moveUp, 10);
		
		function updatePosition() {
			popup.style.left = window.innerWidth - rightPos + "px";
			popup.style.top = window.innerHeight - topPos + "px";
		}
		  
		window.onresize = updatePosition;

		function moveDown() {
			if (pos == topPos) {
			  clearInterval(interval);
			  popup.style.display = 'none';
			} 
			else {
			  pos = pos + 10;  
			  popup.style.top = (window.innerHeight - topPos) + pos + "px";
			}
		}

		function moveUp() {
		  if (pos == topPos) {
			clearInterval(interval);
			pos = 0;
			setTimeout(() => {interval = setInterval(moveDown, 10)}, timeout);
		  } 
		  else {
			pos = pos + 10; 
			popup.style.top = window.innerHeight - pos + "px";
		  }
		}
	}
}
