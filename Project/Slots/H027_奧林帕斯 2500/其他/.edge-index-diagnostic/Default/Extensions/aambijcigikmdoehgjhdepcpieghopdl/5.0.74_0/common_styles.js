/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

function applyCustomizedColorsIfNeeded(customization, frame) {
    return new Promise(resolve => {
        chrome.storage.local.get(["platform", "customization"], (storageResult) => {
            isRunningOnMac(storageResult.platform).then(result => {
                if (result) {
                    applyCustomizedColors(customization, frame, resolve);
                } else {
                    resolve();
                }
            });
        });
    });
}

function applyCustomizedColors(customization, frame, resolve) {
    if (frame) {
        frame.addEventListener('load', () => {
            setStyles(customization, frame.contentDocument);
            resolve();
        });
    } else {
        setStyles(customization, document);
        resolve();
    }
}

function setStyles(customization, customDocument) {
    const mainColor = customization.MainColor;
    const buttonColor = customization.SecondaryColor;
    if (!mainColor || mainColor.length === 0 || 
        !buttonColor || buttonColor.length === 0) {
        console.debug('Invalid colors provided in customization. Not proceeding.');
        return;
    }
    customDocument.documentElement.style.setProperty('--main-color', mainColor);
    customDocument.documentElement.style.setProperty('--button-color', buttonColor);
}

function isRunningOnMac(cachedPlatformInfo) {
    return new Promise(resolve => {
        if (cachedPlatformInfo && cachedPlatformInfo.os) {
            resolve(cachedPlatformInfo.os === 'mac' || cachedPlatformInfo.os === 'cros');
        } else {
            chrome.runtime.sendMessage({ type: MessageName.GetPlatformInfo }, (platformInfo) => {
                resolve(platformInfo.os === 'mac' || cachedPlatformInfo.os === 'cros');
            });
        }
    });
}

function loadCommonStyles() {
    return new Promise(resolve => {
        chrome.storage.local.get(["port", "platform", "customization"], (storageResult) => {
            isRunningOnMac(storageResult.platform).then(result => {
                if (result) {
                    applyCustomizedColors(storageResult.customization, null, resolve);
                } else {
                    loadRemoteCSS("common.css", storageResult.port, resolve);
                }
            });
        });
    });
}

function loadRemoteCSS(fileName, port, resolve) {
    let head = document.getElementsByTagName('head')[0];
    let style = document.createElement('link');
    style.href = `http://localhost:${port}/${fileName}`;
    style.type = 'text/css';
    style.rel = 'stylesheet';
    style.onload = function() {
        resolve();
    };
    style.onerror = function() {
        resolve();
    };
    head.append(style);
}