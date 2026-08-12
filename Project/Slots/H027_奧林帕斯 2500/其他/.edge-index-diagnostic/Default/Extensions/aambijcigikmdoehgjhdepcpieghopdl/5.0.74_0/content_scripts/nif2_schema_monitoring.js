class FsSchemaMonitor {

    #mediaKeyDark = '(prefers-color-scheme: dark)';
    #schemaChangedCallback;

    start() {
        // get initial state
        this.#updateState();

        // start monitoring for changes
        window.matchMedia(this.#mediaKeyDark).addEventListener('change', () => {
            this.#updateState();
        });
    }

    setSchemaChangedCallback(callback) {
        this.#schemaChangedCallback = callback;
    }

    // private update function
    #updateState() {
        const isDarkMode = window.matchMedia(this.#mediaKeyDark).matches;
        chrome.runtime.sendMessage({
            type: MessageName.SchemaChanged,
            schema: isDarkMode ? Schema.Dark : Schema.Light
        });
        if (this.#schemaChangedCallback) {
            this.#schemaChangedCallback(isDarkMode);
        }
    }
}