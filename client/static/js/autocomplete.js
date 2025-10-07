/*
Implement Autocomplete Search Box with debounce technique
this way not for every letter typed an expensive API call is made
Based on: https://www.geeksforgeeks.org/html/implement-search-box-with-debounce-in-javascript/
*/
document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll(".ols-search");
    // Loop on every input in html and set autocomplet
    inputs.forEach(input => {
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
            const ontology = /anatomical/i.test(input.placeholder) ? "uberon" : "efo";
            const url = `/protect/ols_proxy?q=${encodeURIComponent(query)}&ontology=${ontology}`;
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
    });
});
