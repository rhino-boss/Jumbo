/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */


const BalloonFrame = '<div class="fs-ols-balloon" id="fs-ols-balloon"><iframe class="fs-ols-frame" id="fs-ols-frame"></iframe></div>';

class FsOlsBalloon {

	#balloon;
	#customizedCss;
	#customization;
	#main_color;

	constructor() {
		this.#balloon = htmlToElem(BalloonFrame);
		chrome.storage.local.get(["port", "customization"], (storageResult) =>{
			this.#customization = storageResult.customization;
			this.#main_color = storageResult.customization.MainColor || "#0028A0";
		});
	}

	inject() {
		document.body.appendChild(this.#balloon);
		const icons = document.getElementsByClassName("fs-bubble-info");
		Array.from(icons).forEach( (icon) => {
			icon.addEventListener('mouseover', (e) => {
				this.show(e.target);
			});
			icon.addEventListener('mouseout', (e) => {
				this.hide();
			});
		});
	}

	getTemplate (extName, status, domain, categories, trustworthiness, typeIcon) {
		let iconsHtml = "";
		let typeIconVisible = "none";
		if (categories) {
			let cats = fsGetCategoryResources(categories.split(","));
			for (let i = 0; i < cats.length; i++) {
				iconsHtml += `<img style="height: 20px;vertical-align:middle; margin: 2px;" src="${cats[i].icon}" title="${cats[i].title}"></img>`;
			}
			typeIconVisible = "block";
		}
		else if (trustworthiness > 0) {
			iconsHtml = this.getTrustedShoppingTemplate(trustworthiness);
			typeIconVisible = "block";
		}
		return `
		<html>
			<head>
				<style>
					.balloon-grid-container {
					  display: inline-grid;
					  grid-template-columns: auto;
					  padding: 0px;
					  width: 100%
					}
					body {
						margin: 0;
						font-family: 'Segoe UI', system-ui;
						font-style: normal;
						font-weight: 600;
						line-height: 21px;
					}
					.balloon-grid-item {
						text-align: center;
						padding-left: 16px;
						padding-right: 16px;
						display: flex;
						align-items:center;
					}
				</style>
	</head>
	<body>
		<div class="balloon-grid-container">
		  <div class="balloon-grid-item" style="background: ${this.#main_color}; height: 40px; color: white; font-size: 14px;"><div>${extName}</div></div>
		  		<div class="balloon-grid-item" style="background: ${fsGetRatingResources(status).bg_color}; height: 32px; font-size: 14px;">
					<div style="width:100%">
						<img style="margin-right: 8px; vertical-align:middle;display:${typeIconVisible};float:left" src="${typeIcon}"/>
						<div style="float:left;">${domain}</div>
						<div style="float:right;">${iconsHtml}</div>
					</div>
				</div>
		  <div class="balloon-grid-item"><div style="height: 78px; display: flex; align-items:center; font-size: 16px;"><img style="height: 32px; margin-right: 8px" src="${fsGetRatingResources(status).icon}"></img> <span style="text-align:left">${fsGetRatingResources(status).title}</span></div><div>
		</div>
	</body>
</html>
		`;
	}

	getTrustedShoppingTemplate(rating) {
		const iconEmoji1 = chrome.runtime.getURL("img/ic_emoji_status_1.svg");
		const iconEmoji2 = chrome.runtime.getURL("img/ic_emoji_status_2.svg");
		const iconEmoji3 = chrome.runtime.getURL("img/ic_emoji_status_3.svg");
		const iconEmoji4 = chrome.runtime.getURL("img/ic_emoji_status_4.svg");
		const iconEmoji5 = chrome.runtime.getURL("img/ic_emoji_status_5.svg");

		let opacityIconEmoji1 = "0.3", opacityIconEmoji2 = "0.3", opacityIconEmoji3 = "0.3", opacityIconEmoji4 = "0.3", opacityIconEmoji5 = "0.3";
		switch (rating) {
			case 5:
				opacityIconEmoji5 = "1";
				break;
			case 4:
				opacityIconEmoji4 = "1";
				break;
			case 3:
				opacityIconEmoji3 = "1";
				break;
			case 2:
				opacityIconEmoji2 = "1";
				break;
			case 1:
				opacityIconEmoji1 = "1";
				break;
			default:
				console.error("Invalid value", rating);
		}

		return `
			<div style="text-align: left;">
				<span><img style="vertical-align:middle; height: 16px; opacity: ${opacityIconEmoji1}; display: initial;" src="${iconEmoji1}"/></span>
				<span><img style="vertical-align:middle; height: 16px; opacity: ${opacityIconEmoji2}; display: initial;" src="${iconEmoji2}"/></span>
				<span><img style="vertical-align:middle; height: 16px; opacity: ${opacityIconEmoji3}; display: initial;" src="${iconEmoji3}"/></span>
				<span><img style="vertical-align:middle; height: 16px; opacity: ${opacityIconEmoji4}; display: initial;" src="${iconEmoji4}"/></span>
				<span><img style="vertical-align:middle; height: 16px; opacity: ${opacityIconEmoji5}; display: initial;" src="${iconEmoji5}"/></span>
			</div>
		`;
	}

	hide() {
        this.#balloon.style.display = 'none';
	}

	async show(icon) {
		if (icon.dataset.domain == undefined) {
			return;
		}
		let frame = document.getElementById("fs-ols-frame");
		
		frame.srcdoc = this.getTemplate(icon.dataset.ext_name, 
										icon.dataset.rating, 
										icon.dataset.domain, 
										icon.dataset.categories, 
										parseInt(icon.dataset.trustworthiness),
										icon.dataset.typeIcon);

		await applyCustomizedColorsIfNeeded(this.#customization, frame);
		this.#balloon.style.top = getOffset(icon).top - 172 + "px";
		this.#balloon.style.left = getOffset(icon).left - 13 + "px";
		this.#balloon.style.display = 'block';
	}
}
