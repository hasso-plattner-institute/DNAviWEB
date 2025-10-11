
/*
Initialize OLS autocomplete for a single input element
Implement Autocomplete Search Box with debounce technique
this way not for every letter typed an expensive API call is made
Based on: https://www.geeksforgeeks.org/html/implement-search-box-with-debounce-in-javascript/
*/
function initializeAutocomplete(input) {
        // Styling the suggestion box for recommendations
        const suggestionBox = document.createElement("div");
        suggestionBox.classList.add("autocomplete-box");
        suggestionBox.style.cssText = `
            position: absolute;
            border: 1px solid #ccc;
            background: #fff;
            z-index: 1000;
            display: none;
            max-height: 150px;
            overflow-y: auto;
            border-radius: 4px;
            width: ${input.offsetWidth}px;
        `;
        input.parentElement.style.position = "relative";
        input.parentElement.appendChild(suggestionBox);
        // Make the API call to recommend something
        const makeAPICall = async (searchValue) => {
            const query = searchValue.trim();
            suggestionBox.innerHTML = "";
            // If the user did not type, hide the suggestion box 
            // and stop making an API calls
            if (query === "" || query == null) {
                suggestionBox.style.display = "none";
                return;
            }
            // Define url to search for based on the input parameters
            const detectOntology = (placeholder) => {
                if (/disease/i.test(placeholder)) return "efo";
                if (/anatomical/i.test(placeholder)) return "uberon";
                if (/cell type/i.test(placeholder)) return "cl";
                if (/phenotypic/i.test(placeholder)) return "hp";
                if (/organism/i.test(placeholder)) return "ncbitaxon";
                if (/condition/i.test(placeholder)) return "ncit"; 
                return "efo";
            };
            const ontology = detectOntology(input.placeholder);
            const url = `/ols_proxy?q=${encodeURIComponent(query)}&ontology=${ontology}`;
            console.log("Fetching OLS URL:", url);
            try {
                const res = await fetch(url);
                if (!res.ok) throw new Error("OLS API fetching error!");
                const data = await res.json(); // full JSON returned
                // OLS json data has the term we search form inside respons:docs:label
                // example: https://www.ebi.ac.uk/ols4/api/search?q=cancer&ontology=efo&type=class&rows=10
                const results = data.response.docs || [];
                // IF API finds no matches for the user's query, hide the suggestion box
                // and stop making an API calls
                if (results.length == 0) {
                    suggestionBox.style.display = "none";
                    return;
                }
                // Present API call results on suggestion box
                results.forEach(item => {
                    const div = document.createElement("div");
                    // Add Style
                    div.textContent = item.label;
                    div.style.padding = "5px";
                    div.style.cursor = "pointer";
                    // When mouse down even happens meaning the term is clicked
                    // make the label appear in the input and
                    // hide the suggestion box
                    div.addEventListener("mousedown", () => {
                        input.value = item.label;
                        suggestionBox.style.display = "none";
                    });
                    suggestionBox.appendChild(div);
                });
                suggestionBox.style.display = "block";
            } catch (err) {
                console.error("OLS API error:", err);
                suggestionBox.style.display = "none";
            }
        };
        // Debounce method, after last typed letter wait 300 ms and
        // only then make API call, this is important otherwise we will call API
        // for every letter typed which is expensive
        const debounce = (fn, delay = 300) => {
            let timerId;
            return (...args) => {
                clearTimeout(timerId);
                timerId = setTimeout(() => fn(...args), delay);
            };
        };
        // Everytine input is typed in the html call makeAPICall with the debounce method
        input.addEventListener("input", debounce(e => makeAPICall(e.target.value), 300));
        // Any click out of the autocomplete suggestion box cases hiding the suggestion box
        document.addEventListener("click", e => {
            if (!suggestionBox.contains(e.target) && e.target !== input) {
                suggestionBox.style.display = "none";
            }
        });
    };

/*
Implement Autocomplete Search Box with debounce technique
this way not for every letter typed an expensive API call is made
Based on: https://www.geeksforgeeks.org/html/implement-search-box-with-debounce-in-javascript/
*/
document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll(".ols-search");
    // Loop on every input in html and set autocomplet
    inputs.forEach(input => initializeAutocomplete(input));
    // Handle added disease/cell type inputs
    document.addEventListener('click', function(e) {
        // Add disease
        if (e.target.classList.contains('add-disease-btn')) {
            const wrapper = e.target.closest('.disease-wrapper');
            const newField = document.createElement('div');
            newField.classList.add('disease-field', 'mb-2');
            newField.innerHTML = `
                <input type="text" name="disease[0][]" class="form-control form-control-sm ols-search">
                <button type="button" class="btn btn-sm btn-outline-danger remove-disease-btn">Remove</button>`;
            wrapper.insertBefore(newField, e.target);
            initializeAutocomplete(newField.querySelector('.ols-search'));
        }
        
        // Add cell type
        if (e.target.classList.contains('add-celltype-btn')) {
            const wrapper = e.target.closest('.celltype-wrapper');
            const newField = document.createElement('div');
            newField.classList.add('celltype-field', 'mb-2');
            newField.innerHTML = `
                <input type="text" name="cell_type[0][]" class="form-control form-control-sm ols-search">
                <button type="button" class="btn btn-sm btn-outline-danger remove-celltype-btn">Remove</button>
            `;
            wrapper.insertBefore(newField, e.target);
            initializeAutocomplete(newField.querySelector('.ols-search'));
        }
        // Add phenotypic abnormality
        if (e.target.classList.contains('add-phenotype-btn')) {
            const wrapper = e.target.closest('.phenotype-wrapper');
            const newField = document.createElement('div');
            newField.classList.add('phenotype-field', 'mb-2');
            newField.innerHTML = `
                <input type="text" name="phenotypic_abnormality[0][]" class="form-control mb-2 ols-search">
                <button type="button" class="btn btn-sm btn-outline-danger remove-phenotype-btn">Remove</button>
            `;
            wrapper.insertBefore(newField, e.target);
            initializeAutocomplete(newField.querySelector('.ols-search'));
        }
        // Add remove buttons
        if (e.target.classList.contains('remove-disease-btn') || e.target.classList.contains('remove-celltype-btn') || e.target.classList.contains('remove-phenotype-btn')) {
            e.target.parentElement.remove();
        }
    });
});

