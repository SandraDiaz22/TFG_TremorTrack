import numpy as np
import math
import pandas as pd
import datetime
import matplotlib
import matplotlib.pyplot as plt



#Histograma de x (array de datos) con los limites definidos en bins
def histc(X, bins):
    map_to_bins = np.digitize(X,bins) #asigna a cada x el indice del bin al que pertenece
    
    r = np.zeros(len(bins)) #array de ceros del tamaño de bins
    
    for i in map_to_bins: #recorre el array sumando el numero de x en cada bin
        r[i-1] += 1
        
    return r #devuelve cuantos datos de x hay en cada bin   



#Función que encuentra en el dataframe el nombre pasado
def nameForBase(dataframe, name):
    #lista de columnas con ese nombre
    aux=[colNew for colNew in dataframe.columns if name in colNew]
    
    #si no se ha encontrado ninguna se buscan alternativas de nombre parecidas
    if ((len(aux)<1)): 
        if ('H_Y' in name):
            aux=[colNew for colNew in dataframe.columns if 'H&Y' in colNew]
        if ('H&Y' in name):
            aux=[colNew for colNew in dataframe.columns if 'H_Y' in colNew]
  
    return aux[0] #devuelve la primera columna que coincida



#Función que devuelve los nombres de las columnas del dataframe
def getBaseNames():
    return ['EPO', 'W_MEAN', 'W_MEAN_FILT', 'W_STD', 'NUM_WALK', 'SMA', 'DYSKP',
            'DYSKC', 'LEN', 'NUM_STEPS', 'SPEED', 'CAD', 'TW', 'TL', 'TRANS',
            'FALLS', 'FOG_EP', 'FOG_WIN', 'BTN_PRESSED', 'MOTOR10', 'DYSK10',
            'BRADY10', 'TH_LO', 'TH_HI', 'AGE', 'H_Y', 'LL', 'PAT']



#Función que devuelve la media de los valores positivos del array var_m
def devuelve_media_mayor_zero(var_m):
    media=np.nan; #media de numpy vacía
    var_m[np.isnan(var_m)]=0; #reemplaza nan con 0
    var_m[np.isinf(var_m)]=0; #reemplaza infinitos con 0
    
    if sum(var_m>0)>0:     #si hay algo mayor que 0                
         media= np.mean(var_m[var_m>0]); #calcula la media
    return media
    


#Función que imprime el primer y ultimo día de un paciente,
#siendo dataPatient el csv con todos los datos del paciente
#y siendo EPO: "es la medida de tiempo que se ha adquirido la muestra. 
#Llamada Epoch Time o Tiempo Unix, son los segundos que han pasado en UTC
#desde el 1 de Enero del 1970."
def first_and_last_days(dataPatient):

    firstDay=EpocToDatetime(dataPatient['EPO'][0]) #Pasa el primer EPO a fecha y hora normal
    lastDay=EpocToDatetime(dataPatient['EPO'][len(dataPatient)-1]) #Y el ultimo

    #Imprime las dos fechas-hora
    print('First Day: ' + firstDay.strftime ('%Y-%m-%d') )
    print('Last Day: ' + lastDay.strftime ('%Y-%m-%d') )
    
    return onlyDay(firstDay),onlyDay(lastDay) #retorna solo el dia

#Funcion usada para transformar de fecha normal a EPO
def datetimeToEpoc(dateTi):
    return int((dateTi - datetime.datetime(1970,1,1)).total_seconds())*1000

#Funcion usada en first_and_last_days para transformar de EPO a fecha normal 
def EpocToDatetime(dateTi):
    return datetime.datetime.utcfromtimestamp(dateTi/1000)

#Funcion usada en first_and_last_days para eliminar la hora y tener solo fecha
def onlyDay(dateTi):
    return datetime.datetime.strptime(dateTi.strftime ('%Y-%m-%d') , '%Y-%m-%d')



#Funcion para solo sacar la info de un paciente entre dos fechas especificadas
def cutDateFrameByDate(dataPatient, dayIni, dayFin):
    #Datos cuyas fechas sean mayor que ini y menor que fin
    #np.where obtiene los indices de las filas que cumplen la condicion
    #.loc selecciona del dataframe esos indices
    newData=dataPatient.loc[np.where((dataPatient['EPO']>=datetimeToEpoc(dayIni)) & (dataPatient['EPO']<datetimeToEpoc(dayFin)))]
    
    newData.reset_index(drop=True, inplace=True)#reinicia los indices del nuevo dataframe
    return newData
 


#Función que crea graficos (ver en ejemplos) para representar x datos (data) 
#del dataframe (dataP) a lo largo de un rango de tiempo especificado
def plot3Axis(dataP, data, title, ylabel, xlabel, GeneralTitle,dayIni,dayFin):
    
    dataByDays=returnByDatas(dataP,dayIni,dayFin) #Como cutDateFrameByDate
    time=[datetime.datetime.utcfromtimestamp(item/1000.) for item in dataByDays['EPO']] #EpocToDatetime

    #matploilib
    plt.figure(num=1, figsize=(20,10), dpi=150)
    plt.suptitle(GeneralTitle)
    plt.xlabel(xlabel)
    totalOfPlots=len(data)*100+10
    numberOfPlot=1
    
    for index in range(len(data)): #para cada dato a representar crea un subgrafo
        plt.subplot(totalOfPlots+numberOfPlot)
        plt.plot(time,dataByDays[data[index]].tolist())
        plt.title(title[index])
        plt.ylabel(ylabel[index])
        numberOfPlot=numberOfPlot+1
    
    plt.gcf().autofmt_xdate() #fechas legibles
    plt.show() #muestra todos los graficos




#Como cutDateFrameByDate
def returnByDatas(dataP,dayIni,dayFin):
    #EpocToDatetime
    time3=[datetime.datetime.utcfromtimestamp(item/1000.) for item in dataP['EPO']]
    
    output=set() #conjunto vacio que llena con fechas formateadas
    [output.add(item.strftime("%Y-%m-%d")) for item in time3]
    datasDatetime=[datetime.datetime.strptime(item, "%Y-%m-%d") for item in list(output)]
    
    datasDatetime.sort(reverse = False)#ordena ascendente
    ini=dayIni
    fin=dayFin   
    if (ini==-1):
        ini=1
    if ((fin==-1) | (fin>=len(datasDatetime))):
        fin=len(datasDatetime)-1
        
    index=np.where((dataP['EPO']>=(datasDatetime[ini-1].timestamp()*1000)) & (dataP['EPO']<(datasDatetime[fin].timestamp()*1000)))
    return dataP.loc[index] #devuelve las filas en el rango especificado