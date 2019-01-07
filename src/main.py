import descriptorHOG
import cv2 as cv
import auxFunc as af
import pdb
import random
import numpy as np

'''
print("Obteniendo los datos de entrenamiento")
# Obtenemos los datos de entrenamiento
td = descriptorHOG.obtainTrainData()
print("Entrenando la SVM")
# Entrenamos la SVM
svm = descriptorHOG.trainSVM(td)
del td
'''
print("Cargando la SVM de fichero")
svm = cv.ml.SVM_load("svm.txt")
print("Cargandos las imagenes de test")
print("Obteniendo las ventanas y descriptores de las imágenes pregunta")
descr, tags = descriptorHOG.createTestData()
predicciones = svm.predict(descr)[1]
predicciones = [pred[0] for pred in predicciones]

del descr
del svm

print("\n\n##################################################")
print("Predicción: ")
print(predicciones)
print("##################################################\n\n")


npos=0
nneg=0
total_neg = 0
total_pos = 0
# Calculamos el número de aciertos
for i in range(len(predicciones)):
    if tags[i]==1:
        total_pos+=1
    else:
        total_neg+=1
    if tags[i]==predicciones[i]:
        if predicciones[i]==1:
            npos+=1
        else:
            nneg+=1
print("\n\n##################################################")
print("Positivos: " + str(npos) + "/" + str(total_pos) + "===>" + str(100*npos/total_pos) + "%")
print("Negativos: " + str(nneg) + "/" + str(total_neg) + "===>" + str(100*nneg/total_neg) + "%")
print("Porcentaje de acierto total: " + str(100*(npos+nneg)/(total_pos+total_neg)))
print("##################################################\n\n")
