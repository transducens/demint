
// Take into account that these functions will be run automatically when passed as parameter

function js_autoscroll_by_id(id_param) {
    const id_holder = id_param
    console.log("Searching for id:", id_holder);
    const element = document.getElementById(id_holder); 
    if (element) { 
        const anchors = document.querySelectorAll('#transcript_id a');
        anchors.forEach(anchor => {
            anchor.style.backgroundColor = 'transparent';
        });

        element.scrollIntoView({behavior: 'smooth', block: 'center'}); 
        element.animate([{ backgroundColor: 'darkred' }, { backgroundColor: 'transparent' }], { duration: 3000, iterations: 1 }); 
        element.style.backgroundColor = 'darkred';
    } 
    else { 
        console.log('Element not found for:', id_holder); 
    }
}

function js_autoscroll_by_value(word_to_search) {
    try {
        console.log("Searching for:", word_to_search);
        const anchors = document.querySelectorAll('#transcript_id a');
        let found = false;
        anchors.forEach(anchor => {
            if (anchor.textContent.includes(word_to_search)) {
                anchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                anchor.animate([
                    { backgroundColor: 'yellow' },
                    { backgroundColor: 'transparent' }
                ], {
                    duration: 2000,
                    iterations: 1
                });
                found = true;
            }
        });
        if (!found) {
            console.log('Element not found for:', word_to_search);
        }
    } catch (error) {
        console.error("Error in autoscroll_to_string:", error);
    }
}