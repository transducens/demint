// Variable to store the interval ID
let intervalId = null;
// input json file path
let input_json_path = '/public/raw_sorted_sentence_collection.json';
let sentence_collection = {};
let transcript_innerHTML = '';

async function loadJSONData() {
    try {
        const response = await fetch(input_json_path);
        if (!response.ok) {
            throw new Error('Error in reading JSON file ' + response.statusText);
        }
        const data = await response.json();
        console.log(data);
        console.log('JSON data loaded.')
        processJSONData(data);
    } catch (error) {
        console.error('There has been a problem with your fetch operation:', error);
    }
}


// Function to process the JSON data
function processJSONData(data) {
    // Store the data in a variable
    sentence_collection = data;

    // Example of how you can use the data
    for (let key in sentence_collection) {
        if (sentence_collection.hasOwnProperty(key)) {
            //console.log(`ID: ${key}`)
            //console.log(`Time: ${sentence_collection[key].time}`);
            //console.log(`Speaker: ${sentence_collection[key].speaker}`);
            //console.log(`Sentence: ${sentence_collection[key].original_sentence}`);
            transcript_innerHTML += `<a id=sentence-${key}>
                ${sentence_collection[key].speaker}<br>
                ${sentence_collection[key].original_sentence}
                <br><br></a>`;
        }
    }
    console.log('JSON data processed.');
}


// Function to add or update the text component with the specified ID
function addTextToComponent() {
    parent_div_class='.MuiStack-root.css-zpi9s5'
    const targetElement = document.querySelector(parent_div_class);
    if (targetElement) {
        let textComponent = document.querySelector('#transcript-id');
        if (!textComponent) {
            // Create a new component if it doesn't exist
            textComponent = document.createElement('div');
            textComponent.id = 'transcript-id';
            textComponent.innerHTML = transcript_innerHTML;
            // Add the component to the right side of target element
            //targetElement.appendChild(textComponent);

            //or left side of the chat
            reference_div_class ='.MuiBox-root.css-egstdn'
            const referenceElement = document.querySelector(reference_div_class);
            if (referenceElement) {
                targetElement.insertBefore(textComponent, referenceElement);
            }

            console.log('New text component created and added.');
        } else {
            // Update the existing component
            textComponent.innerHTML = transcript_innerHTML;
            console.log('Existing text component updated.');
        }
    } else {
        console.warn('Target element not found.');
    }
}


// Function to set up the MutationObserver for a specific class
function setupMutationObserverForClass() {
    let class_component = '.MuiBox-root.css-egstdn'
    const targetNode = document.querySelector(class_component);
    if (!targetNode) {
        console.warn('Target "changing" node not found.');
        return;
    }
    
    const config = {
        attributes: true,
        childList: true,
        subtree: true
    };

    const callback = function(mutationsList, observer) {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList' || mutation.type === 'attributes' || mutation.type === 'subtree') {
                addTextToComponent();
                console.log('Mutation detected.')
            }
        }
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}


// Function to run periodically and stop when successful
function runPeriodically() {
    const targetElement = document.querySelector('.MuiStack-root.css-zpi9s5');
    const targetChangingElement = document.querySelector('.MuiBox-root.css-egstdn');
    if (targetElement && targetChangingElement) {
        clearInterval(intervalId);
        intervalId = null;
        console.log('Found both components');
        addTextToComponent();
        setupMutationObserverForClass();
    }
}


function js_autoscroll_function_by_value(word_to_search) {
    try {
        console.log("Searching for:", word_to_search);
        const anchors = document.querySelectorAll('#transcript-id a');  // Get all the anchor tags inside a div with id 'transcript-id'
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


function js_autoscroll_function_by_id(word_to_search) { 
    const element = document.getElementById(word_to_search); 
    if (element) { 
        element.scrollIntoView({behavior: 'smooth', block: 'center'}); 
        element.animate([{ backgroundColor: 'yellow' }, { backgroundColor: 'transparent' }], { duration: 2000, iterations: 1 }); 
    } 
    else { 
        console.log('Element not found for:', word_to_search); 
    }
}



// **************************************************
// ********************** MAIN **********************
// **************************************************
// Set up the interval to run the function every second (1000 milliseconds)
document.addEventListener('DOMContentLoaded', (event) => {
    loadJSONData();
    intervalId = setInterval(runPeriodically, 1000);    // run each second until the component is found
    console.log('Interval set up.');

    const socket = new WebSocket("ws://localhost:8001/ws");
});


