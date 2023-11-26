from importlib import reload
import numpy as np
import math
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import Support_v0
reload(Support_v0)
from Support_v0 import histc
from Support_v0 import nameForBase

#Umbrales
class Thresholds:

  #inicializar los valores de cada columna
    def __init__(self, dataPatient, PAT=-1, Age=-1, H_Y=-1):
        self.dataPatient=dataPatient
        #busca en el dataframe los nombres pasados 'asi'
        colNameAge=nameForBase(self.dataPatient, 'AGE')
        colNameH_Y=nameForBase(self.dataPatient, 'H_Y')
        colNamePAT=nameForBase(self.dataPatient, 'PAT')
        colNameLL=nameForBase(self.dataPatient, 'LL')
        colNameTH_LO=nameForBase(self.dataPatient, 'TH_LO')
        colNameTH_HI=nameForBase(self.dataPatient, 'TH_HI')
        colNameW_MEAN=nameForBase(self.dataPatient, 'W_MEAN')
        colNameW_STD=nameForBase(self.dataPatient, 'W_STD')
        colNameNUM_WALK=nameForBase(self.dataPatient, 'NUM_WALK')
        
        #asignamos esa edad a cada elemento de la columna colNameAge.
        if not(Age==-1):
            self.dataPatient[colNameAge]=[Age for i in range(len(self.dataPatient[colNameAge]))]

        #Hoehn & Yahr en OFF.
        if not(H_Y==-1):
            self.dataPatient[colNameH_Y]=[H_Y for i in range(len(self.dataPatient[colNameH_Y]))]    

        #Identificador de paciente.
        if not(PAT==-1):
            self.dataPatient[colNamePAT]=[PAT for i in range(len(self.dataPatient[colNamePAT]))]        
        
        #Valores únicos
        self.Age=self.dataPatient[colNameAge].unique()
        self.H_Y=self.dataPatient[colNameH_Y].unique()
        self.LL=self.dataPatient[colNameLL].unique()
        self.PAT=self.dataPatient[colNamePAT].unique()
        
        self.walk_mean=self.dataPatient[colNameW_MEAN]
        self.walk_std=self.dataPatient[colNameW_STD]
        self.num_walk=self.dataPatient[colNameNUM_WALK]

        
        if (len(dataPatient[colNameTH_LO].unique())!=1 | len(dataPatient[colNameTH_HI].unique())!=1 | len(self.Age)!=1 | len(self.H_Y)!=1 | len(self.LL)!=1 | len(self.PAT)!=1):
            print ('Error en los datos de identificación de paciente')
            error()
        
        if ((self.Age<0) | (self.Age>125)):
            print ('Error en la edad del paciente')
            error()
        
        if ((self.H_Y<0) | (self.H_Y>5)):
            print ('Error en H&Y del paciente')
            error()
            
            
        columnnamesForDel=[columnName for columnName in self.dataPatient.columns if ("Unnamed" in columnName)]
        for col in columnnamesForDel:
            del self.dataPatient[col] #borra columnas sin nombre 
            
        pass
        
    def calculate (self):    
        self.filter()
        return self.eSVMreg()
        
    
    def filter(self):
                
        self.pesoNumPaso_tot     = list();
        self.Brady_mean_weighted = list();
        self.Brady_mean_filtered = list();
        for i in range(len(self.num_walk)):
            pesoNumPaso = 0;
            if ((self.num_walk[i]!=0) & (not(np.isnan(self.num_walk[i])))):
                numPassosTransf   = (self.num_walk[i]/20)*12 -6
                pesoNumPaso       = (1./(1+math.exp( - numPassosTransf )))

            self.Brady_mean_weighted.append(self.walk_mean[i]* pesoNumPaso)
            self.pesoNumPaso_tot.append(pesoNumPaso);

        self.Brady_mean_weighted=np.array(self.Brady_mean_weighted)
        self.pesoNumPaso_tot=np.array(self.pesoNumPaso_tot)

        
        filtering=(((self.walk_std>1.7) & (self.num_walk < 10)) | (self.num_walk  < 3))

        self.Brady_mean_weighted[filtering]= 0
        self.num_walk[filtering]= 0
        self.pesoNumPaso_tot[filtering]= 0

        for i in range(len(self.num_walk)):
            num_min_pasos=self.num_walk>0;

            if (i<=9):
                inds=([ix for ix in range(i+1)])
            else:
                inds=([ix for ix in range(i-9,i+1)])

            acum_mean_aux          = sum( self.Brady_mean_weighted[inds]);
            acum_num_aux           = sum( self.pesoNumPaso_tot[inds]);
            acum_num_min_pasos_aux = sum( num_min_pasos[inds]);

            if ((acum_num_min_pasos_aux>1) & (acum_num_aux>0)):
                self.Brady_mean_filtered.append (acum_mean_aux/acum_num_aux)
            else:
                self.Brady_mean_filtered.append(0)
                
        self.Brady_mean_filtered=np.array(self.Brady_mean_filtered)
       
       
        edgesH=list()
        edgesH.append(0)
        [edgesH.append(ind) for ind in np.arange(2, 15.5, 0.5)]
        edgesH.append(20)
        aux4=(np.diff(edgesH)/2).tolist()
        aux4.append(5)
        centers = [edgesH[ind]+aux4[ind] for ind in range(len(edgesH))]

        histVals  = histc(self.Brady_mean_filtered,edgesH)


        self.hist={ 'centers': centers, 
                    'edges': edgesH,
                    'vals': histVals.tolist(),
                    'valsSinCero': histVals[1:].tolist()}
                    

    
    
    def eSVMreg(self):
        #Voy ha hacer una implementación fija, que es menos tocable.
        #Definición del modelo hecho a manija.
        nr_class = 2
        totalSV = 9
        rho = -6.4296
        parameters = [3.00000, 2.00000, 3.00000, 0.01000, 0.00000]
        sv_indices = [1, 4, 5, 6, 7, 8, 9, 10, 11]
        sv_coef = [ 2.41852, -0.22520, 4.55590, -6.63590, 10.00000,-2.74457, -10.00000, 6.39912, -3.76786 ]
        #Compressed Column Sparse (rows = 9, cols = 8, nnz = 72 [100%])
        SVs = [ [ -0.37553, -0.16032, 0.83929, 1.3871, 1.2865, 1.0657, 0.49213, 1.8965 ],
                [ -0.37553, -1.4428, -0.47583, 0.38191, 0.44173, 0.70571, 0.83431, 0.44386 ],
                [ -0.37553, 1.4428, 0.47513, 0.20029, -0.11198, -0.28673, -0.012478, 0.44386 ],
                [ -0.37553, 1.8703, -0.66498, -0.32617, -0.43092, -0.16723, 0.48956, -1.0088 ],
                [ -0.37553, 0.053438, -0.89812, -0.50393, -0.084291, 0.24198, 0.28112, -0.040351 ],
                [ -0.37553, -0.58782, -1.0620, -0.15308, -0.10566, -0.073665, 1.1064, 0.44386 ],
                [ -0.37553, -0.16032, 0.11055, -0.43911, -0.29628, -0.26276, -0.33653, -0.040351 ],
                [ -0.37553, 0.37407, 0.60154, 0.081130, 0.48843, 0.51836, 0.045123, 0.92807 ],
                [  3.0043 , 0.16032, -1.4500, -0.57011, -0.54091, -0.60723, 0.52409, 0.44386 ] ]

        normMean= [ 2.6667, 62.5000, 3.6645, 6.1304, 7.1992, 8.2962, 11.6736, 6.2917 ]
        normStd= [ 0.44381, 9.35657, 1.06720, 1.14585, 1.32913, 1.45963, 2.58280, 1.03261 ]
        
        vals = self.Brady_mean_filtered[self.Brady_mean_filtered!=0];
        vectorAct=list()
        vectorAct.append(self.H_Y[0])
        vectorAct.append(self.Age[0])
        vectorAct.append(min(vals))
        vectorAct.append(np.percentile(vals, 25))
        vectorAct.append(np.percentile(vals, 50))
        vectorAct.append(np.percentile(vals, 75))
        vectorAct.append(max(vals))
        vectorAct.append(self.hist['centers'][self.hist['valsSinCero'].index(max(self.hist['valsSinCero']))])
        
        datosParaAnchoZonaIntermedia = [np.percentile(vals, 25), np.percentile(vals, 75)];        
        vectorAct = [(vectorAct[index]-normMean[index])/normStd[index] for index in range(len(vectorAct))]
        
        #Predict central threshold
        #OutputJava is obtained by doing the eps - SVR prediction  phase:
        #http://www.csie.ntu.edu.tw/~cjlin/papers/libsvm.pdf
        
        centerMio   = -rho;
        for i in range(len(SVs)):
            newVector=[(vectorAct[ind] - SVs[i][ind]) for ind in range(len(vectorAct))]
            centerMio = centerMio + sv_coef[i]*math.exp(-parameters[3]*math.pow(np.linalg.norm(newVector),2))
       
        zonaInt   = ( datosParaAnchoZonaIntermedia[1] - datosParaAnchoZonaIntermedia[0])/ 2;
        
        self.TH_HI=centerMio+zonaInt/2
        self.TH_LO=centerMio-zonaInt/2
        
        print('The new Thresholds are: ' + str(self.TH_HI) + ' and ' + str(self.TH_LO))
        return self.TH_HI, self.TH_LO
        