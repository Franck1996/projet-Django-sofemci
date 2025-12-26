# sofemci/management/commands/generate_test_production.py
"""
Génère des données de production de test pour démonstration
Usage: python manage.py generate_test_production --days 30
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
from decimal import Decimal
import random

from sofemci.models import (
    ProductionExtrusion, ProductionImprimerie, 
    ProductionSoudure, ProductionRecyclage,
    Equipe, ZoneExtrusion
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Génère des données de production de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours de production à générer',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime les productions existantes avant de générer',
        )

    def handle(self, *args, **options):
        days = options['days']
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des productions existantes...'))
            ProductionExtrusion.objects.all().delete()
            ProductionImprimerie.objects.all().delete()
            ProductionSoudure.objects.all().delete()
            ProductionRecyclage.objects.all().delete()

        # Récupérer les données nécessaires
        try:
            user = User.objects.filter(role__in=['admin', 'superviseur']).first()
            if not user:
                user = User.objects.create_user(
                    username='test_admin',
                    password='test123',
                    role='admin',
                    first_name='Test',
                    last_name='Admin'
                )
        except:
            self.stdout.write(self.style.ERROR('Créez d\'abord un utilisateur admin'))
            return

        equipes = list(Equipe.objects.all())
        zones = list(ZoneExtrusion.objects.filter(active=True))

        if not equipes:
            self.stdout.write(self.style.ERROR('Aucune équipe trouvée. Exécutez: python manage.py init_data'))
            return

        if not zones:
            self.stdout.write(self.style.ERROR('Aucune zone trouvée. Exécutez: python manage.py init_data'))
            return

        self.stdout.write(self.style.SUCCESS(f'Génération de {days} jours de production...'))

        today = timezone.now().date()
        start_date = today - timedelta(days=days)

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            
            # Produire seulement 85% des jours (simuler arrêts)
            if random.random() > 0.85:
                continue

            self.stdout.write(f'Jour {current_date.strftime("%d/%m/%Y")}...')

            # Production Extrusion (pour chaque zone et équipe actives)
            for zone in zones:
                # Seulement certaines équipes travaillent chaque jour
                active_equipes = random.sample(equipes, k=random.randint(2, 3))
                
                for equipe in active_equipes:
                    matiere_premiere = Decimal(str(random.uniform(800, 1500)))
                    prod_finis = matiere_premiere * Decimal(str(random.uniform(0.65, 0.75)))
                    prod_semi_finis = matiere_premiere * Decimal(str(random.uniform(0.15, 0.25)))
                    dechets = matiere_premiere * Decimal(str(random.uniform(0.02, 0.05)))
                    
                    ProductionExtrusion.objects.create(
                        date_production=current_date,
                        zone=zone,
                        equipe=equipe,
                        heure_debut=equipe.heure_debut,
                        heure_fin=equipe.heure_fin,
                        chef_zone=f'Chef Zone {zone.numero}',
                        matiere_premiere_kg=matiere_premiere,
                        nombre_machines_actives=random.randint(2, 4),
                        nombre_machinistes=random.randint(3, 5),
                        nombre_bobines_kg=prod_finis + prod_semi_finis,
                        production_finis_kg=prod_finis,
                        production_semi_finis_kg=prod_semi_finis,
                        dechets_kg=dechets,
                        cree_par=user,
                        valide=True if random.random() > 0.2 else False,
                        observations='Données de test' if random.random() > 0.7 else ''
                    )

            # Production Imprimerie (1 fois par jour)
            if random.random() > 0.1:  # 90% des jours
                bobines_finies = Decimal(str(random.uniform(500, 900)))
                bobines_semi_finies = Decimal(str(random.uniform(200, 400)))
                dechets_imp = (bobines_finies + bobines_semi_finies) * Decimal(str(random.uniform(0.025, 0.045)))
                
                ProductionImprimerie.objects.create(
                    date_production=current_date,
                    heure_debut=time(14, 0),
                    heure_fin=time(22, 0),
                    nombre_machines_actives=random.randint(4, 8),
                    production_bobines_finies_kg=bobines_finies,
                    production_bobines_semi_finies_kg=bobines_semi_finies,
                    dechets_kg=dechets_imp,
                    cree_par=user,
                    valide=True if random.random() > 0.2 else False
                )

            # Production Soudure (1 fois par jour)
            if random.random() > 0.1:
                bobines_finies_sou = Decimal(str(random.uniform(400, 700)))
                bretelles = Decimal(str(random.uniform(100, 250)))
                rema = Decimal(str(random.uniform(80, 180)))
                batta = Decimal(str(random.uniform(50, 120)))
                total_prod = bobines_finies_sou + bretelles + rema + batta
                dechets_sou = total_prod * Decimal(str(random.uniform(0.03, 0.05)))
                
                ProductionSoudure.objects.create(
                    date_production=current_date,
                    heure_debut=time(14, 0),
                    heure_fin=time(22, 0),
                    nombre_machines_actives=random.randint(3, 6),
                    production_bobines_finies_kg=bobines_finies_sou,
                    production_bretelles_kg=bretelles,
                    production_rema_kg=rema,
                    production_batta_kg=batta,
                    dechets_kg=dechets_sou,
                    cree_par=user,
                    valide=True if random.random() > 0.2 else False
                )

            # Production Recyclage (pour certaines équipes)
            recycling_equipes = random.sample(equipes, k=random.randint(1, 2))
            for equipe in recycling_equipes:
                broyage = Decimal(str(random.uniform(300, 600)))
                bache_noir = broyage * Decimal(str(random.uniform(0.70, 0.85)))
                
                ProductionRecyclage.objects.create(
                    date_production=current_date,
                    equipe=equipe,
                    nombre_moulinex=random.randint(2, 4),
                    production_broyage_kg=broyage,
                    production_bache_noir_kg=bache_noir,
                    cree_par=user,
                    valide=True if random.random() > 0.2 else False
                )

        # Statistiques
        self.stdout.write(self.style.SUCCESS('\n✅ Génération terminée!'))
        self.stdout.write(f'\nStatistiques:')
        self.stdout.write(f'  - Productions Extrusion: {ProductionExtrusion.objects.count()}')
        self.stdout.write(f'  - Productions Imprimerie: {ProductionImprimerie.objects.count()}')
        self.stdout.write(f'  - Productions Soudure: {ProductionSoudure.objects.count()}')
        self.stdout.write(f'  - Productions Recyclage: {ProductionRecyclage.objects.count()}')
        
        total_production = (
            ProductionExtrusion.objects.aggregate(total=models.Sum('total_production_kg'))['total'] or 0
        )
        self.stdout.write(f'  - Production totale: {total_production:.2f} kg')