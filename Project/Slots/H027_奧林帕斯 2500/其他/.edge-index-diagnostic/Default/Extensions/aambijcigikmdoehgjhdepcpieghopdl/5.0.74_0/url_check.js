/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

document.addEventListener("DOMContentLoaded", function(event) {
	var urlParams = new URLSearchParams(window.location.search);
	const data = JSON.parse(new URLSearchParams(location.search).get("info"));
	document.getElementById("result_url").innerText = JSON.stringify(data.url);
	document.getElementById("result_cat").innerText = JSON.stringify(data.categories);
})