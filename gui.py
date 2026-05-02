"""
Interface graphique Tkinter de UVSQolor.

Ce fichier gère :
- l'ouverture et la sauvegarde des fichiers ;
- l'affichage de l'image ;
- les menus et les boutons ;
- l'historique Annuler / Rétablir ;
- l'appel aux filtres définis dans filters.py.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from typing import Callable, List, Optional, Union

from PIL import Image, ImageTk

import filters

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # compatibilité avec les anciennes versions de Pillow
    RESAMPLE = Image.LANCZOS


# ---------------------------------------------------------------------------
# Variables globales demandées par le sujet
# ---------------------------------------------------------------------------

fenetre_principale: Optional[tk.Tk] = None
label_image: Optional[tk.Label] = None
label_statut: Optional[tk.Label] = None

image_courante: Optional[Image.Image] = None
image_tk: Optional[ImageTk.PhotoImage] = None

historique: List[Image.Image] = []
indice_historique: int = -1

# Taille maximale utilisée uniquement pour l'affichage à l'écran.
# L'image sauvegardée garde sa vraie taille.
LARGEUR_AFFICHAGE_MAX = 950
HAUTEUR_AFFICHAGE_MAX = 650


# ---------------------------------------------------------------------------
# Fonctions utilitaires d'interface
# ---------------------------------------------------------------------------


def image_chargee() -> bool:
    """Vérifie qu'une image est chargée."""
    if image_courante is None:
        messagebox.showwarning("UVSQolor", "Chargez d'abord une image.")
        return False
    return True


def rafraichir() -> None:
    """
    Met à jour l'image affichée.

    Cette fonction ne modifie pas l'historique. Elle sert uniquement à afficher
    l'état courant de l'image dans la fenêtre.
    """
    global image_tk

    if label_image is None or label_statut is None:
        return

    if image_courante is None:
        label_image.config(image="", text="Aucune image chargée", width=80, height=25)
        label_statut.config(text="Aucune image")
        return

    image_affichage = image_courante.copy()
    image_affichage.thumbnail((LARGEUR_AFFICHAGE_MAX, HAUTEUR_AFFICHAGE_MAX), RESAMPLE)

    image_tk = ImageTk.PhotoImage(image_affichage)
    label_image.config(image=image_tk, text="", width=0, height=0)
    label_image.image = image_tk

    largeur, hauteur = image_courante.size
    label_statut.config(
        text=f"Image : {largeur} x {hauteur} px    |    Historique : {indice_historique + 1}/{len(historique)}"
    )


def initialiser_historique(image: Image.Image) -> None:
    """Réinitialise l'historique après l'ouverture d'une nouvelle image."""
    global historique, indice_historique

    historique = [image.convert("RGB").copy()]
    indice_historique = 0


def ajouter_historique(image: Image.Image) -> None:
    """
    Ajoute une version à l'historique.

    Si l'utilisateur a fait Annuler puis applique un nouveau filtre, les versions
    futures sont supprimées avant l'ajout de la nouvelle version.
    """
    global historique, indice_historique

    if indice_historique < len(historique) - 1:
        historique = historique[:indice_historique + 1]

    historique.append(image.convert("RGB").copy())
    indice_historique = len(historique) - 1


def definir_image(image: Image.Image, ajouter_dans_historique: bool = True) -> None:
    """Change l'image courante, puis met éventuellement à jour l'historique."""
    global image_courante

    image_courante = image.convert("RGB").copy()

    if ajouter_dans_historique:
        ajouter_historique(image_courante)

    rafraichir()


def definir_image_temporaire(image: Image.Image) -> None:
    """
    Affiche une image de prévisualisation sans modifier l'historique.
    """
    global image_courante

    image_courante = image.convert("RGB").copy()
    rafraichir()


def afficher_erreur(titre: str, erreur: Union[Exception, str]) -> None:
    messagebox.showerror(titre, str(erreur))


def executer_avec_sablier(action: Callable[[], Image.Image]) -> Image.Image:
    """Exécute un traitement en affichant un curseur d'attente."""
    if fenetre_principale is not None:
        fenetre_principale.config(cursor="watch")
        fenetre_principale.update_idletasks()

    try:
        return action()
    finally:
        if fenetre_principale is not None:
            fenetre_principale.config(cursor="")
            fenetre_principale.update_idletasks()


# ---------------------------------------------------------------------------
# Fichier : ouvrir / sauvegarder
# ---------------------------------------------------------------------------


def ouvrir_image() -> None:
    """Ouvre une image depuis le disque."""
    global image_courante

    chemin = filedialog.askopenfilename(
        title="Ouvrir une image",
        filetypes=[
            ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
            ("Tous les fichiers", "*.*"),
        ],
    )

    if not chemin:
        return

    try:
        image = Image.open(chemin).convert("RGB")
    except Exception as erreur:
        afficher_erreur("Erreur d'ouverture", erreur)
        return

    image_courante = image.copy()
    initialiser_historique(image_courante)
    rafraichir()


def sauvegarder_image() -> None:
    """Sauvegarde l'image courante dans un fichier."""
    if not image_chargee():
        return

    assert image_courante is not None

    chemin = filedialog.asksaveasfilename(
        title="Sauvegarder l'image",
        defaultextension=".png",
        filetypes=[
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("BMP", "*.bmp"),
            ("WEBP", "*.webp"),
            ("Tous les fichiers", "*.*"),
        ],
    )

    if not chemin:
        return

    try:
        image_a_sauver = image_courante.convert("RGB")
        image_a_sauver.save(chemin)
        messagebox.showinfo("Sauvegarde", "Image sauvegardée avec succès.")
    except Exception as erreur:
        afficher_erreur("Erreur de sauvegarde", erreur)


# ---------------------------------------------------------------------------
# Historique : Annuler / Rétablir
# ---------------------------------------------------------------------------


def annuler() -> None:
    """Revient à la version précédente de l'image."""
    global image_courante, indice_historique

    if not historique:
        return

    if indice_historique <= 0:
        messagebox.showinfo("Annuler", "Aucune action à annuler.")
        return

    indice_historique -= 1
    image_courante = historique[indice_historique].copy()
    rafraichir()


def retablir() -> None:
    """Revient à la version suivante de l'image après une annulation."""
    global image_courante, indice_historique

    if not historique:
        return

    if indice_historique >= len(historique) - 1:
        messagebox.showinfo("Rétablir", "Aucune action à rétablir.")
        return

    indice_historique += 1
    image_courante = historique[indice_historique].copy()
    rafraichir()


# ---------------------------------------------------------------------------
# Application des filtres
# ---------------------------------------------------------------------------


def appliquer_filtre(filtre: Callable[..., Image.Image], *arguments) -> None:
    """Applique un filtre sans prévisualisation."""
    if not image_chargee():
        return

    assert image_courante is not None

    try:
        resultat = executer_avec_sablier(lambda: filtre(image_courante, *arguments))
    except Exception as erreur:
        afficher_erreur("Erreur pendant le filtre", erreur)
        return

    definir_image(resultat, ajouter_dans_historique=True)


def ouvrir_dialogue_slider(
    titre: str,
    texte: str,
    minimum: float,
    maximum: float,
    valeur_initiale: float,
    resolution: float,
    convertir_valeur: Callable[[float], Union[float, int]],
    filtre: Callable[[Image.Image, Union[float, int]], Image.Image],
) -> None:
    """
    Ouvre une boîte avec un slider et une prévisualisation.

    La prévisualisation part toujours de historique[indice_historique], comme
    demandé dans l'énoncé, afin d'éviter d'appliquer plusieurs fois le même effet
    pendant que l'utilisateur déplace le curseur.
    """
    if not image_chargee():
        return

    assert image_courante is not None

    base = historique[indice_historique].copy()
    dialogue = tk.Toplevel(fenetre_principale)
    dialogue.title(titre)
    dialogue.resizable(False, False)

    tk.Label(dialogue, text=texte).pack(padx=12, pady=(12, 4))

    slider = tk.Scale(
        dialogue,
        from_=minimum,
        to=maximum,
        resolution=resolution,
        orient=tk.HORIZONTAL,
        length=330,
    )
    slider.set(valeur_initiale)
    slider.pack(padx=12, pady=8)

    def previsualiser(_=None) -> None:
        valeur = convertir_valeur(float(slider.get()))
        try:
            resultat = executer_avec_sablier(lambda: filtre(base, valeur))
        except Exception as erreur:
            afficher_erreur("Erreur de prévisualisation", erreur)
            return
        definir_image_temporaire(resultat)

    def valider() -> None:
        if image_courante is not None:
            ajouter_historique(image_courante)
        dialogue.destroy()
        rafraichir()

    def annuler_dialogue() -> None:
        definir_image_temporaire(base)
        dialogue.destroy()

    slider.config(command=previsualiser)

    boutons = tk.Frame(dialogue)
    boutons.pack(pady=(4, 12))
    tk.Button(boutons, text="Appliquer", command=valider, width=12).pack(side=tk.LEFT, padx=6)
    tk.Button(boutons, text="Annuler", command=annuler_dialogue, width=12).pack(side=tk.LEFT, padx=6)

    dialogue.protocol("WM_DELETE_WINDOW", annuler_dialogue)
    previsualiser()


def action_sepia() -> None:
    appliquer_filtre(filters.sepia)


def action_luminosite() -> None:
    ouvrir_dialogue_slider(
        "Luminosité",
        "Valeur ajoutée à chaque composante RGB",
        -255,
        255,
        30,
        1,
        lambda valeur: int(round(valeur)),
        filters.brightness,
    )


def action_contraste() -> None:
    ouvrir_dialogue_slider(
        "Contraste",
        "Contraste autour de la valeur moyenne 128",
        -254,
        254,
        40,
        1,
        lambda valeur: int(round(valeur)),
        filters.contrast,
    )


def action_flou() -> None:
    ouvrir_dialogue_slider(
        "Flou uniforme",
        "Rayon du flou moyen",
        1,
        10,
        1,
        1,
        lambda valeur: int(round(valeur)),
        filters.blur,
    )


def action_nettete() -> None:
    appliquer_filtre(filters.sharpen)


def action_flou_gaussien() -> None:
    ouvrir_dialogue_slider(
        "Flou gaussien",
        "Rayon du flou gaussien",
        1,
        20,
        2,
        1,
        lambda valeur: int(round(valeur)),
        filters.gaussian_blur,
    )


def action_nettete_gaussienne() -> None:
    """Ouvre une boîte de réglage pour la netteté basée sur un flou gaussien."""
    if not image_chargee():
        return

    base = historique[indice_historique].copy()
    dialogue = tk.Toplevel(fenetre_principale)
    dialogue.title("Netteté gaussienne")
    dialogue.resizable(False, False)

    tk.Label(dialogue, text="Rayon du flou gaussien").pack(padx=12, pady=(12, 0))
    slider_rayon = tk.Scale(dialogue, from_=1, to=20, resolution=1, orient=tk.HORIZONTAL, length=340)
    slider_rayon.set(2)
    slider_rayon.pack(padx=12)

    tk.Label(dialogue, text="Intensité de la netteté").pack(padx=12, pady=(8, 0))
    slider_intensite = tk.Scale(dialogue, from_=0.0, to=5.0, resolution=0.1, orient=tk.HORIZONTAL, length=340)
    slider_intensite.set(1.0)
    slider_intensite.pack(padx=12)

    tk.Label(dialogue, text="Seuil anti-bruit").pack(padx=12, pady=(8, 0))
    slider_seuil = tk.Scale(dialogue, from_=0, to=255, resolution=1, orient=tk.HORIZONTAL, length=340)
    slider_seuil.set(0)
    slider_seuil.pack(padx=12)

    def previsualiser(_=None) -> None:
        rayon = int(slider_rayon.get())
        intensite = float(slider_intensite.get())
        seuil = int(slider_seuil.get())

        try:
            resultat = executer_avec_sablier(
                lambda: filters.gaussian_sharpen(base, rayon, intensite, seuil)
            )
        except Exception as erreur:
            afficher_erreur("Erreur de prévisualisation", erreur)
            return

        definir_image_temporaire(resultat)

    def valider() -> None:
        if image_courante is not None:
            ajouter_historique(image_courante)
        dialogue.destroy()
        rafraichir()

    def annuler_dialogue() -> None:
        definir_image_temporaire(base)
        dialogue.destroy()

    slider_rayon.config(command=previsualiser)
    slider_intensite.config(command=previsualiser)
    slider_seuil.config(command=previsualiser)

    boutons = tk.Frame(dialogue)
    boutons.pack(pady=12)
    tk.Button(boutons, text="Appliquer", command=valider, width=12).pack(side=tk.LEFT, padx=6)
    tk.Button(boutons, text="Annuler", command=annuler_dialogue, width=12).pack(side=tk.LEFT, padx=6)

    dialogue.protocol("WM_DELETE_WINDOW", annuler_dialogue)
    previsualiser()


def action_fusion() -> None:
    """Charge une deuxième image et fusionne les deux images pixel par pixel."""
    if not image_chargee():
        return

    assert image_courante is not None

    chemin = filedialog.askopenfilename(
        title="Choisir la deuxième image",
        filetypes=[
            ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
            ("Tous les fichiers", "*.*"),
        ],
    )

    if not chemin:
        return

    try:
        image2 = Image.open(chemin).convert("RGB")
    except Exception as erreur:
        afficher_erreur("Erreur d'ouverture", erreur)
        return

    if image2.size != image_courante.size:
        messagebox.showerror(
            "Fusion impossible",
            "Les deux images doivent avoir la même taille.\n\n"
            f"Image courante : {image_courante.size[0]} x {image_courante.size[1]} px\n"
            f"Deuxième image : {image2.size[0]} x {image2.size[1]} px",
        )
        return

    alpha_pourcentage = simpledialog.askinteger(
        "Fusion",
        "Pourcentage de la deuxième image, entre 0 et 100 :",
        initialvalue=50,
        minvalue=0,
        maxvalue=100,
    )

    if alpha_pourcentage is None:
        return

    alpha = alpha_pourcentage / 100
    appliquer_filtre(filters.blend, image2, alpha)


def action_gris() -> None:
    appliquer_filtre(filters.grayscale)


def action_detection_bords() -> None:
    appliquer_filtre(filters.edge_detection)


# ---------------------------------------------------------------------------
# Menus, boutons et lancement
# ---------------------------------------------------------------------------


def creer_menu() -> None:
    assert fenetre_principale is not None

    barre_menu = tk.Menu(fenetre_principale)

    menu_fichier = tk.Menu(barre_menu, tearoff=0)
    menu_fichier.add_command(label="Ouvrir une image", command=ouvrir_image, accelerator="Ctrl+O")
    menu_fichier.add_command(label="Sauvegarder sous...", command=sauvegarder_image, accelerator="Ctrl+S")
    menu_fichier.add_separator()
    menu_fichier.add_command(label="Quitter", command=fenetre_principale.quit)

    menu_edition = tk.Menu(barre_menu, tearoff=0)
    menu_edition.add_command(label="Annuler", command=annuler, accelerator="Ctrl+Z")
    menu_edition.add_command(label="Rétablir", command=retablir, accelerator="Ctrl+Y")

    menu_filtres = tk.Menu(barre_menu, tearoff=0)
    menu_filtres.add_command(label="Sépia", command=action_sepia)
    menu_filtres.add_command(label="Luminosité", command=action_luminosite)
    menu_filtres.add_command(label="Contraste", command=action_contraste)
    menu_filtres.add_command(label="Flou uniforme", command=action_flou)
    menu_filtres.add_command(label="Netteté simple", command=action_nettete)
    menu_filtres.add_separator()
    menu_filtres.add_command(label="Fusion de deux images", command=action_fusion)
    menu_filtres.add_command(label="Flou gaussien", command=action_flou_gaussien)
    menu_filtres.add_command(label="Netteté gaussienne", command=action_nettete_gaussienne)
    menu_filtres.add_separator()
    menu_filtres.add_command(label="Niveaux de gris (bonus)", command=action_gris)
    menu_filtres.add_command(label="Détection de bords Sobel (bonus)", command=action_detection_bords)

    menu_aide = tk.Menu(barre_menu, tearoff=0)
    menu_aide.add_command(
        label="À propos",
        command=lambda: messagebox.showinfo(
            "À propos",
            "UVSQolor\nProjet de traitement d'image en Python avec Tkinter et Pillow.",
        ),
    )

    barre_menu.add_cascade(label="Fichier", menu=menu_fichier)
    barre_menu.add_cascade(label="Édition", menu=menu_edition)
    barre_menu.add_cascade(label="Filtres", menu=menu_filtres)
    barre_menu.add_cascade(label="Aide", menu=menu_aide)

    fenetre_principale.config(menu=barre_menu)


def creer_barre_boutons() -> tk.Frame:
    assert fenetre_principale is not None

    cadre = tk.Frame(fenetre_principale)
    cadre.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

    boutons = [
        ("Ouvrir", ouvrir_image),
        ("Sauvegarder", sauvegarder_image),
        ("Annuler", annuler),
        ("Rétablir", retablir),
        ("Sépia", action_sepia),
        ("Luminosité", action_luminosite),
        ("Contraste", action_contraste),
        ("Fusion", action_fusion),
        ("Flou gaussien", action_flou_gaussien),
        ("Netteté gaussienne", action_nettete_gaussienne),
    ]

    for texte, commande in boutons:
        tk.Button(cadre, text=texte, command=commande).pack(side=tk.LEFT, padx=3)

    return cadre


def configurer_raccourcis() -> None:
    assert fenetre_principale is not None

    fenetre_principale.bind("<Control-o>", lambda event: ouvrir_image())
    fenetre_principale.bind("<Control-s>", lambda event: sauvegarder_image())
    fenetre_principale.bind("<Control-z>", lambda event: annuler())
    fenetre_principale.bind("<Control-y>", lambda event: retablir())


def run_app() -> None:
    """Lance l'application UVSQolor."""
    global fenetre_principale, label_image, label_statut

    fenetre_principale = tk.Tk()
    fenetre_principale.title("UVSQolor")
    fenetre_principale.geometry("1100x780")
    fenetre_principale.minsize(800, 500)

    creer_menu()
    creer_barre_boutons()
    configurer_raccourcis()

    cadre_image = tk.Frame(fenetre_principale, bg="white", bd=1, relief=tk.SUNKEN)
    cadre_image.pack(expand=True, fill=tk.BOTH, padx=8, pady=4)

    label_image = tk.Label(cadre_image, bg="white", text="Aucune image chargée")
    label_image.pack(expand=True)

    label_statut = tk.Label(fenetre_principale, text="Aucune image", anchor=tk.W)
    label_statut.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=4)

    rafraichir()
    fenetre_principale.mainloop()
