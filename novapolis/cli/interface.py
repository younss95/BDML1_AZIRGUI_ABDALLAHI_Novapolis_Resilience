"""Utilitaires d'interface utilisateur pour le CLI interactif."""
import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def effacer_ecran() -> None:
    """Efface l'écran du terminal."""
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

def afficher_en_tete() -> None:
    """Affiche le bandeau de bienvenue principal."""
    titre = Text("Novapolis", style="bold cyan")
    titre.append(" - Outil d'Analyse du Réseau Urbain", style="white")
    console.print(Panel(titre, expand=False, border_style="cyan"))
    console.print("\n")
    
def afficher_section(titre: str) -> None:
    """Affiche un titre de section mis en évidence."""
    console.print(Panel(titre, style="bold magenta italic", expand=False))
