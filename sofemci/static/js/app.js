// static/js/app.js
// 🎯 JAVASCRIPT COMPLET - Reprise exacte de TOUTES vos maquettes

// Configuration globale
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏭 SOFEM-CI Application chargée');
    
    // Initialiser selon la page
    const currentPage = getCurrentPage();
    initializePage(currentPage);
});

// ==========================================
// FONCTIONS UTILITAIRES
// ==========================================

function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('dashboard/direction')) return 'dashboard-direction';
    if (path.includes('dashboard')) return 'dashboard';
    if (path.includes('saisie/extrusion')) return 'saisie-extrusion';
    if (path.includes('saisie/sections')) return 'saisie-sections';
    if (path.includes('historique')) return 'historique';
    if (path.includes('login')) return 'login';
    return 'default';
}

function initializePage(page) {
    switch(page) {
        case 'dashboard':
            initializeDashboard();
            break;
        case 'dashboard-direction':
            initializeDashboardDirection();
            break;
        case 'saisie-extrusion':
            initializeSaisieExtrusion();
            break;
        case 'saisie-sections':
            initializeSaisieSections();
            break;
        case 'historique':
            initializeHistorique();
            break;
        default:
            initializeCommon();
    }
}

function initializeCommon() {
    // Fonctions communes à toutes les pages
    setupNavigation();
    setupAlerts();
}

// ==========================================
// NAVIGATION
// ==========================================

function setupNavigation() {
    // Dropdowns
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('mouseenter', function() {
            this.querySelector('.dropdown-menu').style.display = 'block';
        });
        
        dropdown.addEventListener('mouseleave', function() {
            this.querySelector('.dropdown-menu').style.display = 'none';
        });
    });

    // User dropdown
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        const avatar = userDropdown.querySelector('.user-avatar');
        const menu = userDropdown.querySelector('.dropdown-menu');
        
        avatar.addEventListener('click', function() {
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        });
        
        // Fermer en cliquant ailleurs
        document.addEventListener('click', function(e) {
            if (!userDropdown.contains(e.target)) {
                menu.style.display = 'none';
            }
        });
    }
}

// ==========================================
// DASHBOARD PRINCIPAL - Maquette dashboard_principal
// ==========================================

function initializeDashboard() {
    console.log('📊 Initialisation Dashboard Principal');
    
    // Mise à jour temps réel des données
    updateDashboard();
    setInterval(updateDashboard, 30000); // Toutes les 30 secondes
    
    // Actions rapides
    setupQuickActions();
}

function updateDashboard() {
    if (!window.SOFEMCI || !window.SOFEMCI.urls.apiDashboard) return;
    
    fetch(window.SOFEMCI.urls.apiDashboard)
        .then(response => response.json())
        .then(data => {
            // Mise à jour des métriques - EXACTEMENT comme dans votre maquette
            const prodTotale = document.getElementById('production-totale');
            if (prodTotale) {
                prodTotale.textContent = data.production_totale.toFixed(1);
            }
            
            const machinesActives = document.getElementById('machines-actives');
            if (machinesActives) {
                machinesActives.textContent = data.machines_actives + '/' + (data.machines_total || 28);
            }
            
            // Mise à jour de l'heure
            const lastUpdate = document.getElementById('last-update');
            if (lastUpdate) {
                lastUpdate.textContent = new Date().toLocaleTimeString('fr-FR');
            }
        })
        .catch(error => {
            console.error('Erreur mise à jour dashboard:', error);
        });
}

function setupQuickActions() {
    // Gestion des actions rapides
    const actionBtns = document.querySelectorAll('.action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Animation au clic
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

// ==========================================
// DASHBOARD DIRECTION - Maquette dashboard_direction
// ==========================================

function initializeDashboardDirection() {
    console.log('👑 Initialisation Dashboard Direction');
    
    // Fonctions exécutives
    setupExecutiveFunctions();
}

function setupExecutiveFunctions() {
    // Boutons de rapport exécutif
    const generateReportBtn = document.querySelector('[onclick*="generateExecutiveReport"]');
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showExecutiveLoading('Génération du rapport exécutif...');
            
            setTimeout(() => {
                hideExecutiveLoading();
                alert('📊 Rapport exécutif généré avec succès !');
            }, 3000);
        });
    }
    
    // Autres boutons exécutifs
    setupExecutiveButtons();
}

function setupExecutiveButtons() {
    const buttons = [
        { selector: '[onclick*="openFinancialDashboard"]', message: '💰 Dashboard Financier chargé' },
        { selector: '[onclick*="viewOperationalAlerts"]', message: '🚨 Alertes opérationnelles affichées' },
        { selector: '[onclick*="scheduleReview"]', message: '📅 Révision programmée' },
        { selector: '[onclick*="exportStrategicReport"]', message: '📈 Export stratégique préparé' },
        { selector: '[onclick*="viewPredictions"]', message: '🔮 Prévisions calculées' }
    ];
    
    buttons.forEach(({ selector, message }) => {
        const btn = document.querySelector(selector);
        if (btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                showExecutiveLoading('Traitement en cours...');
                setTimeout(() => {
                    hideExecutiveLoading();
                    alert(message);
                }, 2000);
            });
        }
    });
}

function showExecutiveLoading(message) {
    const loader = document.createElement('div');
    loader.id = 'executive-loader';
    loader.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center;
        z-index: 10000; color: white; font-family: 'Segoe UI', sans-serif;
    `;
    
    loader.innerHTML = `
        <div style="background: white; color: #333; padding: 3rem; border-radius: 20px; text-align: center;">
            <div style="border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 2rem;"></div>
            <h3 style="margin-bottom: 1rem; color: #2c3e50;">${message}</h3>
            <p style="color: #666;">Analyse en cours...</p>
        </div>
    `;
    
    document.body.appendChild(loader);
}

function hideExecutiveLoading() {
    const loader = document.getElementById('executive-loader');
    if (loader) loader.remove();
}

// ==========================================
// SAISIE EXTRUSION - Maquette saisie_extrusion
// ==========================================

function initializeSaisieExtrusion() {
    console.log('🏭 Initialisation Saisie Extrusion');
    
    // Calculs automatiques - EXACTEMENT comme dans votre maquette
    setupExtrusionCalculations();
    
    // Validation du formulaire
    setupExtrusionValidation();
}

function setupExtrusionCalculations() {
    const fields = ['prod_finis', 'prod_semi_finis', 'dechets', 'matiere_premiere', 'nb_machines'];
    
    fields.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.addEventListener('input', updateExtrusionCalculations);
        }
    });
    
    // Calcul initial
    updateExtrusionCalculations();
}

function updateExtrusionCalculations() {
    // Récupération des valeurs - EXACTEMENT comme dans votre maquette
    const prodFinis = parseFloat(document.getElementById('prod_finis')?.value) || 0;
    const prodSemiFinis = parseFloat(document.getElementById('prod_semi_finis')?.value) || 0;
    const dechets = parseFloat(document.getElementById('dechets')?.value) || 0;
    const matierePremiereValue = parseFloat(document.getElementById('matiere_premiere')?.value) || 0;
    const nbMachines = parseInt(document.getElementById('nb_machines')?.value) || 1;
    
    // Calculs - EXACTEMENT comme dans votre maquette
    const totalProduction = prodFinis + prodSemiFinis;
    const rendement = matierePremiereValue > 0 ? ((totalProduction / matierePremiereValue) * 100) : 0;
    const tauxDechet = totalProduction > 0 ? ((dechets / (totalProduction + dechets)) * 100) : 0;
    const prodParMachine = nbMachines > 0 ? (totalProduction / nbMachines) : 0;
    
    // Mise à jour de l'affichage - EXACTEMENT comme dans votre maquette
    const totalProdElement = document.getElementById('total_production');
    if (totalProdElement) totalProdElement.textContent = totalProduction.toFixed(1);
    
    const rendementElement = document.getElementById('rendement');
    if (rendementElement) rendementElement.textContent = rendement.toFixed(1);
    
    const tauxDechetElement = document.getElementById('taux_dechet');
    if (tauxDechetElement) tauxDechetElement.textContent = tauxDechet.toFixed(1);
    
    const prodMachineElement = document.getElementById('prod_par_machine');
    if (prodMachineElement) prodMachineElement.textContent = prodParMachine.toFixed(1);
}

function setupExtrusionValidation() {
    const form = document.getElementById('productionForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (validateExtrusionForm()) {
                if (confirm('Confirmer la validation de cette saisie de production ?')) {
                    // Soumettre le formulaire Django
                    this.submit();
                }
            }
        });
    }
}

function validateExtrusionForm() {
    // Validation personnalisée
    const requiredFields = ['prod_finis', 'prod_semi_finis', 'matiere_premiere'];
    let isValid = true;
    
    requiredFields.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element && (!element.value || parseFloat(element.value) < 0)) {
            showFieldError(element, 'Ce champ est requis et doit être positif');
            isValid = false;
        } else {
            clearFieldError(element);
        }
    });
    
    return isValid;
}

// ==========================================
// SAISIE SECTIONS - Maquette saisie_sections_autres
// ==========================================

function initializeSaisieSections() {
    console.log('🏭 Initialisation Saisie Sections');
    
    // Gestion des onglets - EXACTEMENT comme dans votre maquette
    setupSectionTabs();
    
    // Calculs pour chaque section
    setupSectionCalculations();
    
    // Validation des formulaires
    setupSectionValidation();
}

function setupSectionTabs() {
    const tabs = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Retirer la classe active - EXACTEMENT comme dans votre maquette
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.section-content').forEach(s => s.classList.add('section-hidden'));
            
            // Activer l'onglet cliqué
            this.classList.add('active');
            const section = this.getAttribute('data-section');
            const content = document.getElementById(section);
            if (content) {
                content.classList.remove('section-hidden');
            }
        });
    });
}

function setupSectionCalculations() {
    // Imprimerie
    ['imp_bobines_finies', 'imp_bobines_semi_finies', 'imp_dechets'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updateImprimerieCalculations);
        }
    });
    
    // Soudure
    ['sou_bobines_finies', 'sou_bretelles', 'sou_rema', 'sou_batta', 'sou_dechets'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updateSoudureCalculations);
        }
    });
    
    // Recyclage
    ['rec_broyage', 'rec_bache_noir', 'rec_nb_moulinex'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updateRecyclageCalculations);
        }
    });
    
    // Calculs initiaux
    updateImprimerieCalculations();
    updateSoudureCalculations();
    updateRecyclageCalculations();
}

function updateImprimerieCalculations() {
    const bobinesFinies = parseFloat(document.getElementById('imp_bobines_finies')?.value) || 0;
    const bobinesSemiFinies = parseFloat(document.getElementById('imp_bobines_semi_finies')?.value) || 0;
    const dechets = parseFloat(document.getElementById('imp_dechets')?.value) || 0;
    
    const totalProduction = bobinesFinies + bobinesSemiFinies;
    const tauxDechet = (totalProduction + dechets) > 0 ? ((dechets / (totalProduction + dechets)) * 100) : 0;
    
    const totalProdElement = document.getElementById('imp_total_production');
    if (totalProdElement) totalProdElement.textContent = totalProduction.toFixed(1);
    
    const tauxDechetElement = document.getElementById('imp_taux_dechet');
    if (tauxDechetElement) tauxDechetElement.textContent = tauxDechet.toFixed(1);
}

function updateSoudureCalculations() {
    const bobinesFinies = parseFloat(document.getElementById('sou_bobines_finies')?.value) || 0;
    const bretelles = parseFloat(document.getElementById('sou_bretelles')?.value) || 0;
    const rema = parseFloat(document.getElementById('sou_rema')?.value) || 0;
    const batta = parseFloat(document.getElementById('sou_batta')?.value) || 0;
    const dechets = parseFloat(document.getElementById('sou_dechets')?.value) || 0;
    
    const totalSpecifique = bretelles + rema + batta;
    const totalProduction = bobinesFinies + totalSpecifique;
    const tauxDechet = (totalProduction + dechets) > 0 ? ((dechets / (totalProduction + dechets)) * 100) : 0;
    
    const totalProdElement = document.getElementById('sou_total_production');
    if (totalProdElement) totalProdElement.textContent = totalProduction.toFixed(1);
    
    const totalSpecElement = document.getElementById('sou_total_specifique');
    if (totalSpecElement) totalSpecElement.textContent = totalSpecifique.toFixed(1);
    
    const tauxDechetElement = document.getElementById('sou_taux_dechet');
    if (tauxDechetElement) tauxDechetElement.textContent = tauxDechet.toFixed(1);
}

function updateRecyclageCalculations() {
    const broyage = parseFloat(document.getElementById('rec_broyage')?.value) || 0;
    const bacheNoir = parseFloat(document.getElementById('rec_bache_noir')?.value) || 0;
    const nbMoulinex = parseInt(document.getElementById('rec_nb_moulinex')?.value) || 1;
    
    const totalProduction = broyage + bacheNoir;
    const prodParMoulinex = nbMoulinex > 0 ? (totalProduction / nbMoulinex) : 0;
    const tauxTransformation = broyage > 0 ? ((bacheNoir / broyage) * 100) : 0;
    
    const totalProdElement = document.getElementById('rec_total_production');
    if (totalProdElement) totalProdElement.textContent = totalProduction.toFixed(1);
    
    const prodMoulinexElement = document.getElementById('rec_prod_par_moulinex');
    if (prodMoulinexElement) prodMoulinexElement.textContent = prodParMoulinex.toFixed(1);
    
    const tauxTransformElement = document.getElementById('rec_taux_transformation');
    if (tauxTransformElement) tauxTransformElement.textContent = tauxTransformation.toFixed(1);
}

function setupSectionValidation() {
    // Validation des formulaires par section
    const forms = document.querySelectorAll('.imprimerie-form, .soudure-form, .recyclage-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const sectionName = this.classList[0].replace('-form', '');
            
            if (confirm(`Confirmer la validation de la production ${sectionName} ?`)) {
                // Soumettre via AJAX
                submitSectionForm(this, sectionName);
            }
        });
    });
}

function submitSectionForm(form, section) {
    const formData = new FormData(form);
    const url = getAjaxUrl(section);
    
    if (!url) {
        alert('Erreur: URL de soumission non trouvée');
        return;
    }
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.SOFEMCI.csrf
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            form.reset();
            // Recalculer après reset
            if (section === 'imprimerie') updateImprimerieCalculations();
            if (section === 'soudure') updateSoudureCalculations();
            if (section === 'recyclage') updateRecyclageCalculations();
        } else {
            showAlert('error', 'Erreur dans le formulaire');
            console.error(data.errors);
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showAlert('error', 'Erreur de connexion');
    });
}

function getAjaxUrl(section) {
    const urls = {
        'imprimerie': '/ajax/saisie/imprimerie/',
        'soudure': '/ajax/saisie/soudure/',
        'recyclage': '/ajax/saisie/recyclage/'
    };
    return urls[section];
}

// ==========================================
// HISTORIQUE - Maquette historique_production
// ==========================================

function initializeHistorique() {
    console.log('📋 Initialisation Historique');
    
    // Fonctions de filtrage - EXACTEMENT comme dans votre maquette
    setupHistoriqueFilters();
    
    // Pagination
    setupPagination();
    
    // Tri des colonnes
    setupTableSorting();
    
    // Export
    setupExportFunctions();
}

function setupHistoriqueFilters() {
    const applyBtn = document.querySelector('[onclick*="applyFilters"]');
    if (applyBtn) {
        applyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }
    
    const resetBtn = document.querySelector('[onclick*="resetFilters"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            resetFilters();
        });
    }
}

function applyFilters() {
    const form = document.querySelector('form');
    if (form) {
        showLoading();
        
        // Soumettre le formulaire de filtrage
        setTimeout(() => {
            hideLoading();
            // Le formulaire Django va recharger la page avec les filtres
            form.submit();
        }, 1000);
    }
}

function resetFilters() {
    const form = document.querySelector('form');
    if (form) {
        // Reset des champs
        form.reset();
        
        // Valeurs par défaut
        const moisSelect = document.getElementById('mois');
        if (moisSelect) {
            const currentMonth = new Date().getFullYear() + '-' + String(new Date().getMonth() + 1).padStart(2, '0');
            moisSelect.value = currentMonth;
        }
        
        // Appliquer les filtres resetés
        applyFilters();
    }
}

function setupPagination() {
    const pageButtons = document.querySelectorAll('.page-btn');
    
    pageButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.textContent.includes('‹') || this.textContent.includes('›')) {
                return; // Boutons de navigation
            }
            
            if (!isNaN(this.textContent)) {
                // Retirer classe active
                pageButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                showLoading();
                setTimeout(hideLoading, 500);
            }
        });
    });
}

function setupTableSorting() {
    const headers = document.querySelectorAll('.data-table th');
    
    headers.forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function() {
            const column = this.textContent;
            showAlert('info', `Tri par: ${column}`);
        });
    });
}

function setupExportFunctions() {
    const exportBtns = document.querySelectorAll('[onclick*="export"]');
    
    exportBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const action = this.textContent.toLowerCase();
            showLoading();
            
            setTimeout(() => {
                hideLoading();
                
                if (action.includes('excel')) {
                    showAlert('success', 'Export Excel généré !');
                } else if (action.includes('pdf')) {
                    showAlert('success', 'Rapport PDF généré !');
                } else if (action.includes('imprimer')) {
                    window.print();
                }
            }, 2000);
        });
    });
}

// ==========================================
// FONCTIONS UTILITAIRES
// ==========================================

function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'loader';
    loader.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
        z-index: 9999; color: white; font-family: 'Segoe UI', sans-serif;
    `;
    
    loader.innerHTML = `
        <div style="text-align: center;">
            <div style="border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem;"></div>
            <p>Traitement en cours...</p>
        </div>
    `;
    
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('loader');
    if (loader) loader.remove();
}

function showAlert(type, message) {
    const alertsContainer = document.querySelector('.messages-container') || createAlertsContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Auto-remove après 5 secondes
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function createAlertsContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

function setupAlerts() {
    // Gestion des alertes existantes
    const alerts = document.querySelectorAll('.alert-dismissible');
    
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                this.parentElement.remove();
            });
        }
        
        // Auto-remove après 5 secondes
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
}

function showFieldError(element, message) {
    clearFieldError(element);
    
    element.style.borderColor = '#e74c3c';
    
    const error = document.createElement('div');
    error.className = 'field-error';
    error.style.cssText = 'color: #e74c3c; font-size: 0.875rem; margin-top: 0.25rem;';
    error.textContent = message;
    
    element.parentNode.appendChild(error);
}

function clearFieldError(element) {
    element.style.borderColor = '';
    
    const existingError = element.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// ==========================================
// ANIMATIONS CSS
// ==========================================

const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .fade-show {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .alert-dismissible {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;

document.head.appendChild(style);

// ==========================================
// API CALLS
// ==========================================

function callAPI(endpoint, data = null, method = 'GET') {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.SOFEMCI.csrf
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    return fetch(endpoint, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('API Error:', error);
            showAlert('error', 'Erreur de connexion au serveur');
            throw error;
        });
}

// ==========================================
// AUTO-SAVE (OPTIONNEL)
// ==========================================

function setupAutoSave() {
    // Sauvegarde automatique des brouillons
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                const formId = form.id || 'default-form';
                const fieldName = this.name;
                const value = this.value;
                
                // Sauvegarder dans localStorage
                const draftKey = `sofemci_draft_${formId}`;
                let draft = JSON.parse(localStorage.getItem(draftKey) || '{}');
                draft[fieldName] = value;
                localStorage.setItem(draftKey, JSON.stringify(draft));
                
                console.log('Auto-save:', fieldName, value);
            });
        });
    });
}

// ==========================================
// RACCOURCIS CLAVIER
// ==========================================

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Raccourcis pour la direction
        if (e.ctrlKey && window.SOFEMCI.user.role === 'direction') {
            switch(e.key) {
                case 'r':
                    e.preventDefault();
                    if (typeof generateExecutiveReport === 'function') {
                        generateExecutiveReport();
                    }
                    break;
                case 'd':
                    e.preventDefault();
                    window.location.href = '/dashboard/direction/';
                    break;
            }
        }
        
        // Raccourcis généraux
        if (e.ctrlKey) {
            switch(e.key) {
                case 'h':
                    e.preventDefault();
                    window.location.href = '/historique/';
                    break;
                case 's':
                    e.preventDefault();
                    // Sauvegarder le formulaire actuel
                    const activeForm = document.querySelector('form:focus-within');
                    if (activeForm) {
                        const submitBtn = activeForm.querySelector('button[type="submit"]');
                        if (submitBtn) submitBtn.click();
                    }
                    break;
            }
        }
        
        // Échap pour fermer les modales
        if (e.key === 'Escape') {
            const loader = document.getElementById('loader') || document.getElementById('executive-loader');
            if (loader) loader.remove();
            
            const dropdowns = document.querySelectorAll('.dropdown-menu[style*="block"]');
            dropdowns.forEach(dd => dd.style.display = 'none');
        }
    });
}

// ==========================================
// INITIALISATION FINALE
// ==========================================

// Démarrer les fonctions globales
setupKeyboardShortcuts();
setupAutoSave();

// Logger pour debug
window.SOFEMCI_DEBUG = {
    getCurrentPage,
    updateDashboard,
    updateExtrusionCalculations,
    showAlert,
    callAPI
};

console.log('🎯 SOFEM-CI JavaScript fully loaded and ready!');

// Ajouter un style pour améliorer l'UX
document.documentElement.style.scrollBehavior = 'smooth';