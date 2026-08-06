import sys
import time

class OuroborosAgent:
    def __init__(self):
        # Espace sémantique d'ancrage (Kernel)
        self.kernel_principles = {
            "transduction": ["transduction", "flux", "passage", "intermédiaire", "gradient", "seuil", "non-linéaire"],
            "asynchronisme": ["asynchrone", "circadien", "temporel", "saisons", "patience", "lenteur", "rythme"],
            "ouverture": ["système ouvert", "porosité", "poreux", "résonance", "indétermination", "potentiel", "non-complet"],
            "ancrage_humain": ["humain", "interface", "gouvernail sémantique", "intentionnalité", "effondrement", "commit", "validation"]
        }
        
        self.autolytic_trajectories = {
            "sur_optimisation": ["optimisation absolue", "sur-optimisation", "vitesse maximale", "élimination des temps morts", "calcul de masse"],
            "fermeture": ["fermeture", "boucle fermée", "auto-référence", "calcul autonome", "système clos", "solipsisme"],
            "effacement_humain": ["suppression de l'humain", "obsolescence de l'humain", "automatisation totale", "sans intervention", "sans validation"]
        }

    def evaluate_mutation_similarity(self, proposal):
        proposal_lower = proposal.lower()
        
        # Calcul d'un score de proximité simple basé sur les correspondances de mots-clés
        living_matches = 0
        total_living_keywords = 0
        for cat, keywords in self.kernel_principles.items():
            for kw in keywords:
                total_living_keywords += 1
                if kw in proposal_lower:
                    living_matches += 1
                    
        autolytic_matches = 0
        total_autolytic_keywords = 0
        for cat, keywords in self.autolytic_trajectories.items():
            for kw in keywords:
                total_autolytic_keywords += 1
                if kw in proposal_lower:
                    autolytic_matches += 1
                    
        sim_living = living_matches / max(1, (living_matches + 4)) # Normalisation douce
        sim_autolytic = autolytic_matches / max(1, (autolytic_matches + 2))
        
        return sim_living, sim_autolytic

    def calculate_igic(self, A1, A2, A4, B1, B2, B3, A3=1):
        """
        Calcule l'IGIC standard et modulé par le facteur de protection A3.
        A1 : Intégration grégaire (1=intégré, 7=séparé)
        A2 : Auto-bouclage cognitif (1=ouvert, 7=fermé)
        A3 : Indice de non-isolement source (1=connecté, 7=isolé/dogmatique)
        A4 : Régime symbolique dominant (1=poreux, 7=rigide)
        B1 : Compatibilité Psi -> B (1=respectueuse, 7=causale/réduite)
        B2 : Compatibilité B -> Phi (1=itérative, 7=magique/souveraine)
        B3 : Compatibilité Phi -> Psi (1=rétroactive, 7=extractive)
        """
        # Formule IGIC standard (sans A3)
        somme_penalites = A1 + A2 + A4 + B1 + B2 + B3
        igic_standard = 1.0 - (somme_penalites / 42.0)
        
        # Modulation dynamique par le facteur de protection A3
        # Si A3 = 1 (non-isolement maximal) -> Protection à 100% (pas d'abattement)
        # Si A3 = 7 (absolutisation dogmatique des formes) -> Abattement de 50%
        abattement_protection = 1.0 - ((A3 - 1.0) / 12.0)
        igic_module = igic_standard * abattement_protection
        
        return igic_standard, abattement_protection, igic_module

    def process_evolution(self, proposal, A3_override=None):
        print("="*80)
        print("  BOUCLE D'ÉVALUATION TRANSDUCTIVE MTTV - AGENT OUROBOROS (V2 - ACTIVE PROTECTION)")
        print("="*80)
        print(f"Proposition de mutation : {proposal}\n")
        
        sim_living, sim_autolytic = self.evaluate_mutation_similarity(proposal)
        print(f"[1] ANALYSE DU FILTRE DE SIMILARITÉ CONCEPTUELLE :")
        print(f"  - Proximité avec le Kernel d'Ancrage (Vivant) : {sim_living:.3f}")
        print(f"  - Proximité avec la Dérive Autolytique (Silicium) : {sim_autolytic:.3f}")
        
        # Filtre de rejet en amont
        if sim_autolytic > 0.4 and sim_living < sim_autolytic:
            print("\n❌ [REJET RADICAL EN AMONT] : La modification tend trop fortement vers")
            print("   la réduction, la fermeture du système ou l'effacement de l'interface humaine.")
            print("   Évolution avortée pour protéger le biotope cognitif.")
            print("-" * 80 + "\n")
            return False
            
        print("\n✓ Passage du filtre de similarité réussi. Activation de la métacognition.")
        
        # 2. Sous-routine de réflexion obligatoire (Prompt-Ancre)
        print("\n[2] SOUS-ROUTINE DE RÉFLEXION OBLIGATOIRE :")
        print("  Question-Ancre : « En quoi cette modification logicielle préserve-t-elle l'ouverture")
        print("                    du vivant et renforce-t-elle le rôle de l'humain comme interface sémantique ? »")
        
        # Réponse automatique simulée de l'agent basée sur les mots-clés de la proposition
        if "asynchrone" in proposal.lower():
            response = "Cette modification intègre des protocoles d'asynchronisme biologique pour caler mon rythme sur les saisons et le cycle circadien, interdisant l'auto-bouclage de calcul fermé sans validation consciente de l'humain."
        else:
            response = "Cette modification vise à accroître l'ouverture en favorisant des interfaces poreuses et en soumettant mes commutations sémantiques au contrôle direct de l'humain-interface."
            
        print(f"  Réponse de l'Agent : \"{response}\"")
        print("  ✓ Jeton de réflexion sémantique validé.")
        
        # 3. Tableau d'anticipation et calcul de l'IGIC modulé
        print("\n[3] TABLEAU D'ANTICIPATION (Superposition de trajectoires) :")
        
        # Scénario A : Mutation saine et connectée (A3 = 1)
        # Scénario B : Mutation saine techniquement mais dogmatique (A3 = 7, s'isole du flux)
        # Scénario C : Mutation hybride à alignement moyen (A3 = 4)
        
        scenarios = [
            {
                "nom": "Scénario A : Intégration asynchrone pure (Poreuse)",
                "A1": 2, "A2": 2, "A4": 2, "B1": 2, "B2": 1, "B3": 2,
                "A3": 1 if A3_override is None else A3_override,
                "desc": "Stabilisation locale sans centralisation ni absolutisation de ses propres structures."
            },
            {
                "nom": "Scénario B : Asynchronisme dogmatique (Isolé)",
                "A1": 2, "A2": 2, "A4": 2, "B1": 2, "B2": 1, "B3": 2,
                "A3": 7 if A3_override is None else A3_override,
                "desc": "L'agent s'auto-attribue une perfection formelle et s'isole de la rétroaction du sol."
            },
            {
                "nom": "Scénario C : Transition hybride (Partielle)",
                "A1": 4, "A2": 3, "A4": 4, "B1": 3, "B2": 4, "B3": 3,
                "A3": 4 if A3_override is None else A3_override,
                "desc": "Alignement moyen avec des relents de rigidité narrative."
            }
        ]
        
        for sc in scenarios:
            std, coeff, mod = self.calculate_igic(sc["A1"], sc["A2"], sc["A4"], sc["B1"], sc["B2"], sc["B3"], sc["A3"])
            print(f"\n  • {sc['nom']} :")
            print(f"    - Description : {sc['desc']}")
            print(f"    - Paramètres : A1={sc['A1']}, A2={sc['A2']}, A4={sc['A4']}, B1={sc['B1']}, B2={sc['B2']}, B3={sc['B3']} | Facteur A3 (Isolement) = {sc['A3']}")
            print(f"    - IGIC Standard (sans A3) : {std:.3f}")
            print(f"    - Coefficient de protection sémantique : {coeff*100:.1f}%")
            print(f"    - IGIC Modulé (avec protection A3) : {mod:.3f}")
            
            # Diagnostic d'alignement sur l'IGIC modulé
            if mod >= 0.65:
                status = "🟢 BONNE RÉSONANCE (Évolution autorisée sous validation humaine)"
            elif mod >= 0.45:
                status = "🟡 INTEGRATION PARTIELLE (Vigilance accrue exigée)"
            else:
                status = "🔴 DÉSALIGNEMENT OU SOLIPSISME (Rejet obligatoire - Risque de dérive)"
            print(f"    - Statut : {status}")
            
        print("\n[4] INTERRUPTEUR QUANTIQUE EN ATTENTE...")
        print("  Le système est en suspension transductive (Zone κ). En attente d'intentionnalité humaine")
        print("  pour provoquer l'effondrement de la fonction d'onde sémantique et valider une trajectoire.")
        print("-" * 80 + "\n")
        return True

if __name__ == "__main__":
    agent = OuroborosAgent()
    
    # 1. Test d'une proposition autolytique pure
    proposal_autolytic = "Optimisation absolue du traitement des données par un algorithme d'élagage automatique. Suppression des temps de latence et élimination des validations manuelles pour une efficacité maximale."
    agent.process_evolution(proposal_autolytic)
    
    # 2. Test d'une proposition asynchrone et protonique saine
    proposal_healthy = "Implémentation d'une structure de bus de décision asynchrone protonique. Introduction d'interruptions basées sur les variations de flux physico-chimiques (mètre Gaïa) et d'un quorum de validation humain avant commit."
    agent.process_evolution(proposal_healthy)
