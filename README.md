#Mon projet
Ceci est mon premier projet GitHub

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from scipy.signal import convolve2d


def filtre_sepia(matrice):
    """Transforme l'image en sépia (teinte vieille photo)"""
    coeffs = np.array([
        [0.393, 0.769, 0.189],  # Rouge
        [0.349, 0.686, 0.168],  # Vert
        [0.272, 0.534, 0.131]   # Bleu
    ])
    resultat = np.dot(matrice.astype(np.float32), coeffs.T) #Prends l'image, transforme-la en nombres décimaux, applique la formule magique aux 3 couleurs de chaque pixel, et stocke le résultat dans resultat"
    resultat = np.clip(resultat, 0, 255)#Si un nombre est en dessous de 0, ramène-le à 0. Si un nombre est au-dessus de 255, ramène-le à 255. Sinon, laisse-le comme il est
    return resultat.astype(np.uint8)# Transforme les nombres décimaux en nombres entiers (0 à 255) et renvoie l'image finie.
#rappel pour comprendre comment j'ai fais les couleurs: [255, 0, 0] = ROUGE pur 🔴,[0, 255, 0] = VERT pur 🟢, [0, 0, 255] = BLEU pur 🔵, [255, 255, 255] = BLANC ⬜,[0, 0, 0] = NOIR 
#"Prends 39% du rouge, 77% du vert, 19% du bleu pour faire le nouveau rouge,(pour array et dot) Parce qu'une image a des milliers de pixels on va pas faire le calcul un np.dot fait le calcul pour tous les pixels en même temps


def luminosite(matrice, gamma):
    normalisee = matrice.astype(np.float32) / 255.0
    resultat = np.power(normalisee, gamma)
    return (resultat * 255).astype(np.uint8)
    #matrice.astype(np.float32) je convertis les valeurs de l’image en nombres décimaux (float)(car à la base, elles sont souvent en entiers entre 0 et 255)/ 255.0 je normalises lesvaleurs pour qu’elles soient entre 0 et 1
    #j' appliques la correction gamma np.power(x, gamma) = x^γ effet selon gamma : gamma < 1 : image plus claire gamma > 1 : image plus sombre
    #remets l’image dans un format classique :resultat * 255 repasses de l’intervalle [0, 1] à [0, 255].astype(np.uint8) reconvertis en entiers (0 à 25format standard pour afficher une imagereturnrenvoies l’image modifiée

def contraste(matrice, m, p=0.5): # fonction sert à modifier le contraste de façon non linéaire
    if m <= 0.05:
        m = 0.05 #Si m est trop petit ou nul ça peut casser les logarithmes plus bas donc impose une valeur minimale de 0.05
    gamma = np.log(m) / np.log(p)  #calcules un gamma personnalisé np.log = logarithme naturel Ce gamma contrôle la courbe de contraste
    normalisee = matrice.astype(np.float32) / 255.0 #conversion en float normalisation entre 0 et 1 prépare l’image pour des calculs mathématiques
    resultat = np.where(
        normalisee <= p,
        p * (normalisee / p) ** gamma,
        1 - (1 - p) * ((1 - normalisee) / (1 - p)) ** gamma
    ) #condition vectorisée, applique une transformation différente selon les pixels. si le pixel est dans les tons sombres / moyens bas 
    #(normalisee / p) → normalise par rapport au pivot gamma = applique la courbe de contraste, p= remet à l’échelle améliore les détails dans les zones sombres
    return (resultat * 255).astype(np.uint8)


def flou(matrice):
    """Applique un flou (moyenne avec les voisins)"""
    kernel = np.ones((3, 3), dtype=np.float32) / 9.0 #crées un filtre (kernel) 3×3 : np.ones((3,3)) → matrice remplie de 1/ 9.0 → chaque valeur devient 1/9 calcule une moyenne des pixels voisins
    resultat = np.zeros_like(matrice, dtype=np.float32)#crées une image vide (même taille que l’originale) pour stocker le résultat
    for i in range(3): #parcours les 3 couleurs de l’image
        resultat[:, :, i] = convolve2d(matrice[:, :, i], kernel, mode='same', boundary='symm')#prends chaque pixel et je calcule une moyenne pondérée de ses voisins,(same): l’image de sortie a la même taille que l’image d’entrée, (sym): gère les bords de l’image, 
    return resultat.astype(np.uint8) #conversion en image classique (0–255)


def netteté(matrice, facteur=1.5): #intensité de la netteté
    floue = flou(matrice) #crées une version floue de l’image
    details = matrice.astype(np.float32) - floue.astype(np.float32) #récupères les détails de l’image, image originale = détails + version floue, détails=originale−floue (ça isole les contours et textures)
    resultat = matrice.astype(np.float32) + facteur * details#renforces les détails, rajoutes les détails à l’image originale, 
    resultat = np.clip(resultat, 0, 255)# évites les dépassements, valeurs < 0 → deviennent 0 et valeurs > 255 → deviennent 255, 
    return resultat.astype(np.uint8) #conversion finale en image classique

# UTILISATION DE L'IA POUR LA PARTIE MATHEMATIQUES !!

class UVSQolor:
    def __init__(self):
        # Création de la fenêtre
        self.fenetre = tk.Tk()
        self.fenetre.title("UVSQolor - Éditeur d'images")
        self.fenetre.geometry("800x600")
        
        # Variables
        self.image_courante = None    # Image sous forme de matrice numpy
        self.photo_tk = None          # Image pour l'affichage Tkinter
        self.canvas = None            # Zone d'affichage
        
        # Historique pour Annuler/Rétablir
        self.historique = []
        self.position = -1
        
        # Fenêtre des réglages
        self.fenetre_reglage = None
        self.image_temp = None        # Image temporaire pour prévisualisation
        
        # Création de l'interface
        self.creer_menu()
        self.creer_canvas()
    
    def creer_menu(self):
        """Crée la barre de menu"""
        barre = tk.Menu(self.fenetre)
        self.fenetre.config(menu=barre)
        
        # Menu FICHIER
        menu_fichier = tk.Menu(barre, tearoff=0)
        barre.add_cascade(label="Fichier", menu=menu_fichier)
        menu_fichier.add_command(label="Ouvrir", command=self.ouvrir)
        menu_fichier.add_command(label="Sauvegarder", command=self.sauvegarder)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.fenetre.quit)
        
        # Menu ÉDITION
        menu_edition = tk.Menu(barre, tearoff=0)
        barre.add_cascade(label="Édition", menu=menu_edition)
        menu_edition.add_command(label="Annuler", command=self.annuler)
        menu_edition.add_command(label="Rétablir", command=self.retablir)
        
        # Menu EFFETS
        menu_effets = tk.Menu(barre, tearoff=0)
        barre.add_cascade(label="Effets", menu=menu_effets)
        menu_effets.add_command(label="Sépia", command=self.appliquer_sepia)
        menu_effets.add_command(label="Luminosité", command=self.ouvrir_luminosite)
        menu_effets.add_command(label="Contraste", command=self.ouvrir_contraste)
        menu_effets.add_separator()
        menu_effets.add_command(label="Flou", command=self.appliquer_flou)
        menu_effets.add_command(label="Netteté", command=self.appliquer_netrete)
    
    def creer_canvas(self):
        """Crée la zone d'affichage"""
        self.canvas = tk.Canvas(self.fenetre, bg='gray')
        self.canvas.pack(expand=True, fill=tk.BOTH)
    
    def afficher(self):
        """Affiche l'image courante"""
        if self.position >= 0:
            matrice = self.historique[self.position]
            image_pil = Image.fromarray(matrice)
            self.photo_tk = ImageTk.PhotoImage(image_pil)
            
            self.canvas.delete("all")
            self.canvas.config(width=image_pil.width, height=image_pil.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_tk)
            
            # Ajuste la taille de la fenêtre
            self.fenetre.geometry(f"{image_pil.width+20}x{image_pil.height+50}")
    
    def ajouter_historique(self, image):
        """Ajoute une image à l'historique"""
        self.historique = self.historique[:self.position + 1]
        self.historique.append(image.copy())
        self.position += 1
        self.afficher()
    
    def ouvrir(self):
        """Ouvre une image"""
        chemin = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if chemin:
            image_pil = Image.open(chemin).convert('RGB')
            matrice = np.array(image_pil)
            self.historique = [matrice]
            self.position = 0
            self.afficher()
    
    def sauvegarder(self):
        """Sauvegarde l'image"""
        if self.position >= 0:
            chemin = filedialog.asksaveasfilename(defaultextension=".png")
            if chemin:
                image_pil = Image.fromarray(self.historique[self.position])
                image_pil.save(chemin)
                messagebox.showinfo("Succès", "Image sauvegardée !")
    
    def annuler(self):
        """Annule la dernière action"""
        if self.position > 0:
            self.position -= 1
            self.afficher()
    
    def retablir(self):
        """Rétablit l'action annulée"""
        if self.position < len(self.historique) - 1:
            self.position += 1
            self.afficher()
    
    # ------------------------------------------------------------------
    # Application des filtres
    # ------------------------------------------------------------------
    
    def appliquer_sepia(self):
        if self.position >= 0:
            nouvelle = filtre_sepia(self.historique[self.position])
            self.ajouter_historique(nouvelle)
    
    def appliquer_flou(self):
        if self.position >= 0:
            nouvelle = flou(self.historique[self.position])
            self.ajouter_historique(nouvelle)
    
    def appliquer_netrete(self):
        if self.position >= 0:
            nouvelle = netteté(self.historique[self.position])
            self.ajouter_historique(nouvelle)
    
    # ------------------------------------------------------------------
    # Filtres avec curseur (Luminosité et Contraste)
    # ------------------------------------------------------------------
    
    def ouvrir_luminosite(self):
        """Ouvre une fenêtre avec un curseur pour la luminosité"""
        if self.position < 0:
            return
        
        self.image_temp = self.historique[self.position].copy()
        
        self.fenetre_reglage = tk.Toplevel(self.fenetre)
        self.fenetre_reglage.title("Luminosité")
        self.fenetre_reglage.geometry("300x150")
        
        tk.Label(self.fenetre_reglage, text="Régler la luminosité :").pack(pady=10)
        
        slider = tk.Scale(self.fenetre_reglage, from_=0.2, to=3.0,
                          orient=tk.HORIZONTAL, length=250,
                          resolution=0.05, digits=2)
        slider.set(1.0)
        slider.pack(pady=10)
        
        def on_change(valeur):
            gamma = float(valeur)
            resultat = luminosite(self.image_temp, gamma)
            self.historique[self.position] = resultat
            self.afficher()
        
        slider.config(command=on_change)
        
        btn_frame = tk.Frame(self.fenetre_reglage)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=self.fermer_reglage).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Annuler", command=self.annuler_reglage).pack(side=tk.LEFT, padx=10)
    
    def ouvrir_contraste(self):
        """Ouvre une fenêtre avec un curseur pour le contraste"""
        if self.position < 0:
            return
        
        self.image_temp = self.historique[self.position].copy()
        
        self.fenetre_reglage = tk.Toplevel(self.fenetre)
        self.fenetre_reglage.title("Contraste")
        self.fenetre_reglage.geometry("300x150")
        
        tk.Label(self.fenetre_reglage, text="Régler le contraste :").pack(pady=10)
        
        slider = tk.Scale(self.fenetre_reglage, from_=0.1, to=0.9,
                          orient=tk.HORIZONTAL, length=250,
                          resolution=0.01, digits=2)
        slider.set(0.5)
        slider.pack(pady=10)
        
        def on_change(valeur):
            m = float(valeur)
            resultat = contraste(self.image_temp, m)
            self.historique[self.position] = resultat
            self.afficher()
        
        slider.config(command=on_change)
        
        btn_frame = tk.Frame(self.fenetre_reglage)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=self.fermer_reglage).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Annuler", command=self.annuler_reglage).pack(side=tk.LEFT, padx=10)
    
    def fermer_reglage(self):
        """Ferme la fenêtre de réglage et garde les changements"""
        if self.fenetre_reglage:
            self.fenetre_reglage.destroy()
            self.fenetre_reglage = None
    
    def annuler_reglage(self):
        """Ferme la fenêtre de réglage et annule les changements"""
        if self.fenetre_reglage and self.position >= 0:
            self.historique[self.position] = self.image_temp
            self.afficher()
            self.fenetre_reglage.destroy()
            self.fenetre_reglage = None
    
    def lancer(self):
        """Lance l'application"""
        self.fenetre.mainloop()


# ==============================================================
# LANCEMENT DU PROGRAMME
# ==============================================================

if __name__ == "__main__":
    app = UVSQolor()
    app.lancer()
