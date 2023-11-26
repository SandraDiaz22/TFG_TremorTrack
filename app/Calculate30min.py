from importlib import reload
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import math
import datetime
import Support_v0
reload(Support_v0)
from Support_v0 import nameForBase
from Support_v0 import devuelve_media_mayor_zero
from Support_v0 import datetimeToEpoc
class Calculate30min:

        
    def __init__(self, dataPatient):
        
        self.dataPatient=dataPatient
                
        pass

    
    def minutes30Calcs(self):
    
        self.data30min=pd.DataFrame()
        self.dataPatient=self.dataPatient.drop(['DATE'], axis=1, errors='ignore')
        self.dataPatient['DATE']=[datetime.datetime.utcfromtimestamp(item/1000) for item in self.dataPatient[nameForBase(self.dataPatient, 'EPO')]]
        firstDay=datetime.datetime.strptime(self.dataPatient['DATE'][0].strftime ('%Y-%m-%d') , '%Y-%m-%d')
        lastDay=datetime.datetime.strptime(self.dataPatient['DATE'][len(self.dataPatient)-1].strftime ('%Y-%m-%d') , '%Y-%m-%d')
        oneDay=datetime.timedelta (days=1) 

        actualDay=firstDay
        daysBruto=1
        while(lastDay>=actualDay):
            dayAux=self.dataPatient.loc[np.where((self.dataPatient['DATE']>=actualDay) & (self.dataPatient['DATE']<(actualDay+oneDay)))]
            self.data30min=self.data30min.append(self.calculaVector(dayAux,actualDay,daysBruto),ignore_index = True)
            actualDay=actualDay+oneDay
            daysBruto=daysBruto+1
    
        print ('A total of: ' + str(daysBruto-1) + ' days has been recalculated')
        
    def calculaVector(self, dayAux,dayNow,daysBruto):
        vect_hour=list()
        for item in range(24):
            vect_hour.append(item)
            vect_hour.append(item)
        vect_hour=np.array(vect_hour)
        vect_min=np.zeros(len(vect_hour))
        for item in np.arange(1,len(vect_min),2):
            vect_min[item]=30 
        Time_sens=[datetime.datetime.strptime(dayNow.strftime('%Y-%m-%d') + '--'+str(int(vect_hour[ind])) + ':' + str(int(vect_min[ind])), '%Y-%m-%d--%H:%M') for ind in range(len(vect_hour))]
        Time_epo=[datetimeToEpoc(item) for item in Time_sens]
        aux=np.zeros(len(Time_sens))
        aux[:]=np.nan
        
        dataAux=pd.DataFrame()
        dataAux['EPO']=Time_epo
        dataAux['vect_monit']=list(np.zeros(len(Time_sens)))
        dataAux['vect_off']=list(np.zeros(len(Time_sens)))
        dataAux['vect_int']=list(np.zeros(len(Time_sens)))
        dataAux['vect_on']=list(np.zeros(len(Time_sens)))
        dataAux['vect_dysk']=list(np.zeros(len(Time_sens)))
        dataAux['vect_FoG']=list(np.zeros(len(Time_sens)))
        dataAux['vect_epi_FoG']=list(np.zeros(len(Time_sens)))
        dataAux['vect_dur_FoG']=list(np.zeros(len(Time_sens)))
        dataAux['vect_Button']=list(np.zeros(len(Time_sens)))
        dataAux['vect_SMA']=list(aux)
        dataAux['vect_Cadencia']=list(aux)
        dataAux['vect_SL']=list(aux)
        dataAux['vect_SV']=list(aux)
        dataAux['vect_walk_mean']=list(aux)
        dataAux['vect_num_Pasos']=list(aux)
        dataAux['Time']=Time_sens
        aux=np.zeros(len(Time_sens))
        aux[:]=daysBruto
        dataAux['Day']=list(aux)

        # Se patea la linea de tiempo generando un valor cada 30 min
        for i in range(len(Time_sens)):
            # Se buscan los valores dentro del periodo de tiempo de 30 minutos
            
            if i<(len(Time_sens)-1):
                aux_inds=dayAux.loc[dayAux.index[np.where((dayAux['DATE']>=Time_sens[i]) & (dayAux['DATE']<Time_sens[i+1]))]]
            else:
                aux_inds=dayAux.loc[dayAux.index[np.where(dayAux['DATE']>=Time_sens[i])]]
                
                
            if len(aux_inds)>0:
                dataAux=self.calculaDia30min(dataAux, aux_inds, i)
            
        

        return dataAux

    def calculaDia30min(self, dataAux, aux_inds, i):
    
        dataAux['vect_monit'][i]    =1
        dataAux['vect_SMA'][i]      =devuelve_media_mayor_zero(aux_inds[nameForBase(aux_inds, 'SMA')])
        dataAux['vect_Cadencia'][i] =devuelve_media_mayor_zero(aux_inds[nameForBase(aux_inds, 'CAD')])
        dataAux['vect_SL'][i]       =devuelve_media_mayor_zero(aux_inds[nameForBase(aux_inds, 'LEN')])
        dataAux['vect_SV'][i]       =devuelve_media_mayor_zero(aux_inds[nameForBase(aux_inds, 'SPEED')])
        dataAux['vect_walk_mean'][i]=devuelve_media_mayor_zero(aux_inds[nameForBase(aux_inds, 'W_MEAN_FILT')])
        dataAux['vect_num_Pasos'][i]=sum(aux_inds[nameForBase(aux_inds, 'NUM_STEPS')])

        #           Se recogen aquellos indices que coincidan con los estados motores dentro de la variable de estado motor (0-OFF 1-ON 2-INT)        
        inds_off=sum(aux_inds[nameForBase(aux_inds, 'MOTOR10')]==0)
        inds_int=sum(aux_inds[nameForBase(aux_inds, 'MOTOR10')]==2)
        inds_on =sum(aux_inds[nameForBase(aux_inds, 'MOTOR10')]==1);



        if ((inds_int+inds_off+inds_on)>2):
        #                 Se calculan los porcentajes dentro del periodo
            total=inds_int+inds_off+inds_on
            pct_on=100*(inds_on/total)
            pct_off=100*(inds_off/total)
            pct_int=100*(inds_int/total)

        #               Se aplica el siguiente arbol, si hay mas de un 60% de OFF
        #               la decision es off, si hay más de un 60% de ON la decision
        #               en on los demas casos es intermedio.

            if ((pct_off>50) | (pct_off>(pct_on+pct_int))):
                dataAux['vect_off'][i]= 1
            else: 
                if ((pct_on>50) | (pct_on>(pct_off+pct_int))):
                    dataAux['vect_on'][i]= 1
                else:
                    dataAux['vect_int'][i]= 1

        #           Si hay un solo valor de discinesia en el calculo de discinesia
        #           de 10 minutos se considera que ha habido discinesia dentro del
        #           periodo de media hora

        if sum(aux_inds[nameForBase(aux_inds, 'DYSK10')]==1)>0:
            dataAux['vect_dysk'][i]= 1



        #             Se contabilizan todos los episodios de FoG en el periodo y se 
        #             ejecuta la media de duración de los episodios. NOTA: las
        #             unidades de result_per_min_MATLAB.Vent_FoG es 1.6 segundos, o
        #             sea que para obtener la media 

        if sum(aux_inds[nameForBase(aux_inds, 'FOG_EP')])>0:
            dataAux['vect_epi_FoG'][i]= sum(aux_inds[nameForBase(aux_inds, 'FOG_EP')])
            dataAux['vect_FoG'][i]= 1
            dataAux['vect_dur_FoG'][i]= (sum(aux_inds[nameForBase(aux_inds, 'FOG_WIN')]>0)*1.6)/dataAux['vect_epi_FoG'][i] 
        
        #           Se contabilizan todas las pulsaciones de boton
        if sum(aux_inds[nameForBase(aux_inds, 'BTN_PRESSED')])>0:
            dataAux['vect_Button'][i]= sum(aux_inds[nameForBase(aux_inds, 'BTN_PRESSED')])
        
        return dataAux


        

        
        
        
