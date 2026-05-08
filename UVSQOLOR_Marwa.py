import tkinter as tk
from tkinter import Menu, filedialog, Toplevel, messagebox
from PIL import Image, ImageTk
import numpy as np
from scipy.signal import convolve2d


# Déclaration des variables globales

image_originale = None              #Image chargée depuis le fichier (PIL)
image_modifiee = None               #Image sur laquelle on travaille, change a chaque filtre appliqué  (PIL)
photo = None                        #Variable convertie pour afficher sur TKinter 
label_image = None                  #Widget qui affiche l'image (widget d'affichage)

# rafraichir des images

def rafraichir():
    global image_modifiee, label_image, photo

    photo = ImageTk.PhotoImage(image_modifiee)
    label_image.config(image = photo)   #Elle modifie un widget Label existant pour y afficher une image

# Ouvrir un fichier

def ouvrir_image():
    global image_originale, image_modifiee

    chemin = filedialog.askopenfilename() #Elle ouvre une fenêtre système de sélection de fichier et retourne le chemin complet du fichier choisi par l'utilisateur.
    if chemin:
        image_originale = Image.open(chemin)
        image_modifiee = image_originale.copy()  #Ce bloc charge une image depuis le disque dur et prépare deux versions : l'originale et une copie qui sera modifiée.
        rafraichir()

# Annuler un effet

def annuler():
    global image_originale, image_modifiee

    image_modifiee = image_originale.copy()
    rafraichir()
    dialogue_effet.destroy()

# Appliquer un effet

def appliquer():
    global image_originale, image_modifiee

    image_originale = image_modifiee.copy()
    rafraichir()
    dialogue_effet.destroy()

# Effet sepia

def filtre_sepia():
    global image_modifiee

    img = np.array(image_modifiee) #transforme l'image en matrice

    r = img[:, :, 0]                                #extraction chaque canal R, G, B
    g = img[:, :, 1]
    b = img[:, :, 2]

    nouveau_r = 0.393*r + 0.769*g + 0.189*b         #calcul nouvelle couleur à partir des coeff
    nouveau_g = 0.349*r + 0.686*g + 0.168*b
    nouveau_b = 0.272*r + 0.534*g + 0.131*b

    #idée principale : somme R > somme G > somme B

    img[:, :, 0] = np.clip(nouveau_r, 0, 255)        #valeurs comprisent entre [0, 255]
    img[:, :, 1] = np.clip(nouveau_g, 0, 255)
    img[:, :, 2] = np.clip(nouveau_b, 0, 255)

    image_modifiee = Image.fromarray(img.astype(np.uint8))
    rafraichir()


# Filtre Luminosité

def luminosite(valeur_slider):
    global image_originale, image_modifiee

    m = float(valeur_slider)

    gamma = np.log(m) / np.log(0.5)     #calcul de gamma

    img_array = np.array(image_originale).astype(np.float32)

    max_val = 255.0

    img_array = img_array / max_val             # echelle de valeurs [0, 255] devient [0, 1] (pour travailler avec gamma)

    img_array = img_array ** gamma

    img_array = img_array * max_val                 #retour à l'echelle [0, 255]

    img_array = np.clip(img_array, 0, 255)

    image_modifiee = Image.fromarray(img_array.astype(np.uint8))

    rafraichir()

# Callback

def correction_gammma():
    global dialogue_effet

    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Luminosité")
    dialogue_effet.geometry("300x150")
    dialogue_effet.grab_set()
    slider = tk.Scale(dialogue_effet, from_=0.05, to=0.95,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=0.01, digits=2,
                      command=luminosite)
    slider.set(0.50)
    slider.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=appliquer)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annuler)
    bouton_annuler.pack(side=tk.LEFT, padx=10)


# Fonction Contraste

def correction_gamma_pivotee(c, p):
    global image_originale, image_modifiee

    img_array = np.array(image_originale).astype(np.float32)        #transformer en matrice + convertir en float

    img_array = img_array / 255.0       #valeurs entre 0 et 1

    gamma = 2 ** float(c)

    p = np.clip(p, 0.001, 0.999)

    if image_originale:
        for i in range(img_array.shape[0]):         #shape[0] = ligne (hauteur), on parcourt les lignes
            for j in range(img_array.shape[1]):     #[1] = colonnes (largeur), parcourt les col
                for k in range(3): #canaux de couleurs
                    x = img_array[i, j, k]

                    if x  <= p:
                        y = p * (x/p) ** gamma
                        img_array[i,j,k] = y
                    else : 
                        y = 1 - (1-p)*((1-x)/(1-p))**gamma
                        img_array[i,j,k] = y

    img_array = img_array * 255 #valeurs entre  0 à 255
    img_array = np.clip(img_array, 0, 255)
    img_array = Image.fromarray(img_array.astype(np.uint8))
    image_modifiee = img_array #sauvegarder le resultat

    rafraichir() #afficher

    # Callback

def filtre_contraste():
    global dialogue_effet

    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Contraste")
    dialogue_effet.geometry("300x250")
    dialogue_effet.grab_set()
    slider1 = tk.Scale(dialogue_effet, from_=-1.0, to=2.0,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=0.01, digits=2)
    slider1.set(0.0)
    slider1.config(command=lambda x: correction_gamma_pivotee(slider1.get(), slider2.get()))
    slider1_label = tk.Label(dialogue_effet, text = "c :")
    slider1_label.pack()
    slider1.pack(pady=20)
    slider2 = tk.Scale(dialogue_effet, from_=0.001, to=0.999,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=0.01, digits=2)
    slider2.set(0.5)
    slider2.config(command = lambda x: correction_gamma_pivotee(slider1.get(), slider2.get())) #2 sliders = recuperer val manuellement => lambda
    slider2_label = tk.Label(dialogue_effet, text = "p : ")
    slider2_label.pack()
    slider2.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=appliquer)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annuler)
    bouton_annuler.pack(side=tk.LEFT, padx=10)    

    

def flou(valeur):
    global image_modifiee, image_originale

    if image_originale:
        base = image_originale
        noyau_taille = int(valeur)
    if noyau_taille <= 0:
        return
    noyau = np.ones((noyau_taille, noyau_taille), dtype=np.float32) / (noyau_taille*noyau_taille) #converti direct en float32 au lieu de faire astype (float64 puis conv en float32) #qstion d'optimisation
    image_mat = np.array(base).astype(np.float32) #tableau de 0 de mm taille que img_originale (qu'on va remplir avec convolution2d)
    image_modifiee_np = np.zeros_like(image_mat)
    for i in range(3):
        image_modifiee_np[:,:,i] = convolve2d(image_mat[:, :, i], noyau, mode='same', boundary='symm')
        image_modifiee = Image.fromarray(np.clip(image_modifiee_np, 0, 255).astype(np.uint8))
    rafraichir()

# Callbacks
def dial_flou():
    global dialogue_effet

    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Flou uniforme")
    dialogue_effet.geometry("300x150")
    dialogue_effet.grab_set()
    slider = tk.Scale(dialogue_effet, from_=1, to=10,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=1, digits=2,
                      command=flou)
    slider.set(0.50)
    slider.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=appliquer)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annuler)
    bouton_annuler.pack(side=tk.LEFT, padx=10)


def gaussien(valeur):
    global image_originale

    if image_originale:
        base = image_originale
        sigma = float(valeur)
        if sigma <= 0:
            return
        x = np.array([-1, 0, 1])    #pixel gauche, milieu, droit
        gauss = np.exp(-(x **2 )/ 2 * (sigma **2)) / gauss.sum()   #formule loi normale
        noyau = np.zeros(sigma, sigma)

        for ligne in range(sigma):
            for colonne in range(sigma):

                noyau[ligne][colonne] = gauss[ligne] * gauss[colonne]
        
        image_array = np.array(base)
        resultat = np.zeros_like(image_array)
        for i in range(3):
            resultat[:, :, i] = convolve2d(image_array[:, :, i], noyau, mode='same', boundary='symm')
        image_originale = Image.fromarray(np.clip(resultat, 0, 255).astype(np.uint8))
        rafraichir()

def dial_gauss():
    global dialogue_effet

    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Flou gaussien")
    dialogue_effet.geometry("300x150")
    dialogue_effet.grab_set()
    slider = tk.Scale(dialogue_effet, from_=1, to=10,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=1, digits=2,
                      command=flou)
    slider.set(0.50)
    slider.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=appliquer)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annuler)
    bouton_annuler.pack(side=tk.LEFT, padx=10)

# Algorithme de filtre
def  sharp(intensité):
    global image_modifiee, image_originale

    I1 = np.array(image_originale).astype(np.float32) #transformer en numpy
    B = flou()
    I1 = image_originale
    D = I1 - B
    I2 = I1 + (float(intensité)* D) 
    I2 =  np.clip(I2, 0, 255)
    image_modifiee = Image.fromarray(I2.astype(np.uint8)) #retour image PIL
    rafraichir()


# Callbacks
def dial_sharp():
    global dialogue_effet

    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Netteté")
    dialogue_effet.geometry("300x150")
    dialogue_effet.grab_set()
    slider = tk.Scale(dialogue_effet, from_=1, to=10,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=1, digits=2,
                      command=sharp)
    slider.set(0.50)
    slider.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=appliquer)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annuler)
    bouton_annuler.pack(side=tk.LEFT, padx=10)


def fusion_images():
    global image_originale, image_modifiee
    if image_originale:
        path = filedialog.askopenfilename(title="Charger la deuxième image")
        if path:
            img2 = Image.open(path).convert("RGB").resize(image_originale.size)
            fusion = Image.blend(image_originale, img2, alpha=0.5)
            image_originale = fusion
        rafraichir()


fenetre_principale = tk.Tk()
fenetre_principale.geometry("300x300")
fenetre_principale.title("Editeur d'image")

# Création du menu principal
menu = tk.Menu(fenetre_principale)
fenetre_principale.config(menu=menu)
menu_fichier = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Fichier", menu=menu_fichier)
menu_fichier.add_command(label="Ouvrir", command=ouvrir_image)

menu_effets = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Effets", menu=menu_effets)
menu_effets.add_command(label="Netteté", command=dial_sharp)
menu_effets.add_command(label="Flou", command=dial_flou)
menu_effets.add_cascade(label="Contraste", command = filtre_contraste)
menu_effets.add_command(label="Luminosité", command=correction_gammma)
menu_effets.add_command(label="Filtre sepia", command = filtre_sepia)
menu_effets.add_command(label="Fusion", command=fusion_images)
menu_effets.add_command(label="Flou Gaussien", command = dial_gauss)
label_image = tk.Label(fenetre_principale)
label_image.pack()


fenetre_principale.mainloop()
