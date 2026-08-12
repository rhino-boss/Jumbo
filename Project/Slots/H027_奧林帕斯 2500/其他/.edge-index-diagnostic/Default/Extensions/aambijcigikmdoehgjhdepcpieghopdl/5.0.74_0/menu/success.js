/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

document.addEventListener("DOMContentLoaded", () => {
    parent.document.getElementById("footer-panel").style.removeProperty("display");
    let reportButton = document.getElementById("btn-report");
    if (reportButton) {
        reportButton.addEventListener("click", () => {
            window.location.href = "new_rating.html";
        });
    }
})
