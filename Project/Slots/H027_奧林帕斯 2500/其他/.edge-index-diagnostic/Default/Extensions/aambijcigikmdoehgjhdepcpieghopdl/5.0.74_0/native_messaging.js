/*
 * Copyright (c) F-Secure Corporation. All rights reserved.
 * See license terms for the related product.
 */

class NativeMessagingHost {

    #port;
    #failedConnectionCount = 0;
    #lastConnectionTime = 0;
    #reconnectLimitMilliseconds = 10000;
    #reconnectUpperLimit = 10;

    constructor() {
        this.pendingResponses = [];
        this.id = 0;
        this.serverId = "";
        this.connect();
    }

    setServerRestartedCallback(callback) {
        this.serverRestartedCallback = callback;
    }

    setSettingsChangedCallback(callback) {
        this.settingsChangedCallback = callback;
    }

    setBankingModeChangedCallback(callback) {
        this.bankingModeChangedCallback = callback;
    }

    setOnPortDisconnectCallback(callback) {
        this.onPortDisconnectCallback = callback;
    }

    #shouldConnectToHost() {
        const now = new Date().getTime();
        if (this.#lastConnectionTime !== 0 && 
            (now - this.#lastConnectionTime) < this.#reconnectLimitMilliseconds && 
            this.#failedConnectionCount > this.#reconnectUpperLimit) {
            console.debug(`More than ${this.#reconnectUpperLimit} connection attemps in ${this.#reconnectLimitMilliseconds/1000} seconds, ignoring.`);
            return false;
        }

        console.debug(`Will connect to native messaging host. Failed count: ${this.#failedConnectionCount}`);
        return true;
    }

    #resetFailedConnectState() {
        this.#failedConnectionCount = 0;
    }

    connect() {
        if (!this.#shouldConnectToHost()) {
            return;
        }
        this.#lastConnectionTime = new Date().getTime();
        const onMessage = response => {
            this.#resetFailedConnectState(); // reset fail state when successfully receiving response from the host
            if (response.id == "settings") { // special settings message, not received as a response to sent message
                console.log("Received settings:", JSON.stringify(response.settings));
                if (this.settingsChangedCallback) {
                    this.settingsChangedCallback(response.settings);
                }
            }
            if (response.id == "bankingSession") {
                console.log("Banking mode is changed to:", JSON.stringify(response.bankingSession));
                if (this.bankingModeChangedCallback) {
                    this.bankingModeChangedCallback(response.bankingSession);
                }
            }
            else {
                if (typeof response.server != "undefined") {
                    if (response.server != this.serverId) {
                        this.serverId = response.server;
                        console.log("Server ID changed to", this.serverId);
                        if (this.serverRestartedCallback) {
                            this.serverRestartedCallback();
                        }
                    }
                }
                
                const found = this.pendingResponses.findIndex(item => item.id === response.id);
                if (found !== -1) {
                    console.log("Received:", JSON.stringify(response));

                    this.pendingResponses[found].callback(response);
                    this.pendingResponses.splice(found, 1); // Remove pending response
                }
            }
        };

        this.#port = chrome.runtime.connectNative(FS_NATIVE_MESSAGING_APP);
        this.#port.onMessage.addListener(onMessage);
        const self = this;
        this.#port.onDisconnect.addListener(() => {
            if (self.onPortDisconnectCallback) {
                self.onPortDisconnectCallback();
            }
            self.#port = null;
            self.#failedConnectionCount++;
            self.#clearMessageQueue();
        });
    }

    postMessage(message) {
        return new Promise((resolve) => {
            const callback = response => {
                resolve(response);
            };

            if (!this.#port) {
                this.connect();
            }

            const id = ++this.id;
            if (this.#port) {
                message.id = id;
                this.pendingResponses.push({ id, callback });
                this.#port.postMessage(message);
                console.log("Sent:", JSON.stringify(message));
            } else {
                console.error('Port missing. Not sending message to the native messaging host');
                this.#generateEmptyResponse(id, callback);
            }
        });
    }
    
    isServerIdValid() {
        return this.serverId != "";
    }

    #clearMessageQueue() {
        this.pendingResponses.forEach(pendingResponse => {
            this.#generateEmptyResponse(pendingResponse.id, pendingResponse.callback);
        });
    }

    #generateEmptyResponse(id, callback) {
        const emptyResponse = {
            id: id
        };
        callback(emptyResponse);
    }
};

class WebSocketMessagingHost {
    
    #isConnected = false
    #failedConnectionCount = 0;
    #lastConnectionTime = 0;
    #reconnectLimitMilliseconds = 10000;
    #reconnectUpperLimit = 10;
    #couldConnectEver = false
    #socket;

    constructor() {
        this.pendingResponses = [];
        this.id = 0;
        this.serverId = "";
        this.connect();
    }

    setServerRestartedCallback(callback) {
        this.serverRestartedCallback = callback;
    }

    setSettingsChangedCallback(callback) {
        this.settingsChangedCallback = callback;
    }

    setBankingModeChangedCallback(callback) {
        this.bankingModeChangedCallback = callback;
    }

    setOnPortDisconnectCallback(callback) {
        this.onPortDisconnectCallback = callback;
    }
    
    connect() {
            if (!this.#shouldConnectToHost()) {
                return;
            }
            this.#socket = new WebSocket(WS_WEB_SOCKET_ADDRESS);
            this.#lastConnectionTime = new Date().getTime();
            const onMessage = rawResponse => {
                let response = JSON.parse(rawResponse.data);
                this.#resetFailedConnectState(); // reset fail state when successfully receiving response from the host
                if (response.id == "settings") { // special settings message, not received as a response to sent message
                    console.log("Received settings:", JSON.stringify(response.settings));
                    if (this.settingsChangedCallback) {
                        this.settingsChangedCallback(response.settings);
                    }
                }
                if (response.id == "bankingSession") {
                    console.log("Banking mode is changed to:", JSON.stringify(response.bankingSession));
                    if (this.bankingModeChangedCallback) {
                        this.bankingModeChangedCallback(response.bankingSession);
                    }
                }
                else {
                    if (typeof response.server != "undefined") {
                        if (response.server != this.serverId) {
                            this.serverId = response.server;
                            console.log("Server ID changed to", this.serverId);
                            if (this.serverRestartedCallback) {
                                this.serverRestartedCallback();
                            }
                        }
                    }
                    
                    const found = this.pendingResponses.findIndex(item => item.id === response.id);
                    if (found !== -1) {
                        console.log("Received:", JSON.stringify(response));
    
                        this.pendingResponses[found].callback(response);
                        this.pendingResponses.splice(found, 1); // Remove pending response
                    }
                }
            };

            this.#socket.addEventListener("open", () => {
                this.#couldConnectEver = true
                this.#isConnected = true;
                this.#lastConnectionTime = new Date().getTime();
            });
            const self = this;
            
            this.#socket.addEventListener("close", () => {
                if (self.onPortDisconnectCallback) {
                    self.onPortDisconnectCallback();
                }
                self.#isConnected = false;
                self.#failedConnectionCount++;
                self.#clearMessageQueue();
            });

            this.#socket.addEventListener("message", onMessage);
            
            this.#socket.addEventListener("error", (err)=> {
                console.log(err);
                this.#isConnected = false;
            });
    }

    postMessage(message) {
        return new Promise((resolve) => {
            const callback = response => {
                resolve(response);
            };

            if (!this.#isConnected) {
                this.connect();
            }

            const id = ++this.id;
            if (this.#isConnected) {
                message.id = id;
                this.pendingResponses.push({ id, callback });
                this.#socket.send(JSON.stringify(message));
                console.log("Sent:", JSON.stringify(message));
            } else {
                console.error('Port missing. Not sending message to the native messaging host');
                this.#generateEmptyResponse(id, callback);
            }
        });
    }

    #generateEmptyResponse(id, callback) {
        const emptyResponse = {
            id: id
        };
        callback(emptyResponse);
    }

    #shouldConnectToHost() {
        const now = new Date().getTime();
        if (this.#lastConnectionTime !== 0 && 
            (now - this.#lastConnectionTime) < this.#reconnectLimitMilliseconds && 
            this.#failedConnectionCount > this.#reconnectUpperLimit) {
            console.debug(`More than ${this.#reconnectUpperLimit} connection attemps in ${this.#reconnectLimitMilliseconds/1000} seconds, ignoring.`);
            return false;
        }

        console.debug(`Will connect to native messaging host. Failed count: ${this.#failedConnectionCount}`);
        return true;
    }
    #clearMessageQueue() {
        this.pendingResponses.forEach(pendingResponse => {
            this.#generateEmptyResponse(pendingResponse.id, pendingResponse.callback);
        });
    }
    #resetFailedConnectState() {
        this.#failedConnectionCount = 0;
    }
    isServerIdValid() {
        return this.#couldConnectEver;
    }
    
};

class MessagingHostFactory {
    getMessageHost() {
        if (navigator.userAgentData && navigator.userAgentData.platform) {
            switch (navigator.userAgentData.platform) {
                case 'Chrome OS':
                    return new WebSocketMessagingHost();
                default:
                    return new NativeMessagingHost();
            }
        } else {
            return new NativeMessagingHost();
        }
    }
}
