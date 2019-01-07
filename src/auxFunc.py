import cv2 as cv
import numpy as np
import pdb
import os
import re
import random

PATH_TO_INRIA = "../../INRIAPerson"

################################################################################
##                       Funciones de dibujado                                ##
################################################################################

def pintaMI(vim):
    '''
    @brief Función que dada una lista de imágenes las pinta en una misma ventana.
    @param vim Lista de imágenes que queremos pintar
    '''
    imagenes = []
    max_h = 0
    max_w = 0
    for im in vim:
        if im.shape[0]>max_h:
            max_h = im.shape[0]
        if im.shape[1]>max_w:
            max_w = im.shape[1]
    for im in vim:
        if len(im.shape)==2:
            imagenes.append(cv.copyMakeBorder(cv.cvtColor(im,cv.COLOR_GRAY2RGB),top=0,bottom=max_h-im.shape[0],left=0,right=0,borderType= cv.BORDER_CONSTANT, value=[0,0,0]))
        else:
            imagenes.append(cv.copyMakeBorder(im,top=0,bottom=max_h-im.shape[0],left=0,right=0,borderType= cv.BORDER_CONSTANT, value=[0,0,0]))
    concatenada = cv.hconcat(imagenes)
    cv.namedWindow('Imagenes', cv.WINDOW_NORMAL)
    cv.imshow("Imagenes",concatenada)
    cv.waitKey(0)
    cv.destroyAllWindows()

################################################################################
##                          Preprocesamiento                                  ##
################################################################################

def obtainCropLimits(nrows,ncols,window_size=(64,128)):
    '''
    @brief Función que dados el número de filas y columnas de la imagen original
    da los límites de una ventana aleatoria de tamaño window_size
    @param nrows Número de filas de la imagen original
    @param ncols Número de columnas de la imagen original
    @param window_size Tamaño de la ventana que queremos obtener, por defecto es
    de tamaño 64x128
    @return Devuelve las esquinas con valores mínimos y máximo de x e y
    '''
    x0 = random.randint(0,nrows)
    y0 = random.randint(0,ncols)
    while x0+window_size[0]>=ncols or y0+window_size[1]>=nrows:
        x0 = random.randint(0,nrows)
        y0 = random.randint(0,ncols)
    x1 = x0+window_size[0]
    y1 = y0+window_size[1]
    return x0,y0,x1,y1

def obtainNegativeSamples(neg_samples_dir="../../INRIAPerson/Train/neg/",dir_to_save="./cropped_neg/"):
    '''
    @brief Función que dado un directorio con imágenes y un directorio para guardarlas
    obtiene 10 ventanas aleatorias de la misma y las guarda en el directorio correspondiente
    @param neg_samples_dir Directorio que contiene las imágenes
    @param dir_to_save Directorio donde queremos guardar los resultados
    '''
    list_images = os.listdir(neg_samples_dir)
    for img_name in list_images:
        img = cv.imread(neg_samples_dir + img_name,-1)
        img_name_sp = img_name.split(".")[0]
        format = img_name.split(".")[1]
        for i in range(10):
            x_min,y_min,x_max,y_max = obtainCropLimits(img.shape[0],img.shape[1])
            crop = img[y_min:y_max, x_min:x_max]
            cv.imwrite(dir_to_save+img_name_sp+"_c_"+str(i)+"."+format,crop)

def obtainNegatives(neg_samples_dir="../../INRIAPerson/Train/neg/"):
    '''
    @brief Función que dado un directorio con imágenes y un directorio para guardarlas
    obtiene 10 ventanas aleatorias de la misma y las guarda en el directorio correspondiente
    @param neg_samples_dir Directorio que contiene las imágenes
    @param dir_to_save Directorio donde queremos guardar los resultados
    '''
    ret = []
    list_images = os.listdir(neg_samples_dir)
    for img_name in list_images:
        img = cv.imread(neg_samples_dir + img_name,-1)
        img_name_sp = img_name.split(".")[0]
        format = img_name.split(".")[1]
        for i in range(10):
            x_min,y_min,x_max,y_max = obtainCropLimits(img.shape[0],img.shape[1])
            crop = img[y_min:y_max, x_min:x_max]
            ret.append(crop)
    return ret
################################################################################
##                         Funciones de cálculo                               ##
################################################################################

def convoluteWith1DMask(ker,horizontally,im):
    '''
    @brief Se convoluciona una imagen con una mascara 1 dimensional en una sola direccion horizontal
    o vertical.
    @param ker mascara con la que se hace la convolucion
    @param horizontally booleano que define si la convolucion se hace en horizontal o en vertical
    @param im numpy array de enteros sin signo que contiene informacion relativa a una imagen
    @return Devuelve un vector con todas los canales de la imagen convolucionados.
    '''
    # Definimos los nucleos de convolucion
    kerX = kerY = None
    if horizontally:
        # Si convolucionamos por filas el nucleo que no es trivial es kerX
        # Reversed porque sepFilter2D hace correlacion
        kerX = np.array(list(reversed(ker)))
        # Nucleo trivial [...,0,1,0,...]
        kerY = np.array([1])
    else:
        # Analogamente
        # Nucleo trivial [...,0,1,0,...]
        kerX = np.array([1])
        # Si convolucionamos por filas el nucleo que no es trivial es kerY
        # Reversed porque sepFilter2D hace correlacion
        kerY = np.array(list(reversed(ker)))
    if len(im.shape) == 3:      # Para imagenes RGB o LAB
        alto, ancho, profundo = im.shape
        # Se tratan los tres canales por separado
        inputSignals = cv.split(im)
        convolutedSignals = []
        for i in range(profundo):
            inputSignal = inputSignals[i]
            # Se convoluciona las senales R,G y B
            convolutedSignal = cv.sepFilter2D(inputSignal,-1,kerX,kerY)
            convolutedSignals.append(convolutedSignal)
        return convolutedSignals
    else:
        # Para imagenes GRAYSCALE
        return [cv.sepFilter2D(im,-1,kerX,kerY)]

def normaEuclidea(v):
    '''
    @brief Se calcula la norma euclidea de un vector
    @param im numpy array que contiene las coordenadas del vector
    @return Devuelve la norma de un vector
    '''
    return np.linalg.norm(v)

def getGradient(signalsdx,signalsdy):
    '''
    @brief Calcula un gradiente a partir de las derivadas en las direcciones de x de
    todos los canales de una imagen
    @param signalsdx Derivada en la direccion de equis para todos los canales de una
    imagen
    @param signalsdy Derivada en la direccion de i para todos los canales de una
    imagen
    @return Devuelve el gradiente formado por en cada pixel el gradiente de mayor norma de entre todos
    los gradientes de todos los canales
    '''
    n,m = signalsdx[0].shape
    # Contiene el gradiente final
    dx = []
    dy = []
    # Contiene los gradientes de todos los canales de la imagen
    cuadradoX = [gx**2 for gx in signalsdx]
    cuadradoY = [gy**2 for gy in signalsdy]
    for i in range(n):
        for j in range(m):
            normas = []
            for k in range(3):
                xx = cuadradoX[k][i,j]
                yy = cuadradoY[k][i,j]
                normas.append(xx+yy)
            # Verificamos en cada pixel que
            indiceMax = np.argmax(normas, axis=None)
            dx.append(signalsdx[indiceMax][i,j])
            dy.append(signalsdy[indiceMax][i,j])
    dx = np.array(dx)
    dy = np.array(dy)
    dx = dx.reshape((n,m))
    dy = dy.reshape((n,m))
    return dx, dy

def convexCombOfTwo(point, vpoints):
    '''
    @brief Función que dado un ángulo y una lista de ángulos posibles nos dice
    en qué porcentaje debemos sumar a cada índice del histograma
    @param point Ángulo del que queremos obtener los coeficientes
    @param vpoints Lista que contiene una división equiespaciada de los posibles
    valores del ángulo point
    @return Devuelve una 4-upla que contiene el valor del primer índice, su
    coeficiente correspondiente, el valor del segundo índice y su coeficiente
    correspondiente
    '''
    N = len(vpoints)
    for i in range(1,N):
        # En el momento en que encontremos el ángulo de la lista que es mayor que el nuestro
        if vpoints[i]>point:
            # Calculamos los coeficientes y los devolvemos
            tam = vpoints[1]-vpoints[0]
            coef1 = 1 - (point-vpoints[i-1])/tam
            coef2 = (point-vpoints[i-1])/tam
            return i-1, coef1, i, coef2
    # Si el ángulo es justo el último asignamos los coeficientes
    if point == vpoints[N-1]:
        return N-2, 0, N-1, 1
    return False

def computeHistogram(subMag, subAng, num_cols, threeSixtyQ=False):
    '''
    @brief Dada una célula con un vector gradiente en cada posición coge el ángulo
    de cada vector y hace un histograma en forma de vector con los ángulos ponderados.
    @param cell Matriz con los datos del gradiente que representa una célula
    @return Devuelve un vector  de 180 elementos donde tiene un 0 si el ángulo no aparece
    o un valor correspondiente a la interpolación bilineal al obtener el histograma.
    '''
    m,n = subMag.shape
    possibleAngles = []
    # Inicializamos el histogama
    histogram = np.zeros(num_cols)
    # Si estamos en 0,360 o en 0,180 hacemos la lista de posibles ángulos
    if threeSixtyQ:
        possibleAngles = np.linspace(0,360,num_cols)
    else:
        possibleAngles = np.linspace(0,180,num_cols)
    # Para cada posición calculamos el ángulo y sumamos el valor proporcional a la
    # magnitud a la posición correspondiente del histograma
    for i in range(m):
        for j in range(m):
            mag = subMag[i,j]
            angle = None
            if threeSixtyQ:
                angle = subAng[i,j]
            else:
                angle = subAng[i,j] if subAng[i,j] < 180 else subAng[i,j]-180
            indice1, coef1, indice2, coef2 = convexCombOfTwo(angle,possibleAngles)
            histogram[indice1] += coef1*mag
            histogram[indice2] += coef2*mag
    return list(histogram)

def modifyLocalMatrix(img,local_matrix,row_min,row_max,col_min,col_max):
    '''
    @brief Función que modifica la submatriz de img dada por los valores row_min,
    row_max, col_min y col_max con los valores de local_matrix
    @param img Matriz de la imagen que queremos modificar
    @param local_matrix Matriz local que tiene los valores que queremos poner en img
    @param row_min Valor mínimo en las filas (se empieza desde este índice)
    @param row_max Valor máximo en las filas (no se tinta en inglesllega a tomar este valor de índice)
    @param col_min Valor mínimo en las columnas (se empieza desde este índice)
    @param col_max Valor máximo en las columnas (no se llega a tomar este valor de índice)
    @return Devuelve una copia de img con los valores modificados según local_matrix
    '''
    # Creamos una copia de la imagen
    img_aux = np.copy(img)
    for i in range(row_min,row_max):
        for j in range(col_min,col_max):
            # Modificamos los valores de la imagen auxiliar con los de local_matrix
            img_aux[i][j]=local_matrix[i-row_min][j-col_min]
    return img_aux

def loadTrainImgs():
    '''
    @brief Función que devuelve las imágenes de entrenamiento como dos listas
    @return Devuelve dos vectores, el primero con los casos positivos, es decir,
    donde si hay personas y el segundo con los casos negativos, es decir, donde
    no hay personas.
    '''
    pos_imgs = []
    neg_imgs = []
    pos_imgs_names = os.listdir(PATH_TO_INRIA+"/cropped_pos")
    for pimg in pos_imgs_names:
        im = cv.imread(PATH_TO_INRIA+"/cropped_pos/"+pimg,-1)
        im = np.float32(im)
        pos_imgs.append(im)
    neg_imgs_names = os.listdir(PATH_TO_INRIA+"/cropped_neg")
    for nimg in neg_imgs_names:
        neg_imgs.append(cv.imread(PATH_TO_INRIA+"/cropped_neg/"+nimg,-1))
    return pos_imgs,neg_imgs

def loadTestImgs():
    '''
    @brief Función que devuelve las imágenes de test como dos listas
    @return Devuelve dos vectores, el primero con los casos positivos, es decir,
    donde si hay personas y el segundo con los casos negativos, es decir, donde
    no hay personas.
    '''
    pos_imgs = []
    neg_imgs = []
    pos_imgs_names = os.listdir(PATH_TO_INRIA+"/cropped_test_pos")
    for pimg in pos_imgs_names:
        im = cv.imread(PATH_TO_INRIA+"/cropped_test_pos/"+pimg,-1)
        im = np.float32(im)
        pos_imgs.append(im)
    neg_imgs_names = os.listdir(PATH_TO_INRIA+"/cropped_test_neg")
    for nimg in neg_imgs_names:
        neg_imgs.append(cv.imread(PATH_TO_INRIA+"/cropped_test_neg/"+nimg,-1))
    return pos_imgs,neg_imgs

def getAllWindows(im,window_size=(64,128)):
    '''
    @brief Función que devuelve todas las submatrices de 64x128 de la imagen im
    @param im Imagen de la que queremos sacar las submatrices
    @param window_size Tupla que nos da las dimensiones de la ventana
    @return Devuelve una lista con las submatrices de 64x128 extraídas
    '''
    ret = []
    m = im.shape[0]
    n = im.shape[1]
    for i in range(m-window_size[1]):
        for j in range(n-window_size[0]):
            ret.append(im[i:i+window_size[1],j:j+window_size[0]])
    return ret


def gaussianPyramid(img,levels=3):
    '''
    @brief Esta función obtiene la pirámide gaussiana de la imagen dada.
    @param img Imagen a la que se le quiere calcular la pirámide gaussiana.
    @param levels Niveles de la pirámide gaussiana, por defecto 3.
    @return Devuelve la pirámide gaussiana de la imagen pasada.
    '''
    pyr = []
    # Se hace un downsample a la imagen. La función pyrDown implementa ya el blur.
    img_pyr = cv.pyrDown(img)
    pyr.append(img)
    pyr.append(img_pyr)
    # Se hace el downsample y el blur tantas veces como niveles se quieran a la imagen una y otra vez.
    for i in range(levels-2):
        img_pyr = cv.pyrDown(img_pyr)
        pyr.append(img_pyr)
    return pyr

def getPedestrianBoxes(img_name):
    '''
    @brief Función que dado el nombre de una imagen de la carpeta Test de INRIAPerson
    por ejemplo crop001501.png devuelve las cajas en las que hay peatones
    @param img_name Nombre de la imagen sobre la que queremos obtener las cajas de los peatones
    @return Devuelve una lista de listas en las que en cada sublista se encuentran
    los valores xmin, ymin, xmax, ymax que delimitan el rectángulo del peatón
    '''
    # Nos quedamos sólo con el nombre crop001501
    name_only = img_name.split(".")[0]
    # Leemos el fichero, en ISO porque si no da fallos de procesamiento
    annotations_f = open(PATH_TO_INRIA+"/Test/annotations/"+name_only+".txt","r",encoding = "ISO-8859-1")
    # Inicializamos la lista de cajas
    boxes = []
    for line in annotations_f:
        # Si en la línea se da información sobre la caja de peatones
        if "Bounding box" in line:
            # Magia y saco los valores, mejor no preguntes
            xmin = int(line.split(":")[1].split("-")[0].replace(" ","").split(",")[0].split("(")[-1])
            ymin = int(line.split(":")[1].split("-")[0].replace(" ","").split(",")[1].split(")")[0])
            xmax = int(line.split("-")[-1].replace(" ","").split(",")[0].split("(")[-1])
            ymax = int(line.split("-")[-1].replace(" ","").split(",")[1].split(")")[0])
            # Se une la lista a boxes
            boxes.append([xmin,ymin,xmax,ymax])
    return boxes

def getWindowsAndTagsPos(imgs,boxes):
    windows = []
    tags = []
    for i in range(len(imgs)):
        lwindow= calculateEveryWindow(imgs[i],boxes[i])
        windows = windows + lwindow
        tags = tags + [ 1 for i in range(len(windows)) ]
    return windows, tags

def getWindowsAndTagsNeg(imgs):
    windows = obtainNegatives(neg_samples_dir="../../INRIAPerson/Test/neg/")
    tags = 2*np.ones(len(windows))
    return windows, tags


def checkArea(x1,y1,x2,y2,u1,v1,u2,v2):
    areaTotal = float((x2-x1)*(y2-y1))
    areaParcial = float((u2-u1)*(v2-v1))
    return areaParcial/areaTotal >= 0.5

def calculateEveryWindow(img, boxes):
    windows=[]
    pyr = gaussianPyramid(img)
    for level in pyr:
        y,x,z = level.shape
        indiceX = 0
        indiceY = 0
        while indiceY+128<y:
            indiceX = 0
            while indiceX+64<x:
                for xmin,ymin,xmax,ymax in boxes:
                    x1 = max(indiceX, xmin)
                    y1 = max(indiceY, ymin)
                    x2 = min(indiceX+64,xmax)
                    y2 = min(indiceY+128,ymax)
                    if x1<x2 or y1<y2:
                        if checkArea(xmin,ymin,xmax,ymax,x1,y1,x2,y2):
                            windows.append(img[indiceY:indiceY+128,indiceX:indiceX+64])
                indiceX = indiceX + 32
            indiceY = indiceY + 64
    return windows

def getImagesAndTags():
    pos_imgs = []
    pos_boxes = []
    neg_imgs = []
    pos_imgs_names = os.listdir(PATH_TO_INRIA+"/Test/pos")
    for pimg in pos_imgs_names:
        im = cv.imread(PATH_TO_INRIA+"/Test/pos/"+pimg,-1)
        im = np.float32(im)
        pos_imgs.append(im)
        pos_boxes.append(getPedestrianBoxes(pimg))
    del pos_imgs_names
    neg_imgs_names = os.listdir(PATH_TO_INRIA+"/Test/neg")
    for nimg in neg_imgs_names:
        im = cv.imread(PATH_TO_INRIA+"/Test/neg/"+nimg,-1)
        im = np.float32(im)
        neg_imgs.append(im)
    del neg_imgs_names
    pos_windows, tags_pos_windows = getWindowsAndTagsPos(pos_imgs,pos_boxes)
    del pos_imgs
    del pos_boxes
    neg_windows, tags_neg_windows = getWindowsAndTagsNeg(neg_imgs)
    del neg_imgs
    resp = np.concatenate((tags_pos_windows,tags_neg_windows)).astype(np.int)
    return pos_windows + neg_windows, resp
