
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
                if (/disease/i.test(placeholder) || /ethnicity/i.test(placeholder)) return "efo";
                if (/anatomical/i.test(placeholder)) return "uberon";
                if (/cell type/i.test(placeholder)) return "cl";
                if (/phenotypic/i.test(placeholder)) return "hp";
                if (/organism/i.test(placeholder)) return "ncbitaxon";
                if (/condition/i.test(placeholder)) return "xco";
                if (/treatment/i.test(placeholder)) return "dron";  
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
        // Add treatments
        if (e.target.classList.contains('add-treatment-btn')) {
            const wrapper = e.target.closest('.treatment-wrapper');
            const newField = document.createElement('div');
            newField.classList.add('treatment-field', 'mb-2');
            newField.innerHTML = `
                <input type="text" name="treatment[0][]" class="form-control form-control-sm ols-search">
                <button type="button" class="btn btn-sm btn-outline-danger remove-treatment-btn">Remove</button>`;
            wrapper.insertBefore(newField, e.target);
            initializeAutocomplete(newField.querySelector('.ols-search'));
        }
        // Add remove buttons
        if (e.target.classList.contains('remove-disease-btn') || e.target.classList.contains('remove-celltype-btn') || e.target.classList.contains('remove-phenotype-btn') || e.target.classList.contains('remove-treatment-btn')) {
            e.target.parentElement.remove();
        }
    });
    // Enable all (i) info in the metadata table on each column.
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

/**
 ** Ladder options to show based on chosen gel electrophoresis device.
 */
const ladderOptions = {
  "2100 Bioanalyzer Instrument, Agilent": [
    "DNA 1000", "DNA 12000", "DNA 7500"
  ],
  "4150 TapeStation System, Agilent": [
    "gDNA", "HS gDNA", "D5000", "HS D5000", "D1000"
  ],
  "4200 TapeStation System, Agilent": [
    "gDNA", "HS gDNA", "D5000", "HS D5000", "D1000"
  ],
  "5200 Fragment Analyzer System, Agilent": [
    "NGS Fragment Kit (1-6000bp)", "HS NGS Fragment Kit (1-6000bp)",
    "Small Fragment Kit (50 to 1500 bp)", "HS Small Fragment Kit (50 to 1500 bp)",
    "gDNA", "HS gDNA", "Large Fragment Kit", "HS Large Fragment 50 kb kit",
    "Plasmid DNA Analysis Kit (2,000 to 10,000 bp)",
    "dsDNA 905 Reagent Kit (1-500bp)", "dsDNA 910 Reagent Kit (35-1500bp)",
    "dsDNA 915 Reagent Kit (35-5000bp)", "dsDNA 920 Reagent Kit (75-15000bp)",
    "dsDNA 930 Reagent Kit (75-20000bp)", "dsDNA 935 Reagent Kit (1-1500bp)"
  ],
  "5300 Fragment Analyzer System, Agilent": [
    "NGS Fragment Kit (1-6000bp)", "HS NGS Fragment Kit (1-6000bp)",
    "Small Fragment Kit (50 to 1500 bp)", "HS Small Fragment Kit (50 to 1500 bp)",
    "gDNA", "HS gDNA", "Large Fragment Kit", "HS Large Fragment 50 kb kit",
    "Plasmid DNA Analysis Kit (2,000 to 10,000 bp)",
    "dsDNA 905 Reagent Kit (1-500bp)", "dsDNA 910 Reagent Kit (35-1500bp)",
    "dsDNA 915 Reagent Kit (35-5000bp)", "dsDNA 920 Reagent Kit (75-15000bp)",
    "dsDNA 930 Reagent Kit (75-20000bp)", "dsDNA 935 Reagent Kit (1-1500bp)"
  ],
  "5400 Fragment Analyzer System, Agilent": [
    "NGS Fragment Kit (1-6000bp)", "HS NGS Fragment Kit (1-6000bp)",
    "Small Fragment Kit (50 to 1500 bp)", "HS Small Fragment Kit (50 to 1500 bp)",
    "gDNA", "HS gDNA", "Large Fragment Kit", "HS Large Fragment 50 kb kit",
    "Plasmid DNA Analysis Kit (2,000 to 10,000 bp)",
    "dsDNA 905 Reagent Kit (1-500bp)", "dsDNA 910 Reagent Kit (35-1500bp)",
    "dsDNA 915 Reagent Kit (35-5000bp)", "dsDNA 920 Reagent Kit (75-15000bp)",
    "dsDNA 930 Reagent Kit (75-20000bp)", "dsDNA 935 Reagent Kit (1-1500bp)"
  ],
  "Qsep 1 Bio-Fragment Analyzer, Nippon": [
    "10-50000 bp", "10-1500 bp", "10-5000 bp"
  ],
  "Qsep 100 Bio-Fragment Analyzer, Nippon": [
    "10-50000 bp", "10-1500 bp", "10-5000 bp"
  ],
  "Qsep 400 Bio-Fragment Analyzer, Nippon": [
    "10-50000 bp", "10-1500 bp", "10-5000 bp"
  ]
};

/**
 ** Update ladder options displayed to the user automatically when a device is chosen.
 */
document.addEventListener('change', function (e) {
  if (e.target.matches('.device-select')) {
    const row = e.target.closest('tr');
    const ladderSelect = row.querySelector('.ladder-select');
    // Load chosen device
    const selectedDevice = e.target.value;
    const ladders = ladderOptions[selectedDevice] || [];
    // Set display ladder type to default Select
    ladderSelect.innerHTML = '<option value="">Select</option>';
    // Create ladder options based on device
    ladders.forEach(ladder => {
      const opt = document.createElement('option');
      opt.textContent = ladder;
      opt.value = ladder;
      ladderSelect.appendChild(opt);
    });
    // Always enable also Custom option
    const customOpt = document.createElement('option');
    customOpt.textContent = 'Custom';
    customOpt.value = 'custom';
    ladderSelect.appendChild(customOpt);
  }
});

/**
 * This method handles any select that has the custom option.
 * In that case when the custom is selected the select is 
 * converted into text option and user can type their custom
 * value.
 */
document.addEventListener('change', function (e) {
  if (e.target.tagName === 'SELECT' && e.target.value === 'custom') {
    const select = e.target;
    // Creat a text input
    const input = document.createElement('input');
    input.type = 'text';
    input.name = select.name;
    input.className = select.className;
    input.placeholder = 'Enter custom value';
    input.required = true;
    input.value = '';
    // Replace select with text
    select.parentNode.replaceChild(input, select);
    // Switch back to select if text is deleted by user
    input.addEventListener('blur', () => {
      if (input.value.trim() === '') {
        input.parentNode.replaceChild(select, input);
        select.value = '';
      }
    });
  }
});