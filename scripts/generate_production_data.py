import datetime
import random
from decimal import Decimal, getcontext
from django.db import transaction
from django.utils import timezone

# --- AJOUT POUR EXÉCUTION DIRECTE HORS SHELL ---
# Ceci configure l'environnement Django lorsque le script est exécuté directement
import os
import django

from sofemci.models import CustomUser
if __name__ == '__main__':
    # Remplacez 'votre_projet.settings' par le chemin réel de votre settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sofemci.settings') 
    django.setup()
# ---------------------------------------------

# Assurez-vous d'importer vos modèles depuis le bon chemin
from sofemci.models import ProductionExtrusion
from sofemci.models import ZoneExtrusion, Equipe

# Définir la précision pour les calculs en Decimal
# COMMENTÉ: getcontext().prec = 4 car une précision aussi basse peut causer des InvalidOperation
# lorsque des nombres plus grands sont générés (ex: 5000 kg).
# Laisser le contexte par défaut de 28 est plus sûr.

def generate_random_kg(base_max):
    """Génère une valeur en kg aléatoire pour la production."""
    # Correction de l'erreur TypeError: convertir base_max en float temporairement 
    # pour permettre l'utilisation de random.uniform, qui exige des arguments float.
    base_float = float(base_max)
    float_value = random.uniform(base_float * 0.7, base_float * 1.1)
    
    # Correction: Utiliser la conversion en chaîne de caractères (str) pour créer 
    # le Decimal à partir du float, ce qui garantit la précision nécessaire et
    # évite l'erreur InvalidOperation. On arrondit le float d'abord pour le nettoyer.
    rounded_float = round(float_value, 4)
    return Decimal(str(rounded_float)).quantize(Decimal('.01'))

def get_shift_times(date, equipe_index, total_equipes):
    """Calcule l'heure de début et l'heure de fin pour l'équipe en fonction de son index."""
    # Simuler des équipes sur une période de 24h (par exemple, 6h-14h, 14h-22h, 22h-6h)
    
    # Simuler une durée de quart de 8 heures
    shift_duration = 8
    
    # Décalage de l'heure de début basé sur l'index de l'équipe
    # Ex: Équipe 0 commence à 6h, Équipe 1 commence à 14h, Équipe 2 commence à 22h
    # Nous commençons à 6h pour éviter le problème d'heure_fin=0h le jour même.
    start_hour = 6 + (equipe_index * shift_duration)
    end_hour = start_hour + shift_duration
    
    # Gérer le passage à minuit (heure_fin > 24)
    if end_hour >= 24:
        # L'heure de fin sera le jour suivant
        end_date = date + datetime.timedelta(days=1)
        end_hour = end_hour % 24
    else:
        end_date = date

    # Créer les objets datetime complets avec un décalage aléatoire en minutes (0 à 15 min)
    heure_debut = datetime.datetime.combine(date, datetime.time(start_hour % 24, random.randint(0, 15)))
    heure_fin = datetime.datetime.combine(end_date, datetime.time(end_hour, random.randint(0, 15)))
    
    return heure_debut, heure_fin


def run():
    """Fonction principale pour générer un mois de données de production."""
    print("Démarrage de la génération des enregistrements de Production Extrusion...")

    # --- 1. Définition de la période ---
    today = datetime.date.today()
    # Début du mois dernier
    start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1) 
    # Fin du mois dernier
    end_date = today.replace(day=1) - datetime.timedelta(days=1)
    
    print(f"Période de génération: du {start_date} au {end_date}")

    # --- 2. Récupération des objets FK (Foreign Key) ---
    
    # Récupérer l'utilisateur pour lier l'enregistrement
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        user = CustomUser.objects.order_by('id').first()
    if not user:
        print("ERREUR: Aucun utilisateur trouvé. Veuillez créer au moins un utilisateur.")
        return

    # Récupérer la première zone et les équipes disponibles
    zone = ZoneExtrusion.objects.first()
    equipes = list(Equipe.objects.all())

    if not zone or not equipes:
        print("ERREUR: Assurez-vous d'avoir au moins une ZoneExtrusion et des Equipes créées.")
        return

    print(f"Utilisateur créateur: {user.username}")
    print(f"Zone utilisée: {zone.nom}")
    print(f"Nombre d'équipes: {len(equipes)}")
    
    total_equipes = len(equipes)

    # Valeurs de production de base (ajustez ces chiffres à votre réalité)
    BASE_MATIERE_PREMIERE = 5000  # kg de matière première consommée par équipe
    BASE_PRODUCTION_FINIS = 4500  # kg de produits finis attendus

    # --- 3. Boucle de génération des données ---
    current_date = start_date
    total_records = 0

    with transaction.atomic():
        while current_date <= end_date:
            print(f"\n--- Jour: {current_date.strftime('%Y-%m-%d')} ---")
            
            # Créer un enregistrement pour chaque équipe ce jour-là
            for i, equipe in enumerate(equipes):
                
                # --- Calculer les heures de début et de fin ---
                heure_debut, heure_fin = get_shift_times(current_date, i, total_equipes)
                
                # Génération des données réalistes (avec un peu de variation)
                matiere_premiere_kg = generate_random_kg(BASE_MATIERE_PREMIERE)
                
                # Les produits finis sont généralement un peu moins que la matière première (rendement < 100%)
                production_finis_kg = generate_random_kg(BASE_PRODUCTION_FINIS)
                
                # Les semi-finis et les déchets sont des fractions
                production_semi_finis_kg = generate_random_kg(500)
                
                # Calculer les déchets pour obtenir une boucle fermée approximative
                # Déchets = MP - (PF + PS) + Marge d'erreur/perte
                dechets_kg = matiere_premiere_kg - (production_finis_kg + production_semi_finis_kg)
                
                # S'assurer que les déchets ne sont pas négatifs (si c'est le cas, simuler une faible valeur)
                if dechets_kg < 0:
                    dechets_kg = generate_random_kg(100) # Déchets réels faibles
                else:
                    # Ajouter un petit déchet "normal" si le calcul est déjà équilibré
                    dechets_kg += generate_random_kg(50)
                
                dechets_kg = dechets_kg.quantize(Decimal('.01'))

                # --- Ajouter le champ nombre_machines_actives ---
                nombre_machines_actives = random.randint(1, 4) 
                
                # --- Ajouter le champ nombre_machinistes (OBLIGATOIRE) ---
                nombre_machinistes = random.randint(2, 6)
                
                # --- NOUVEAU: Ajouter le champ chef_zone (OBLIGATOIRE) ---
                chef_zone = random.choice([
                    "S. KONE", "M. TRAORE", "J. N'GUESSAN", "A. COULIBALY", "K. KONAN", "Y. KOUASSI"
                ])
                
                # --- NOUVEAU: Ajouter le champ nombre_bobines_kg (OBLIGATOIRE) ---
                # Le poids des bobines produites est généralement très proche de la production finie
                nombre_bobines_kg = generate_random_kg(production_finis_kg * Decimal('1.05')) 
                
                # Création de l'enregistrement
                ProductionExtrusion.objects.create(
                    date_production=current_date,
                    zone=zone,
                    equipe=equipe,
                    heure_debut=heure_debut,
                    heure_fin=heure_fin,
                    chef_zone=chef_zone, # NOUVEAU: Champ obligatoire ajouté
                    matiere_premiere_kg=matiere_premiere_kg,
                    production_finis_kg=production_finis_kg,
                    production_semi_finis_kg=production_semi_finis_kg,
                    dechets_kg=dechets_kg,
                    valide=random.choice([True, False, True, True]), # Simuler quelques enregistrements non validés
                    cree_par=user,
                    nombre_machines_actives=nombre_machines_actives,
                    nombre_machinistes=nombre_machinistes,
                    nombre_bobines_kg=nombre_bobines_kg, # NOUVEAU: Champ obligatoire ajouté
                    # Les champs total_production_kg et rendement_pourcentage seront calculés dans la méthode save() du modèle
                )
                
                total_records += 1
                # CORRECTION: Changement de 'equipe.nom_display' à 'equipe.nom' pour éviter l'AttributeError
                print(f" - Enregistré pour l'Équipe {equipe.nom} ({heure_debut.strftime('%H:%M')} -> {heure_fin.strftime('%H:%M')}, Chef: {chef_zone}): PF={production_finis_kg} kg")


            current_date += datetime.timedelta(days=1)

    print(f"\n✅ Terminé. {total_records} enregistrements de production créés avec succès pour le mois.")

# La fonction run() est appelée si le script est lancé via `runscript` ou s'il est exécuté directement.
if __name__ == '__main__':
    run()