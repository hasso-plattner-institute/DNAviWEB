let ontologyMap = {};
// True if example data load was clicked
let EXAMPLE_CLICKED = false;

async function loadOntologyMap() {
    try {
        const res = await fetch("/static/json/ontology_map.json");
        if (!res.ok) throw new Error("Failed to load ontology_map.json");
        ontologyMap = await res.json();
    } catch (err) {
        console.error("Error loading ontology map:", err);
    }
}

/**
 * Handle adding custom columns button and adding new grouping checkbox for new column
 */
document.getElementById('addColumnBtn').addEventListener('click', function () {
  const columnName = prompt("Enter new column name:");
  if (!columnName) return;
  // Add new custom column checkbox to the grouping options
  if (!ALL_METADATA_COLUMNS.includes(columnName)) {
    ALL_METADATA_COLUMNS.push(columnName);
  }
  const table = document.getElementById('metadata-table');
  const headerRow = table.querySelector('thead tr');
  const newHeader = document.createElement('th');
  newHeader.textContent = columnName;
  headerRow.insertBefore(newHeader, headerRow.lastElementChild);
  makeColumnResizable(newHeader, table);
  const rows = table.querySelectorAll('tbody tr');
  rows.forEach(row => {
    const newCell = document.createElement('td');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = `custom_${columnName.toLowerCase().replace(/\s+/g, '_')}[]`;
    input.className = 'form-control form-control-sm';
    newCell.appendChild(input);
    row.insertBefore(newCell, row.lastElementChild);
  });
  //Refresh grouping checkboxess
  getGroupByCheckBoxes();
});

/**
  * Load example data into the form without immidiate submission
  */
document.getElementById('load-example').addEventListener('click', async () => {
  EXAMPLE_CLICKED = true;
  const files = [
      {url: './static/tests/electropherogram.csv', inputName: 'data_file'},
      {url: './static/tests/metadata.csv', inputName: 'meta_file'}
  ];
  // Load electropherogram and metadata
  for (const file of files) {
      const response = await fetch(file.url);
      const blob = await response.blob();
      const fileObj = new File([blob], file.url.split('/').pop(), {type: blob.type});
      const input = document.querySelector(`input[name="${file.inputName}"]`);
      if (input) {
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(fileObj);
          input.files = dataTransfer.files;
          if (file.inputName === "meta_file") {
            addCSVColumnsToAll(fileObj);
          }
      }
  }
  // Automatically select HSD5000 ladder option
  const ladderOption = document.querySelector('input[name="ladder_file"][value="HSD5000"]');
  if (ladderOption) {
      ladderOption.checked = true;
      const fileContainer = document.getElementById('fileUploadContainer');
      if (fileContainer) fileContainer.style.display = 'none';
  }
  alert("Example data loaded! You can review or edit before submitting.");
});

/*
Initialize OLS autocomplete for a single input element
Implement Autocomplete Search Box with debounce technique
this way not for every letter typed an expensive API call is made
Based on: https://www.geeksforgeeks.org/html/implement-search-box-with-debounce-in-javascript/
*/
function initializeAutocomplete(input) {
        // Track last valid OLS term
        let lastSelected = "";
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
        document.body.appendChild(suggestionBox);
        const updatePosition = () => {
            const rect = input.getBoundingClientRect();
            suggestionBox.style.top = `${window.scrollY + rect.bottom}px`;
            suggestionBox.style.left = `${window.scrollX + rect.left}px`;
            suggestionBox.style.width = `${rect.width}px`;
        };
        // Make the API call to recommend something
        const makeAPICall = async (inputEl) => {
            updatePosition();
            const query = inputEl.value.trim();
            suggestionBox.innerHTML = "";
            // If the user did not type, hide the suggestion box 
            // and stop making an API calls
            if (!query) {
                suggestionBox.style.display = "none";
                return;
            }
            // Define url to search for based on the input parameters
            const detectOntology = (name) => {
                const lower = name.toLowerCase();
                for (const [key, value] of Object.entries(ontologyMap)) {
                  if (lower.includes(key)) return value;
                }
                return "";
            };
            const ontology = detectOntology(input.name.toLowerCase());
            const url = `/ols_proxy?q=${encodeURIComponent(query)}&ontology=${ontology}`;
            console.log("Fetching OLS URL:", url);
            try {
                const res = await fetch(url);
                if (!res.ok) throw new Error("OLS API fetching error!");
                const data = await res.json(); // full JSON returned
                // OLS json data has the term we search form inside respons:docs:label
                // example: https://www.ebi.ac.uk/ols4/api/search?q=cancer&ontology=efo&type=class&rows=10
                const results = data.response?.docs || data || [];
                // Filter to only display terms with id starting with the ontology prefix
                let filtered = [];
                if (ontology === "pathogen") {
                    filtered = results.filter(item =>
                        item.termId && item.termId.startsWith("NCBITaxon")
                    );
                } else {
                    const prefix = ontology.toUpperCase();
                    filtered = results.filter(item =>
                        item.termId && item.termId.toLowerCase().startsWith(prefix.toLowerCase())
                    );
                }
                // IF API finds no matches for the user's query, hide the suggestion box
                // and stop making an API calls
                if (filtered.length === 0) {
                    suggestionBox.style.display = "none";
                    return;
                }
                // Present API call results on suggestion box
                filtered.forEach(item => {
                    const div = document.createElement("div");
                    // Cancer (MONDO:0004992)
                    const id = item.termId || "";
                    div.textContent = `${item.label} (${id})`;
                    div.style.padding = "5px";
                    div.style.cursor = "pointer";
                    // When mouse down event happens meaning the term is clicked
                    // make the label appear in the input and
                    // hide the suggestion box
                    // and remember the term as last valid ols term
                    div.addEventListener("mousedown", () => {
                        input.value = `${item.label} (${id})`;
                        lastSelected = input.value;
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
        input.addEventListener("input", debounce(e => makeAPICall(e.target), 300));
        // Any click out of the autocomplete suggestion box cases hiding the suggestion box
        document.addEventListener("click", e => {
            if (!suggestionBox.contains(e.target) && e.target !== input) {
                suggestionBox.style.display = "none";
            }
        });
        window.addEventListener("scroll", updatePosition);
        window.addEventListener("resize", updatePosition);
        // Prohibit free text input
        // If not selected from ols options -> clear text and give a note
        // To only select from given choices
        input.addEventListener("blur", () => {
          if (input.value.trim() !== lastSelected) {
              input.value = "";
              input.classList.add("is-invalid");

              const msg = document.createElement("div");
              msg.className = "invalid-feedback d-block";
              msg.textContent = "Select from the dropdown.";
              input.parentNode.appendChild(msg);

              setTimeout(() => {
                  msg.remove();
                  input.classList.remove("is-invalid");
              }, 2000);
          }
      });
    };

/*
Implement Autocomplete Search Box with debounce technique
this way not for every letter typed an expensive API call is made
Based on: https://www.geeksforgeeks.org/html/implement-search-box-with-debounce-in-javascript/
*/
document.addEventListener("DOMContentLoaded", async () => {
    const table = document.getElementById("metadata-table");
    if (!table) return;
    table.querySelectorAll("th").forEach(th => makeColumnResizable(th, table));
    await loadOntologyMap();
    const inputs = document.querySelectorAll(".ols-search");
    // Loop on every input in html and set autocomplet
    inputs.forEach(input => initializeAutocomplete(input));
    // Enable all (i) info in the metadata table on each column.
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
    // Initial display of grouping checkboxes on page load
    getGroupByCheckBoxes();
});

/**
 * This method handles any select that has the custom option.
 * In that case when the custom is selected the select is 
 * converted into text option and user can type their custom
 * value.
 */
document.addEventListener('change', function (e) {
  if (e.target.tagName == 'SELECT' && e.target.value == 'custom') {
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
      if (input.value.trim() == '') {
        input.parentNode.replaceChild(select, input);
        select.value = '';
      }
    });
  }
});

let EGA_COLUMNS = [
    "Subject ID", "Disease", "Cell Type", "Sample Type", "Sample Collection Date", "Phenotypic Feature",
    "Material Anatomical Entity", "Biological Sex", "Age", "Organism",
    "Case vs Control", "Condition Under Study", "Is Deceased?", "Is Pregnant?",
    "Is Infection Suspected?", "Infection Strain", "Hospitalization Status",
    "Extraction Kit (DNA Isolation Method)",
    "DNA Mass", "DNA Mass Units", "Carrying Liquid Volume",
    "Carrying Liquid Volume Unit", "In vitro / In vivo",
    "Gel Electrophoresis Device", "Treatment", "Ethnicity"
];

let ELBS_COLUMNS = [
    "My patient(s) were informed about the potential consequences of unexpected or incidental ﬁndings",
    "Opt-out: My patient(s) do NOT wish to be informed about unexpected and/or incidental findings",
    "Test purpose (Why is this test performed):",
    "Pathological diagnosis",
    "Disease stage",
    "Burden of disease",
    "Disease status",
    "Previous and current oncological treatment",
    "Previously diagnosed malignancies",
    "Conﬁrmed tumor predisposition",
    "Mutations from previous tissue or liquid proﬁling available",
    "Previously identiﬁed CH (clonal hematopoiesis)-related variants",
    "Macroscopic abnormalities (e.g. hemolysis)",
    "Any sample QC not meeting criteria?",
    "Type of planned downstream assay",
    "LOD (limit of detection)",
    "LOB (limit of blank)",
    "LOQ (limit of quantiﬁcation)",
    "analytical sensitivity",
    "analytical speciﬁcity",
    "Sequencing: percentage of target region covered with the minimum required depth",
    "Sequencing: average sequencing depth",
    "Any downstream QC not meeting criteria?",
    "Recommendation for equivocal variants",
    "Pathogenic and likely pathogenic variants (incl. number of supporting reads, sequencing depth, VAF, number of mutated molecules, conﬁdence level)",
    "Variants in cancer susceptibility genes with VAF indicating germline origin (incl. number of supporting reads, sequencing depth, VAF, number of mutated molecules, conﬁdence level)",
    "Potential CH-related variants (incl. number of supporting reads, sequencing depth, VAF, number of mutated molecules, conﬁdence level)",
    "Recommendation for putative germline variants",
    "SCNA (estimated copy number or log2 ratio, conﬁdence level, potentially co-ampliﬁed genes and estimated size of the ampliﬁed/deleted segment)",
    "Negative results ( Tumor fraction – Not detected or Requested mutation is not detected)",
    "Unexpected findings",
    "Explanation why the ﬁndings were unexpected",
    "Clinically actionable results and evidence-based associations with response to speciﬁc drugs"
];

// This array will be dynamically updated when new columns are added from CSV upload/or custom columns added via UI
let ALL_METADATA_COLUMNS = [...EGA_COLUMNS, ...ELBS_COLUMNS];

/** 
 * Update grouping columns display to show all columns inside ALL_METADATA_COLUMNS
 * excluding Actions and SAMPLE columns
 */
function getGroupByCheckBoxes() {
    const container = document.getElementById("metadata-group-container");
    container.innerHTML = ""; 
    const EXCLUDED_COLUMNS = ["actions", "sample"];
        const allColumns = ALL_METADATA_COLUMNS.filter(col => 
        !EXCLUDED_COLUMNS.includes(col.toLowerCase())
    );
    allColumns.forEach(col => {
        const safeId = "group_" + col.toLowerCase().replace(/\s+/g, "_");
        const div = document.createElement("div");
        div.className = "form-check mb-1";
        div.innerHTML = `
            <input class="form-check-input"
                   name="metadata_group_columns_checkbox"
                   type="checkbox"
                   value="${col}"
                   id="${safeId}">
            <label class="form-check-label" for="${safeId}">${col}</label>
        `;
        container.appendChild(div);
    });
}

/**
 * On event: change of metadata file input upload
 * Read the new CSV file and add any new columns found to grouping checkboxes
 */
document.addEventListener('DOMContentLoaded', () => {
    const metaInput = document.querySelector('input[name="meta_file"]');
    if (metaInput) {
        metaInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                addCSVColumnsToAll(file);
            }
        });
    }
});

/**
 * This function reads a CSV file that was uploaded 
 * and adds any new columns found to grouping checkboxes.
 * This method ensures that even if the file was uploaded as csv all 
 * columns are available for grouping in the checkboxes.
 */
function addCSVColumnsToAll(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        let headers = text.split('\n')[0].split(',').map(h => h.trim());
        const EXCLUDED_COLUMNS = ["actions", "sample"];
        // Save all headers inside the example metadata file to auto select them later in grouping
        // Exclude only EXCLUDED_COLUMNS
        const newExampleHeadersToAddToGrouping = [];
        headers = headers.filter(h => !EXCLUDED_COLUMNS.includes(h.toLowerCase()));
        const table = document.getElementById('metadata-table');
        const headerRow = table.querySelector('thead tr');
        const rows = table.querySelectorAll('tbody tr');
        headers.forEach(header => {
            newExampleHeadersToAddToGrouping.push(header);
            if (!ALL_METADATA_COLUMNS.includes(header)) {
                ALL_METADATA_COLUMNS.push(header);
                const newHeader = document.createElement('th');
                newHeader.textContent = header;
                newHeader.style.fontWeight = 'normal';
                headerRow.insertBefore(newHeader, headerRow.lastElementChild);
                makeColumnResizable(newHeader, table);
                rows.forEach(row => {
                    const newCell = document.createElement('td');
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.name = `custom_${header.toLowerCase().replace(/\s+/g, '_')}[]`;
                    input.className = 'form-control form-control-sm';
                    newCell.appendChild(input);
                    row.insertBefore(newCell, row.lastElementChild);
                });
            }
        });
        // Refresh grouping checkboxes display
        getGroupByCheckBoxes();
        if (EXAMPLE_CLICKED) {
            autoSelectNewGroupColumns(newExampleHeadersToAddToGrouping);
            // reset flag so next uploads are not considered example uploads unless example data load clicked again
            EXAMPLE_CLICKED = false;
        }
    };
    reader.readAsText(file);
}

/**
 * When example data load clicked: Auto select all columns in the grouping checkboxes
 */
function autoSelectNewGroupColumns(newHeaders) {
    if (!Array.isArray(newHeaders) || newHeaders.length === 0) return;
    const normalized = newHeaders.map(h => h.toLowerCase());
    const checkboxes = document.querySelectorAll(
        '#metadata-group-container input[type="checkbox"]'
    );
    checkboxes.forEach(cb => {
        const colName = cb.value.trim().toLowerCase();
        if (normalized.includes(colName)) {
            cb.checked = true;
        }
    });
}

/**
 * Handle adding ELBS report columns
 */
document.getElementById('addELBSBtn').addEventListener('click', function () {
    const button = this;
    fetch('/get-column-names')
        .then(response => response.json())
        .then(data => {
            const table = document.getElementById('metadata-table');
            const headerRow = table.querySelector('thead tr');
            const rows = table.querySelectorAll('tbody tr');
            // Render column infos from dictionary
            data.columnsInfo.forEach(columnInfo => {
                const { ColumnName: columnName, ColumnType: columnType } = columnInfo;
                const newHeader = document.createElement('th');
                newHeader.textContent = columnName;
                newHeader.style.fontWeight = 'normal';
                headerRow.insertBefore(newHeader, headerRow.lastElementChild);
                makeColumnResizable(newHeader, table);
                rows.forEach(row => {
                    const newCell = document.createElement('td');
                    let input;
                    // Decide on input
                    if (columnType == "bool") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        ['Yes', 'No'].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                            applySelectColor(input);
                        });
                        applySelectColor(input);
                    } else if (columnType == "purpose") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        ['Screening', 'Therapy decision aid', 'MRD', 'Relapse',
                            'Clinical study', 'Basic Research'].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                        applySelectColor(input);
                    }
                    else if (columnType == "assay") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        applySelectColor(input);
                        input.appendChild(defaultOption);
                        ['DNA-Sequencing - Short reads (e.g. Illumina)', 'DNA-Sequencing - Long reads (e.g. Nanopore)',
                            'PCR', 'Epigenetics - targeted','Epigenetics - genome-wide', 'RNA-Sequencing',
                        ].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                           // input.required = true; // Optional: Make selection required
                    }
                    else if (columnType == "patho") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        applySelectColor(input);
                        ['GX', 'G1', 'G2', 'G3', 'G4'].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                           // input.required = true; // Optional: Make selection required
                    }
                    else if (columnType == "stage") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        applySelectColor(input);
                        ['I', 'II', 'III', 'IV', 'Other'].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                           // input.required = true; // Optional: Make selection required
                    }
                    else if (columnType == "status") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        applySelectColor(input);
                        ['Diagnosed', 'Healthy', 'R0', 'R1', 'Relapsed'].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                           // input.required = true; // Optional: Make selection required
                    }
                    else if (columnType == "opt") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        applySelectColor(input);
                        ['Yes, OPT OUT', 'No, information is desired.'].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                    }
                    else if (columnType == "equivoc") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        applySelectColor(input);
                        ['corresponding tissue testing','liquid re-biopsy', 'both tissue testing and liquid re-biopsy'
                        ].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                           // input.required = true; // Optional: Make selection required
                    }
                    else if (columnType == "germline") {
                        input = document.createElement('select');
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Choose';
                        input.appendChild(defaultOption);
                        applySelectColor(input);
                        ['genetic counselling','germline testing', 'both counselling and germline testing'
                        ].forEach(optionText => {
                            const option = document.createElement('option');
                            option.value = optionText.toLowerCase();
                            option.textContent = optionText;
                            input.appendChild(option);
                        });
                           // input.required = true; // Optional: Make selection required
                    }
                    else {
                        input = document.createElement('input');
                        input.type = 'text';
                    }
                    input.name = `custom_${columnName.toLowerCase().replace(/\s+/g, '_')}[]`;
                    input.className = 'form-control form-control-sm';
                    newCell.appendChild(input);
                    row.insertBefore(newCell, row.lastElementChild);
                });
            });
            // Change button color to green and disable it
            button.style.backgroundColor = 'green';
            button.style.color = 'white';
            button.textContent = 'Columns Added';
            button.disabled = true;
        })
        .catch(error => console.error('Error fetching column names:', error));
});

// Function to apply gray color on select /black if already selected value
function applySelectColor(select) {
  function updateColor() {
    select.style.color = select.value ? '#000000' : '#c0c0c0';
  }
  updateColor();
  select.addEventListener('change', updateColor);
}

// Function to apply gray (no date chosen)/black (date chosen)
function applyDateColor(input) {
  function updateColor() {
    input.style.color = input.value ? '#000000' : '#c0c0c0';
  }
  updateColor();
  input.addEventListener('input', updateColor);
}

function makeColumnResizable(th, table) {
    const resizer = document.createElement("div");
    resizer.classList.add("resizer");
    th.appendChild(resizer);
    let startX, startWidth, colIndex;
    resizer.addEventListener("mousedown", function(e) {
        e.preventDefault();
        startX = e.pageX;
        const parentCell = e.target.parentElement;
        startWidth = parentCell.offsetWidth;
        colIndex = Array.from(parentCell.parentElement.children).indexOf(parentCell);
        document.addEventListener("mousemove", resizeColumn);
        document.addEventListener("mouseup", stopResize);
    });

    function resizeColumn(e) {
        const newWidth = startWidth + (e.pageX - startX);
        table.querySelectorAll("tr").forEach(row => {
            const cell = row.children[colIndex];
            if (cell) cell.style.width = newWidth + "px";
        });
    }

    function stopResize() {
        document.removeEventListener("mousemove", resizeColumn);
        document.removeEventListener("mouseup", stopResize);
    }
}



// Commented section for ladder type that was removed from metadata table
/**
 ** Ladder options to show based on chosen gel electrophoresis device.
 */
/**
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
*/
/**
 ** Update ladder options displayed to the user automatically when a device is chosen.
 */
/**
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
*/