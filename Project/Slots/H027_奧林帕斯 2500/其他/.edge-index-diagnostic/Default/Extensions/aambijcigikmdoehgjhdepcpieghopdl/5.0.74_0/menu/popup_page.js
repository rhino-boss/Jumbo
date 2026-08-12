/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function getSortedCategories() {
    let catList = [];
    Object.keys(LocalizedCategories).forEach( (category) => {
        let catObj = {};
        catObj.id = category;
        let loc = chrome.i18n.getMessage(`search_rating_${LocalizedCategories[category]}`);
        catObj.name = loc || LocalizedCategories[category];
        catObj.logo = `../img/categories/${category}.svg`;
        catList.push(catObj);
    });
    return catList.sort((a, b) => a.name.localeCompare(b.name));
};

function getCheckboxEl(category) {
    let span = document.createElement("span");
    span.setAttribute("class", "hds-checkbox-item");

    let input = document.createElement("input");
    input.setAttribute("id", category.id);
    input.setAttribute("class", "hds-checkbox");
    input.setAttribute("type", "checkbox");
    span.appendChild(input);

    let img = document.createElement("img");
    img.setAttribute("src", category.logo);
    img.style.height = "16px";
    span.appendChild(img);

    let label = document.createElement("label");
    label.setAttribute("for", category.id);
    let labelText = document.createTextNode(category.name);
    label.appendChild(labelText);
    span.appendChild(label);

    return span;
};

