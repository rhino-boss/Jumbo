/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function fsGetValueDefault(value, defaultString) {
    if (typeof value === "undefined" || value === null) {
        return defaultString;
    }

    if (value.length === 0) {
        return defaultString;
    }

    return value;
}

function fsMatchParentNode(node, className, exactMatch, depth) {
    for (var i = 0; i <= depth; i++) {
        if (!node) {
            break;
        }

        if (fsMatchClass(node, className, exactMatch)) {
            return true;
        }

        node = node.parentNode;
    }

    return false;
}

function fsMatchClass(node, expectedValue, exactMatch) {
    if (!node || !expectedValue || !node.getAttributeNode) {
        return false;
    }

    var attribute = node.getAttributeNode('class') || node.getAttributeNode('className');
    if (!attribute) {
        return false;
    }

    var actualValueLow = attribute.nodeValue.toLowerCase();
    var expectedValueLow = expectedValue.toLowerCase();

    return exactMatch ? actualValueLow === expectedValueLow : actualValueLow.indexOf(expectedValueLow) >= 0;
}

function fsSetStyle(node, styleText) {
    if (node.style.setAttribute) {
        node.style.setAttribute("cssText", styleText);
    } else {
        node.setAttribute("style", styleText);
    }
}

function fsSetStyleToParentNodes(initialNode, styleText, nodeDepth) {
    var node = initialNode.parentNode;

    for (var x = 0; x < nodeDepth; x++) {
        if (!node) {
            break;
        }

        fsSetStyle(node, styleText);
        node = node.parentNode;
    }
}

function fsSome(elements) {
    if (typeof elements !== "object" || typeof elements.length === "undefined") {
        return false;
    }

    for (var i = 0; i < elements.length; i++) {
        if (elements[i]) {
            return true;
        }
    }

    return false;
}

function htmlToElem(html) {
	let temp = document.createElement('template');
	html = html.trim();
	temp.innerHTML = html;
	return temp.content.firstChild;
}

function getOffset(el) {
    const rect = el.getBoundingClientRect();
    return {
        left: rect.left + window.scrollX,
        top: rect.top + window.scrollY
    };
}
