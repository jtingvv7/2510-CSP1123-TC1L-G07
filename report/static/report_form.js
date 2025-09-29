document.addEventListener("DOMContentLoaded", function () {
    console.log("report_form.js loaded");

    const typeSelect = document.getElementById("report_type");
    const reportedIdSelect = document.getElementById("reported_id");
    const targetContainer = document.getElementById("target-container");
    const hiddenReportedId = document.getElementById("hidden_reported_id");

    function loadTargets(type, preId = null) {
        if (!reportedIdSelect) return;

        reportedIdSelect.innerHTML = "<option value=''>-- Select --</option>";

        let apiUrl = "";
        if (type === "product") apiUrl = "/report/api/my_products";
        if (type === "user") apiUrl = "/report/api/my_users";
        if (type === "transaction") apiUrl = "/report/api/my_transactions"; 

        if (apiUrl) {
            fetch(apiUrl)
                .then(res => res.json())
                .then(data => {
                    data.forEach(item => {
                        let opt = document.createElement("option");
                        opt.value = item.id;
                        opt.textContent = item.name || ("#" + item.id);
                        if (preId && String(item.id) === String(preId)) {
                            opt.selected = true;
                        }
                        reportedIdSelect.appendChild(opt);
                    });
                    targetContainer.style.display = "block";
                })
                .catch(err => {
                    console.error("Error fetching data:", err);
                    targetContainer.style.display = "none";
                });
        } else {
            targetContainer.style.display = "none";
        }
    }

    // When user manually chooses type
    if (typeSelect) {
        typeSelect.addEventListener("change", function () {
            if (this.value) {
                loadTargets(this.value);
            } else {
                targetContainer.style.display = "none";
            }
        });
    }

    // If there is a pre-selected type
    if (PRE_TYPE) {
        typeSelect.value = PRE_TYPE;

        if (PRE_ID) {
            // Case 1: direct report with pre_id
            hiddenReportedId.value = PRE_ID;
            hiddenReportedId.setAttribute("name", "reported_id");

            if (reportedIdSelect) {
                reportedIdSelect.removeAttribute("name");
            }
            targetContainer.style.display = "none";

        } else {
            // Case 2: type exists but no pre_id thn load options normally
            if (reportedIdSelect) {
                reportedIdSelect.setAttribute("name", "reported_id");
            }
            hiddenReportedId.removeAttribute("name");
            loadTargets(PRE_TYPE);
        }
    } else {
        // No pre_type thn check if user already selected manually
        if (typeSelect && typeSelect.value) {
            loadTargets(typeSelect.value);
        }
    }
});