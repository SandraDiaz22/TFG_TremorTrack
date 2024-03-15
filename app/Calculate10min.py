from importlib import reload
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import math
import Support_v0
reload(Support_v0)
from Support_v0 import nameForBase

#Clase que monitoriza de la actividad motora, la bradicinesia y la discinesia
#del paciente en intervalos de 10 minutos.
class Calculate10min:

        
    def __init__(self, dataPatient, Brady_mean_filtered, TH_HI, TH_LO):
        self.Brady_mean_filtered=Brady_mean_filtered
        
        self.dataPatient=dataPatient
        
        self.Brady_llindarSup=TH_HI
        self.Brady_llindarInf=TH_LO
                
        self.dyskProb=self.dataPatient[nameForBase(self.dataPatient, 'DYSKP')]
        self.dyskConf=self.dataPatient[nameForBase(self.dataPatient, 'DYSKC')]
        self.timeCSV=self.dataPatient[nameForBase(self.dataPatient, 'EPO')]
        
        
        pass

    
    
    def minutes10Calcs(self):
        self.ON_OFF_minute=list();
        self.ON_OFF_10minute_by_minute=list()
        self.DyskConsidered_10_min_tot=list()


        inds_dysk_pos=((self.dyskProb>=0.3) & (self.dyskConf>=0.4))
        inds_dysk_pos=inds_dysk_pos.astype(int)
        inds_dysk_NaN=self.dyskConf<=0.3;
        inds_dysk_NaN=inds_dysk_NaN.astype(int)
        ON_OFF_10minute_act_val=3;
        counter_10_min=0;
        DyskConsidered_10_min=0;

        for i in range(len(self.Brady_mean_filtered)):
            counter_10_min=counter_10_min+1;
            
            if(self.Brady_mean_filtered[i]>0):
        #                 0-OFF 1-ON 2-INT 3-NaN
                if(self.Brady_mean_filtered[i]> self.Brady_llindarSup):
                        self.ON_OFF_minute.append(1)

                else: 
                    if(self.Brady_mean_filtered[i]< self.Brady_llindarInf):
                        self.ON_OFF_minute.append(0)
                    else:
                        self.ON_OFF_minute.append(2)
            else:
                self.ON_OFF_minute.append(3)

            if (counter_10_min>=10):

                counter_10_min=0;
                
                ON_OFF_10minute_act_val=2
                
                
                numBradNaN= sum(np.array(self.ON_OFF_minute[i-9:i+1])==3)
                numNoBrad=  sum(np.array(self.ON_OFF_minute[i-9:i+1])==1)
                numBradINT= sum(np.array(self.ON_OFF_minute[i-9:i+1])==2)
                numBrad=    sum(np.array(self.ON_OFF_minute[i-9:i+1])==0)
                numDyskNaN= sum(inds_dysk_NaN[i-9:i+1])
                numDysk=    sum(inds_dysk_pos[i-9:i+1])


                if (numBradNaN>=9):
                        ON_OFF_10minute_act_val=3;
                else:
                    if ((numNoBrad>numBradINT) & (numNoBrad>=2)):
                        ON_OFF_10minute_act_val=1;
                    else:
                        if (((numNoBrad+numBradINT)<numBrad) & (numBrad>1)):
                                ON_OFF_10minute_act_val=0;
                   
                DyskConsidered_10_min=0;    
                if ((numDyskNaN<=7) & (numDysk>=3)):
                    DyskConsidered_10_min=1;
                    if (ON_OFF_10minute_act_val==0):
                        ON_OFF_10minute_act_val=2;
                    else:
                        ON_OFF_10minute_act_val=1;
                else:
                    if (numDyskNaN>7):
                        DyskConsidered_10_min=3; 
                    else:
                        DyskConsidered_10_min=2;
                        
            self.ON_OFF_10minute_by_minute.append(ON_OFF_10minute_act_val)
            self.DyskConsidered_10_min_tot.append(DyskConsidered_10_min)
            
        for index in range(10,len(self.timeCSV)-15):
            if (((self.timeCSV[index]/1000)-(self.timeCSV[index-10])/1000)>11*60):
                self.ON_OFF_10minute_by_minute[index]=3;
                self.DyskConsidered_10_min_tot[index]=3;
                self.ON_OFF_minute[index]=3;
        
        print ('A total of: ' + str(len(self.timeCSV)) + ' minutes has been recalculated')
        
        self.dataPatient[nameForBase(self.dataPatient,'MOTOR10')]= self.ON_OFF_10minute_by_minute
        self.dataPatient[nameForBase(self.dataPatient,'DYSK10')]= self.DyskConsidered_10_min_tot
        self.dataPatient[nameForBase(self.dataPatient,'BRADY10')]= self.ON_OFF_minute
        self.dataPatient[nameForBase(self.dataPatient,'TH_HI')]=[self.Brady_llindarSup for i in range(len(self.dataPatient[nameForBase(self.dataPatient,'TH_HI')]))]
        self.dataPatient[nameForBase(self.dataPatient,'TH_LO')]=[self.Brady_llindarInf for i in range(len(self.dataPatient[nameForBase(self.dataPatient,'TH_LO')]))]



    #crea un excel con los resultados en 3 columnas(estado motor, discinesia y bradicinesia)
    def to_excel_10min (self, filename):           
        data = pd.DataFrame(list(zip(self.ON_OFF_10minute_by_minute, self.DyskConsidered_10_min_tot, self.ON_OFF_minute)), 
                            columns=['Motor State', 'Dysk_10min', 'Brady_10min'])
        data.to_excel(filename,index=False)

    #guarda los datos modificados en un csv
    def generateCSV(self, filename):      
        self.dataPatient.to_csv(filename,index=False)
        print ('The new File: ' +filename + ' has been created')