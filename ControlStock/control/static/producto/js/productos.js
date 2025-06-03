document.addEventListener("DOMContentLoaded", function () {
    const selectAllCheckbox = document.getElementById("selectAll");
    const rowCheckboxes = document.querySelectorAll(".row-checkbox");
    const bulkDeleteBtn = document.getElementById("bulkDeleteBtn");
    const bulkDeleteForm = document.getElementById("bulkDeleteForm");

    // Marcar/Desmarcar todos
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", function () {
            rowCheckboxes.forEach(chk => chk.checked = this.checked);
            toggleBulkDeleteButton();
        });
    }

    // Al cambiar un checkbox individual
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", toggleBulkDeleteButton);
    });

    function toggleBulkDeleteButton() {
        const anyChecked = Array.from(rowCheckboxes).some(cb => cb.checked);
        bulkDeleteBtn.disabled = !anyChecked;
    }

    // Confirmación antes de eliminar
    if (bulkDeleteForm) {
        bulkDeleteForm.addEventListener("submit", function (e) {
            const selected = Array.from(rowCheckboxes).filter(cb => cb.checked);
            if (selected.length === 0) {
                e.preventDefault();
                return;
            }

            const confirmDelete = confirm(`¿Seguro que deseas eliminar ${selected.length} producto(s)?`);
            if (!confirmDelete) {
                e.preventDefault();
            }
        });
    }

    // Sidebar filtros (si tienes uno con ID "filterSidebar")
    const filterToggle = document.getElementById("openFilterSidebar");
    const filterSidebar = document.getElementById("filterSidebar");

    if (filterToggle && filterSidebar) {
        filterToggle.addEventListener("click", () => {
            filterSidebar.classList.toggle("show");
        });
    }
});
