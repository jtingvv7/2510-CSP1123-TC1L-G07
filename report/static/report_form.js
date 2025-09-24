document.addEventListener("DOMContentLoaded", function () {
    console.log("report_form.js loaded");

    const typeSelect = document.getElementById("report_type");
    const reportedIdSelect = document.getElementById("reported_id");
    const targetContainer = document.getElementById("target-container");
    const hiddenReportedId = document.getElementById("hidden_reported_id");

    function loadTargets(type, preId = null) {
        reportedIdSelect.innerHTML = "<option value=''>-- Select --</option>";

        let apiUrl = "";
        if (type === "product") apiUrl = "/report/api/my_products";
        if (type === "user") apiUrl = "/report/api/my_users";
        if (type === "transaction") apiUrl = "/report/api/my_transaction";

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

    // user manually choose type
    typeSelect.addEventListener("change", function () {
        if (this.value) {
            loadTargets(this.value);
        } else {
            targetContainer.style.display = "none";
        }
    });

    // // ✅ 初始化加载
    if (typeSelect && typeSelect.value) {
    loadTargets(typeSelect.value);
    }

    // if have default id
    if (PRE_TYPE) {
        typeSelect.value = PRE_TYPE;

        if (PRE_ID) {
            //if default id exist hide the dropdown menu and direct insert value to a hidden input field
            document.getElementById("reported_id_hidden").value = PRE_ID;
            document.getElementById("reported_id_hidden").setAttribute("name", "reported_id");

            document.getElementById("reported_id_select").removeAttribute("name");
            targetContainer.style.display = "none";

        } else {
            // if not default id, as usual
            document.getElementById("reported_id_select").setAttribute("name", "reported_id");
            document.getElementById("reported_id_hidden").removeAttribute("name");
            loadTargets(PRE_TYPE);
        }
    }
});