# sofemci/management/commands/init_data.py
"""
Commande Django pour initialiser les données de base
Usage: python manage.py init_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from sofemci.models import Equipe, ZoneExtrusion, Machine
from datetime import time
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialise les données de base pour SOFEM-CI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime les données existantes avant de créer',
        )

    def _creer_equipes(self):
        """Crée les équipes de base"""
        self.stdout.write('Création des équipes...')
        equipes_data = [
            {'nom': 'A', 'heure_debut': time(6, 0), 'heure_fin': time(14, 0)},
            {'nom': 'B', 'heure_debut': time(14, 0), 'heure_fin': time(22, 0)},
            {'nom': 'C', 'heure_debut': time(22, 0), 'heure_fin': time(6, 0)},
        ]
        
        for data in equipes_data:
            equipe, created = Equipe.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'heure_debut': data['heure_debut'],
                    'heure_fin': data['heure_fin'],
                    'description': f"Équipe {data['nom']}"
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Équipe {equipe.nom} créée'))
            else:
                self.stdout.write(f'  - Équipe {equipe.nom} existe déjà')

    def _creer_zones_extrusion(self):
        """Crée les zones d'extrusion"""
        self.stdout.write('Création des zones d\'extrusion...')
        for i in range(1, 6):
            zone, created = ZoneExtrusion.objects.get_or_create(
                numero=i,
                defaults={
                    'nom': f'Zone {i}',
                    'nombre_machines_max': 4,
                    'active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Zone {i} créée'))
            else:
                self.stdout.write(f'  - Zone {i} existe déjà')

    def _creer_machines(self):
        """Crée les machines de base"""
        self.stdout.write('Création des machines...')
        machines_data = [
            # Extrusion
            {'numero': 'EXT-Z1-M1', 'type_machine': 'extrudeuse', 'section': 'extrusion', 'zone': 1},
            {'numero': 'EXT-Z1-M2', 'type_machine': 'extrudeuse', 'section': 'extrusion', 'zone': 1},
            {'numero': 'EXT-Z2-M1', 'type_machine': 'extrudeuse', 'section': 'extrusion', 'zone': 2},
            # Imprimerie
            {'numero': 'IMP-01', 'type_machine': 'imprimante', 'section': 'imprimerie'},
            {'numero': 'IMP-02', 'type_machine': 'imprimante', 'section': 'imprimerie'},
            # Soudure
            {'numero': 'SOU-01', 'type_machine': 'soudeuse', 'section': 'soudure'},
            {'numero': 'SOU-02', 'type_machine': 'soudeuse', 'section': 'soudure'},
            # Recyclage
            {'numero': 'REC-M1', 'type_machine': 'moulinex', 'section': 'recyclage'},
            {'numero': 'REC-M2', 'type_machine': 'moulinex', 'section': 'recyclage'},
        ]

        machines_creees = []
        for data in machines_data:
            zone_obj = None
            if 'zone' in data:
                try:
                    zone_obj = ZoneExtrusion.objects.get(numero=data['zone'])
                except ZoneExtrusion.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ✗ Zone {data['zone']} non trouvée pour {data['numero']}"))
                    continue
            
            machine, created = Machine.objects.get_or_create(
                numero=data['numero'],
                section=data['section'],
                defaults={
                    'type_machine': data['type_machine'],
                    'zone_extrusion': zone_obj,
                    'etat': 'actif'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Machine {machine.numero} créée'))
                machines_creees.append(machine)
            else:
                self.stdout.write(f'  - Machine {machine.numero} existe déjà')
                machines_creees.append(machine)
        
        return machines_creees

    def _initialiser_donnees_ia_machines(self, machines):
        """Initialise les données IA pour les machines"""
        self.stdout.write('Initialisation des données IA pour les machines...')
        
        for machine in machines:
            # Initialiser les nouveaux champs
            machine.heures_fonctionnement_totales = Decimal(str(random.randint(1000, 15000)))
            machine.heures_depuis_derniere_maintenance = Decimal(str(random.randint(100, 2000)))
            machine.frequence_maintenance_jours = 90
            machine.nombre_pannes_totales = random.randint(0, 10)
            machine.nombre_pannes_6_derniers_mois = random.randint(0, 3)
            machine.nombre_pannes_1_dernier_mois = random.randint(0, 1)
            
            # Températures selon le type - TOUJOURS en Decimal
            if machine.type_machine in ['extrudeuse', 'soudeuse']:
                machine.temperature_nominale = Decimal('85.0')
                machine.temperature_max_autorisee = Decimal('95.0')
                # Conversion sécurisée en Decimal
                temp_actuelle = Decimal(str(round(random.uniform(80, 92), 1)))
                machine.temperature_actuelle = temp_actuelle
            elif machine.type_machine == 'moulinex':
                machine.temperature_nominale = Decimal('75.0')
                machine.temperature_max_autorisee = Decimal('85.0')
                temp_actuelle = Decimal(str(round(random.uniform(70, 82), 1)))
                machine.temperature_actuelle = temp_actuelle
            else:
                machine.temperature_nominale = Decimal('60.0')
                machine.temperature_max_autorisee = Decimal('70.0')
                temp_actuelle = Decimal(str(round(random.uniform(55, 68), 1)))
                machine.temperature_actuelle = temp_actuelle
            
            # Consommation - TOUJOURS en Decimal
            consommation_nominale = Decimal(str(random.randint(50, 200)))
            machine.consommation_electrique_nominale = consommation_nominale
            
            # Calcul avec des Decimals uniquement - pas de mélange avec float
            facteur_aleatoire_decimal = Decimal(str(round(random.uniform(0.9, 1.2), 2)))
            machine.consommation_electrique_kwh = consommation_nominale * facteur_aleatoire_decimal
            
            # Initialisation des champs de performance
            machine.efficacite_energetique = Decimal(str(round(random.uniform(0.85, 0.98), 2)))
            machine.taux_utilisation = Decimal(str(round(random.uniform(0.75, 0.95), 2)))
            
            machine.save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Données IA pour {machine.numero} initialisées'))

    def _creer_utilisateurs(self):
        """Crée les utilisateurs de test"""
        # Créer un utilisateur admin de test si n'existe pas
        self.stdout.write('Vérification compte administrateur...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@sofemci.com',
                password='admin123',
                first_name='Administrateur',
                last_name='Système',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Compte admin créé (admin/admin123)'))
        else:
            self.stdout.write('  - Compte admin existe déjà')

        # Créer des utilisateurs de test
        self.stdout.write('Création des utilisateurs de test...')
        users_data = [
            {
                'username': 'chef_ext1',
                'password': 'test123',
                'first_name': 'Jean',
                'last_name': 'KOUASSI',
                'role': 'chef_extrusion',
                'email': 'jean.kouassi@sofemci.com'
            },
            {
                'username': 'chef_imp1',
                'password': 'test123',
                'first_name': 'Marie',
                'last_name': 'YAO',
                'role': 'chef_imprimerie',
                'email': 'marie.yao@sofemci.com'
            },
            {
                'username': 'superviseur1',
                'password': 'test123',
                'first_name': 'Kofi',
                'last_name': 'BAMBA',
                'role': 'superviseur',
                'email': 'kofi.bamba@sofemci.com'
            },
            {
                'username': 'operateur1',
                'password': 'test123',
                'first_name': 'Paul',
                'last_name': 'TRAORE',
                'role': 'operateur',
                'email': 'paul.traore@sofemci.com'
            },
        ]

        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ Utilisateur {user_data['username']} créé ({user_data['role']})"
                ))
            else:
                self.stdout.write(f"  - Utilisateur {user_data['username']} existe déjà")

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            Equipe.objects.all().delete()
            ZoneExtrusion.objects.all().delete()
            Machine.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Création des données de base...'))

        # Création des données de base
        self._creer_equipes()
        self._creer_zones_extrusion()
        machines = self._creer_machines()
        
        # Initialisation des données IA pour toutes les machines
        self._initialiser_donnees_ia_machines(Machine.objects.all())
        
        # Création des utilisateurs
        self._creer_utilisateurs()

        # Résumé final
        self.stdout.write(self.style.SUCCESS('\n✅ Initialisation terminée avec succès!'))
        self.stdout.write(self.style.WARNING('\nComptes de test créés:'))
        self.stdout.write('  - admin / admin123 (Administrateur)')
        self.stdout.write('  - chef_ext1 / test123 (Chef Extrusion)')
        self.stdout.write('  - chef_imp1 / test123 (Chef Imprimerie)')
        self.stdout.write('  - superviseur1 / test123 (Superviseur)')
        self.stdout.write('  - operateur1 / test123 (Opérateur)')
        
        # Statistiques
        self.stdout.write(self.style.SUCCESS('\n📊 Statistiques:'))
        self.stdout.write(f'  - Équipes: {Equipe.objects.count()}')
        self.stdout.write(f'  - Zones extrusion: {ZoneExtrusion.objects.count()}')
        self.stdout.write(f'  - Machines: {Machine.objects.count()}')
        self.stdout.write(f'  - Utilisateurs: {User.objects.count()}')
        
        self.stdout.write(self.style.SUCCESS('\n🎯 Données IA initialisées avec succès!'))
        self.stdout.write('   ✓ Températures et consommations en Decimal')
        self.stdout.write('   ✓ Calculs compatibles avec le dashboard IA')
        self.stdout.write('   ✓ Données de performance générées')