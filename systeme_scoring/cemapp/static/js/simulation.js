document.addEventListener("DOMContentLoaded", function() {
    // Récupération des éléments HTML et des valeurs transmises par Django
    const container = document.querySelector(".simulation-container");
    const incomeRange = document.getElementById("monthlyIncome");
    const loanRange = document.getElementById("loanAmount");
    const termRange = document.getElementById("loanTerm");

    const incomeValue = document.getElementById("incomeValue");
    const loanValue = document.getElementById("loanValue");
    const termValue = document.getElementById("termValue");
    const monthlyPayment = document.getElementById("monthlyPayment");
    const monthlyTermResult = document.getElementById("monthlyTermResult");
    const debtRatio = document.getElementById("debtRatio");
    const totalCost = document.getElementById("totalCost");

    const errorMessage = document.createElement("div");
    errorMessage.className = "error-message";

    // Ajout du message d'erreur dans la section de résultats
    document.querySelector(".result-card").appendChild(errorMessage);

    // Récupération des données depuis les attributs `data-*`
    const interestRate = parseFloat(container.getAttribute("data-interest-rate")) / 100;
    const minTerm = parseInt(container.getAttribute("data-min-term"));
    const maxTerm = parseInt(container.getAttribute("data-max-term"));
    const minAmount = parseFloat(container.getAttribute("data-min-amount"));
    const maxAmount = parseFloat(container.getAttribute("data-max-amount"));

    // Fonction de mise à jour de la simulation
    function updateSimulation() {
        const loanAmount = parseFloat(loanRange.value);
        const loanTerm = parseInt(termRange.value);
        const monthlyIncome = parseFloat(incomeRange.value);

        // Calcul de la mensualité
        const monthlyInterest = interestRate;
        const monthlyPaymentAmount = (loanAmount * (monthlyInterest / (1 - Math.pow(1 + monthlyInterest, -loanTerm)))).toFixed(2);
        const maxAllowedPayment = (monthlyIncome * 0.4).toFixed(2);
        const debtRatioValue = ((monthlyPaymentAmount / monthlyIncome) * 100).toFixed(2);
        const totalCostValue = (monthlyPaymentAmount * loanTerm).toFixed(2);

        // Mise à jour des valeurs affichées
        incomeValue.textContent = `${monthlyIncome.toLocaleString()}`;
        loanValue.textContent = `${loanAmount.toLocaleString()}`;
        termValue.textContent = `${loanTerm}`;
        monthlyTermResult.textContent = `${loanTerm}`;
        monthlyPayment.textContent = `${parseFloat(monthlyPaymentAmount).toLocaleString()} MGA`;
        debtRatio.textContent = `${debtRatioValue}%`;
        totalCost.textContent = `${parseFloat(totalCostValue).toLocaleString()} MGA`;

        // Vérification si la mensualité dépasse 40% du revenu mensuel
        if (parseFloat(monthlyPaymentAmount) > parseFloat(maxAllowedPayment)) {
            // Calcul du montant maximum autorisé pour le prêt
            const maxLoanAmount = ((maxAllowedPayment * (1 - Math.pow(1 + monthlyInterest, -loanTerm))) / monthlyInterest).toFixed(2);

            // Calcul du nombre de mois nécessaires
            let maxLoanTerm = maxTerm;
            for (let term = minTerm; term <= maxTerm; term++) {
                const paymentForTerm = (loanAmount * (monthlyInterest / (1 - Math.pow(1 + monthlyInterest, -term)))).toFixed(2);
                if (parseFloat(paymentForTerm) <= parseFloat(maxAllowedPayment)) {
                    maxLoanTerm = term;
                    break;
                }
            }

            errorMessage.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Avertissement :</strong> Le montant de la mensualité (${parseFloat(monthlyPaymentAmount).toLocaleString()} MGA) 
                dépasse 40% de votre revenu mensuel (${maxAllowedPayment} MGA).<br>
                <strong>Recommandation :</strong> 
                Réduisez le montant à ${parseFloat(maxLoanAmount).toLocaleString()} MGA 
                ou augmentez la durée à ${maxLoanTerm} mois.
            `;
            errorMessage.style.display = "block";

            // Ajout de la classe d'erreur pour le style
            monthlyPayment.classList.add("error");
            debtRatio.classList.add("error");
        } else {
            errorMessage.style.display = "none";
            monthlyPayment.classList.remove("error");
            debtRatio.classList.remove("error");
        }
    }

    // Écouteurs d'événements
    incomeRange.addEventListener("input", updateSimulation);
    loanRange.addEventListener("input", updateSimulation);
    termRange.addEventListener("input", updateSimulation);

    // Initialisation
    updateSimulation();
});