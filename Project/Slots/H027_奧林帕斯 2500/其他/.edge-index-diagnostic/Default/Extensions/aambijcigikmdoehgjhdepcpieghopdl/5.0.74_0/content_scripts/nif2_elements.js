/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function apply_styles(styles, element) {
    for (const [attribute, value] of Object.entries(styles)) {
        element.style[attribute] = value;
    }
}

function fsGeneratePlaceHolderId(url) {
    url = url.replace(/^http:\/\/www|[^\w\s]/gi, '');
    return url + '_' + Math.floor(Math.random() * 1001) + '_' + Math.floor(Math.random() * 101);
}

function fsRatingIcon(element, url, engineClass) {
    var FSMARKED_CLASS = 'fsrating_marked';
    if (element.classList.contains(FSMARKED_CLASS)) {
        return '';
    }

    var id = fsGeneratePlaceHolderId(url);
    var img = document.createElement('img');
    img.setAttribute('id', id);
    img.setAttribute('src', fs_loading_svg);
    img.setAttribute('class', 'fs-rating-summary-rating-icon fs-spin');
    img.setAttribute('data-rating', 'loading');

    var rs_shell = fsRatingSummaryShell(id, img, engineClass);

    element.classList.add(FSMARKED_CLASS);

    if (engineClass == "fs-ddg") {
        // if result has website logo, need to add icon before this logo
        let imgElements = element.parentNode.getElementsByTagName("svg");
        if (imgElements.length == 0) {
            imgElements = element.parentNode.getElementsByTagName("img");
        }
        if (element.classList[0] != "f3uDrYrWF3Exrfp1m3Og" || element.parentNode.childNodes.length == 1) {
            rs_shell.style.top = "3px";
        }
        if (imgElements.length > 0) {
            element.parentNode.insertBefore(rs_shell, element.parentNode.firstChild);
        }
        else {
            element.parentNode.insertBefore(rs_shell, element);
        }
        return id;
    }

    element.parentNode.insertBefore(rs_shell, element);

    if (engineClass == "fs-google") {
        // if result has website logo, apply fix to center rating icon properly
        if (element.getElementsByTagName("svg").length > 0 || element.getElementsByTagName("img").length > 0) {
            // Google has a new span element with the class '.V9tjod'
            //      and because of the new span with 'scaleY(-1)' we need to center it with a negative value
            // old value: rs_shell.style.top = "8px" 
            rs_shell.style.top = "-8px";
        }
    }

    return id;
}

function fsRatingSummaryShell(id, child1, engineClass) {
    var element = document.createElement('div');
    element.setAttribute('id', 'rs_' + id);
    element.setAttribute('class', 'fs-bubble-info ' + engineClass);
    element.appendChild(child1);

    // used by default when CSS styles get unloaded by the browser
    // this can happen when the extension is disabled or when access to the web page is revoked by the user in Safari
    const invisibleStyles = {
        visibility: 'hidden',
        display: 'none',
        opacity: 0
    };
    apply_styles(invisibleStyles, element);

    return element;
}


function hasParentClass(child, classname){
    if (child.className.split(' ').indexOf(classname) >= 0) {
        return true;
    }
    try {
        return child.parentNode && hasParentClass(child.parentNode, classname);
    } 
    catch(TypeError) {
        return false;
    }
}
