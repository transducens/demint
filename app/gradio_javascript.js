
// Take into account that these functions will be run automatically when passed as parameter

function js_set_dark_mode() {
    const url = new URL(window.location);
    console.log("set dark mode");

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}

