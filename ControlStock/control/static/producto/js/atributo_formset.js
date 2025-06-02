document.addEventListener('DOMContentLoaded', () => {
    const prefix = 'atributo_set';  // Asegúrate que coincida con tu formset prefix en la vista
    const totalForms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    const container = document.getElementById('atributos-container');
    const addBtn = document.getElementById('add-atributo');
    const deleteBtn = document.getElementById('delete-atributos');
    const selectAll = document.getElementById('selectAllAttributes');

    // Mapeo Atributo → Opciones (llenado dinámico)
    const opcionesMap = window.__atributoOpciones__ || {};  // cargado desde plantilla

    function updateDeleteButton() {
        const anyChecked = Array.from(container.querySelectorAll('.attr-checkbox')).some(cb => cb.checked);
        deleteBtn.disabled = !anyChecked;
        updateSelectAllCheckbox();
    }

    function updateSelectAllCheckbox() {
        const checkboxes = container.querySelectorAll('.attr-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        selectAll.checked = checkboxes.length && allChecked;
    }

    function bindEventsToForm(div) {
        const selAtributo = div.querySelector('.atributo-select');
        const selOpcion = div.querySelector('.opcion-select');
        const cb = div.querySelector('.attr-checkbox');

        selAtributo?.addEventListener('change', () => {
            const id = selAtributo.value;
            selOpcion.innerHTML = '<option value="">Seleccionar...</option>';
            selOpcion.disabled = !id;
            if (id && opcionesMap[id]) {
                opcionesMap[id].forEach(opt => {
                    const el = document.createElement('option');
                    el.value = opt.id;
                    el.textContent = opt.valor;
                    selOpcion.appendChild(el);
                });
            }
        });

        cb?.addEventListener('change', updateDeleteButton);
    }

    function addAtributoForm() {
        const index = parseInt(totalForms.value, 10);
        const div = document.createElement('div');
        div.className = 'atributo-form mb-3 border p-3 position-relative';
        div.innerHTML = `
            <input type="checkbox" class="attr-checkbox form-check-input mb-2">
            <div class="row g-3">
                <div class="col-md-5">
                    <label class="form-label">Atributo</label>
                    <select name="${prefix}-${index}-atributo" class="form-select atributo-select" id="id_${prefix}-${index}-atributo">
                        <option value="">Seleccionar atributo...</option>
                        ${Object.keys(opcionesMap).map(id =>
                            `<option value="${id}">${opcionesMap[id][0]?.atributo_nombre || 'Atributo ' + id}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label">Opción</label>
                    <select name="${prefix}-${index}-opcion" class="form-select opcion-select" id="id_${prefix}-${index}-opcion" disabled>
                        <option value="">Seleccionar...</option>
                    </select>
                </div>
            </div>
            <input type="hidden" name="${prefix}-${index}-id" id="id_${prefix}-${index}-id">
            <input type="checkbox" name="${prefix}-${index}-DELETE" id="id_${prefix}-${index}-DELETE" hidden>
        `;
        container.appendChild(div);
        totalForms.value = index + 1;
        bindEventsToForm(div);
    }

    function deleteSelectedForms() {
        container.querySelectorAll('.attr-checkbox:checked').forEach(cb => {
            const form = cb.closest('.atributo-form');
            form.querySelector(`input[name$="-DELETE"]`).checked = true;
            form.classList.add('d-none');
            cb.checked = false;
        });
        updateDeleteButton();
    }

    selectAll?.addEventListener('change', () => {
        container.querySelectorAll('.attr-checkbox').forEach(cb => {
            cb.checked = selectAll.checked;
        });
        updateDeleteButton();
    });

    addBtn?.addEventListener('click', addAtributoForm);
    deleteBtn?.addEventListener('click', deleteSelectedForms);

    container.querySelectorAll('.atributo-form').forEach(bindEventsToForm);
    updateDeleteButton();
});
