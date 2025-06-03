let montantMin = 0,
    montantMax = 0,
    tauxInteret = 0;

// Fonction pour initialiser les événements du modal
function initModalEvents() {
    // Recherche dynamique pour les clients (version modal)
    document.getElementById('modalClientSearch') ? .addEventListener('input', function() {
        const searchQuery = this.value.toLowerCase();
        const clientOptions = document.getElementById('modalClient').options;

        for (let i = 0; i < clientOptions.length; i++) {
            const option = clientOptions[i];
            const text = option.textContent.toLowerCase();
            option.style.display = text.includes(searchQuery) ? '' : 'none';
        }
    });

    // Charger les sous-types de crédit (version modal)
    document.getElementById('modalTypeCredit') ? .addEventListener('change', function() {
        const typeCreditId = this.value;
        const sousTypeSelect = document.getElementById('modalSousTypeCredit');

        // Réinitialiser le champ des sous-types
        sousTypeSelect.innerHTML = '<option value="" selected disabled>Chargement...</option>';
        sousTypeSelect.disabled = true;

        fetch(`/api/sous-types-credit/${typeCreditId}/`)
            .then(response => response.json())
            .then(data => {
                sousTypeSelect.innerHTML = '<option value="" selected disabled>-- Sélectionner un sous-type de crédit --</option>';
                data.forEach(sousType => {
                    sousTypeSelect.innerHTML += `<option value="${sousType.id}" data-min="${sousType.montant_min}" data-max="${sousType.montant_max}" data-taux="${sousType.taux_interet}">${sousType.nom}</option>`;
                });
                sousTypeSelect.disabled = false;
            });
    });

    // Mettre à jour les limites de montant (version modal)
    document.getElementById('modalSousTypeCredit') ? .addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        montantMin = parseFloat(selectedOption.dataset.min);
        montantMax = parseFloat(selectedOption.dataset.max);
        tauxInteret = parseFloat(selectedOption.dataset.taux);
        document.getElementById('modalCreditLimits').textContent = `Montant min: ${montantMin} - Montant max: ${montantMax}`;
    });

    // Validation du montant total (version modal)
    document.getElementById('modalMontantTotal') ? .addEventListener('input', function() {
        const montantTotal = parseFloat(this.value);

        if (montantTotal < montantMin || montantTotal > montantMax) {
            this.setCustomValidity(`Le montant doit être entre ${montantMin} et ${montantMax}`);
        } else {
            this.setCustomValidity('');
        }
    });
}

// Initialisation des événements pour la page normale
document.addEventListener('DOMContentLoaded', function() {
    // Recherche dynamique pour les clients (page normale)
    document.getElementById('clientSearch') ? .addEventListener('input', function() {
        const searchQuery = this.value.toLowerCase();
        const clientOptions = document.getElementById('client').options;

        for (let i = 0; i < clientOptions.length; i++) {
            const option = clientOptions[i];
            const text = option.textContent.toLowerCase();
            option.style.display = text.includes(searchQuery) ? '' : 'none';
        }
    });

    // Charger les sous-types de crédit (page normale)
    document.getElementById('type_credit') ? .addEventListener('change', function() {
        const typeCreditId = this.value;
        const sousTypeSelect = document.getElementById('sous_type_credit');

        sousTypeSelect.innerHTML = '<option value="" selected disabled>Chargement...</option>';
        sousTypeSelect.disabled = true;

        fetch(`/api/sous-types-credit/${typeCreditId}/`)
            .then(response => response.json())
            .then(data => {
                sousTypeSelect.innerHTML = '<option value="" selected disabled>-- Sélectionner un sous-type de crédit --</option>';
                data.forEach(sousType => {
                    sousTypeSelect.innerHTML += `<option value="${sousType.id}" data-min="${sousType.montant_min}" data-max="${sousType.montant_max}" data-taux="${sousType.taux_interet}">${sousType.nom}</option>`;
                });
                sousTypeSelect.disabled = false;
            });
    });

    // Mettre à jour les limites de montant (page normale)
    document.getElementById('sous_type_credit') ? .addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        montantMin = parseFloat(selectedOption.dataset.min);
        montantMax = parseFloat(selectedOption.dataset.max);
        tauxInteret = parseFloat(selectedOption.dataset.taux);
        document.getElementById('credit_limits').textContent = `Montant min: ${montantMin} - Montant max: ${montantMax}`;
    });

    // Validation du montant total (page normale)
    document.getElementById('montant_total') ? .addEventListener('input', function() {
        const montantTotal = parseFloat(this.value);

        if (montantTotal < montantMin || montantTotal > montantMax) {
            this.setCustomValidity(`Le montant doit être entre ${montantMin} et ${montantMax}`);
        } else {
            this.setCustomValidity('');
        }
    });
});

// Initialiser les événements quand le modal s'ouvre
document.getElementById('addDemandeButton') ? .addEventListener('click', function() {
    setTimeout(initModalEvents, 50); // Petit délai pour s'assurer que le modal est chargé
});