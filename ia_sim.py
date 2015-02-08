#Aaron Stacey
#June 03 2013
from SimPy.Simulation import *
from math import exp,log,floor,ceil

import csv
import array

def readInData(filename,filetype):
    #read in each line and split it as we read it to create a multidimensional
    #array.  The array is then returned to the calling process.
    #Used to read in all types of input files
    if filetype=="txt":
        table=[line.split() for line in open (filename)]
    else:
        table=[line.split(',') for line in open (filename)]
    return table

# load the file location for the fire data by year
# currently reads in the year and the scenario1****.txt location
#CSVReader=csv.reader(open('fireDataLocation.csv','rb'),delimiter=',',quotechar='"')
csvlist=readInData('fireDataLocation.csv',"csv")


def simFireStats():
    f=open(str(sys.argv[3])+"\\"+str(int_year_simulated)+".csv",'a')
    temp=str(sys.argv[1])+","+str(ontario.int_HumanFireCount)+","+str(ontario.int_LightningFireCount)+","+str(ontario.int_EscapedFires)+","+str(ontario.int_IASuccess)+","+str(prov2.int_HumanFireCount)+","+str(prov2.int_LightningFireCount)+","+str(prov2.int_EscapedFires)+","+str(prov2.int_IASuccess)+","+str(prov3.int_HumanFireCount)+","+str(prov3.int_LightningFireCount)+","+str(prov3.int_EscapedFires)+","+str(prov3.int_IASuccess)
    temp=str(temp)
    f.write(temp + '\n')
    f.close()

#Creating Class for Fire
class Fire(Process):
    def __init__(self,name):
        Process.__init__(self,name=name)
        self.name=name
        #Defining any crews assigned to the fire
        self.int_Crews=0
        self.int_CrewsExt=[0,0,0]
        self.int_Crewtype2=0
        self.int_Airtankers=0
        self.int_Helicopters=0
        self.int_CrewsRequested=0
        self.int_Crewtype2Requested=0
        self.int_AirtankersRequested=0
        self.int_HelicoptersRequested=0
        self.int_CrewsDispatched=0
        self.int_Crewtype2Dispatched=0
        self.int_AirtankersDispatched=0
        self.int_HelicoptersDispatched=0
        #Information about the fire itself        
        #From 'Initialize Fire Attributes'
        self.dbl_HeadAdvance=17+random.weibullvariate(145,0.758)
        self.dbl_BackAdvance= self.dbl_HeadAdvance / 2
        self.dbl_FlankAdvance = 0.75 * self.dbl_HeadAdvance
        self.dbl_Perimeter=0.0
        self.dbl_Size= (self.dbl_HeadAdvance + self.dbl_BackAdvance) * 0.5 * self.dbl_FlankAdvance * 0.0001 * 3.1416
        self.dbl_FireIntensity=0.0
        self.dbl_FirelinePerimeter=0.0
        self.int_ecoregion=0
        self.int_Fuel=0
        self.int_HoursDelayed =0
        self.dbl_DaysDelayed =0.0
        self.dbl_RealFinalSize=0.0
        self.int_ExcelDate=0
        self.dbl_ArrivalTime=0.0
        self.int_Cause =0
        self.int_EcoRegion=0
        self.dbl_Unif0to1=0.0
        self.int_ExtTime=0
        self.int_ExtDate=0
        self.bool_Burning=True
        self.dbl_probOfEscape=0.0
        
    #Assign 347
    #Get a random number from 0 to 1
    def setUnif0to1(self):
        self.dbl_Unif0to1=random.uniform(0,1)
    
    #Decide 39 from the Arena model
    #Does the fire escape? If the prob of escape is 
    #greater than the random value then we do escape
    def doesFireEscape(self):
        self.setUnif0to1()
        #print now(),self.name,"Escape:",self.dbl_probOfEscape,"0to1:",self.dbl_Unif0to1
        if self.dbl_probOfEscape>=self.dbl_Unif0to1:
            return True
        else:
            return False
        
    
    
    def fireSpotted(self,prov,provLoad,fuelNow,ecoregion,cause):
        #print now(),self.name, " Fire spotted in {0} -> fuel-> {1} eco-region {2} caused by {3}".format(prov.name, fuelNow ,ecoregion, cause)
        self.dbl_ArrivalTime=now()
        self.int_Fuel=fuelNow
        self.int_ecoregion=ecoregion
        if cause==2.0:
            self.recordPPL(prov)
        else:
            self.recordLTG(prov)
        isi=float(prov.getIndicator(floor(now()),3,ecoregion))
        #Check to see the size of the escape fire value to decide the potential escapes
        if int_escape_size_criteria==4:
            bool_Large=False
        else:
            bool_Large=True
        self.dbl_probOfEscape=float(probOfEscape(ecoregion,bool_Large,isi,provLoad))
        
        #Attempt to send an airtanker to the fire, followed by attempts to send
        #crews(local or external), then type2's and then helicopters though they have no impact right now
        if prov.int_airtanker_pool>0:
            yield request,self,prov.serv_Airtanker
            prov.int_airtanker_pool=prov.int_airtanker_pool-1
            self.int_Airtankers=1
            #Check if we can send local crew to this fire
            if prov.int_crew_pool>0:
                yield request,self,prov.serv_Crew1
                prov.int_crew_pool=prov.int_crew_pool-1
                self.int_Crews=self.int_Crews+1
                yield hold, self, float(delayCrews("crews")/24.0)
                yield release,self,prov.serv_Crew1
                prov.int_crew_pool=prov.int_crew_pool+1
                self.int_Crews=self.int_Crews-1
            #No Local crew, try the external crews to see if any are available
            else:
                if prov.bool_madeRequest and (prov.int_crewExt_pool[0]>0 or prov.int_crewExt_pool[1]>0 or prov.int_crewExt_pool[2]>0):
                    #Set the crewExt to look at, example, if Ontario has a fire, they would not look
                    #at themselves (0) for EXT fire help, so would look at 1-Prov2, 2-Prov3
                    temp1=0
                    temp2=0
                    if prov.name=="Ontario":
                        temp1=1
                        temp2=2 
                    elif prov.name=="Prov2":
                        temp1=0
                        temp2=2
                    else:
                        temp1=0
                        temp2=1
                                            
                    if prov.int_crewExt_pool[temp1]>0:
                        yield request,self,prov.serv_Crew1Ext
                        prov.int_crewExt_pool[temp1] -=1
                        self.int_Crews +=1
                        #set where the crew comes from (ie. what province)
                        yield hold, self, float(delayCrews("crews")/24.0)
                        yield release,self,prov.serv_Crew1Ext
                        prov.int_crewExt_pool[temp1] +=1
                        self.int_Crews -=1
                        #release the crew back to the proper province Ext pool
                        prov.int_crewExt_pool[temp1] +=1
                    elif prov.int_crewExt_pool[temp2]>0:
                        yield request,self,prov.serv_Crew1Ext
                        prov.int_crewExt_pool[temp2] -=1
                        self.int_Crews +=1
                        #set where the crew comes from (ie. what province)
                        yield hold, self, float(delayCrews("crews")/24.0)
                        yield release,self,prov.serv_Crew1Ext
                        prov.int_crewExt_pool[temp2] +=1
                        self.int_Crews -=1
                        #release the crew back to the proper province Ext pool
                        prov.int_crewExt_pool[temp2] +=1
                            
                else:
                    #Penalty for missing Type 1 Crews, attemp to send a type 2
                    #This would not likely happen but is possible, just no hover exit on this one
                    self.dbl_probOfEscape=self.dbl_probOfEscape*dbl_missingCrewPenalty
                    if prov.int_crewtype2_pool>0:
                        yield request,self,prov.serv_Crew2
                        prov.int_crewtype2_pool=prov.int_crewtype2_pool-1
                        self.int_Crewtype2=self.int_Crewtype2+1
                        yield hold, self, float(delayCrews("type2crews")/24.0)
                        yield release,self,prov.serv_Crew2
                        prov.int_crewtype2_pool=prov.int_crewtype2_pool+1
                        self.int_Crewtype2=self.int_Crewtype2-1
                    else:                
                        yield hold, self, float(delayCrews("airtanker")/24.0)
            yield release,self,prov.serv_Airtanker
            self.int_Airtankers=self.int_Airtankers-1
            prov.int_airtanker_pool=prov.int_airtanker_pool+1
        #No Airtanker available but still try to send everything else
        else:
            #print self.name
            if prov.bool_madeRequest and (prov.int_crewExt_pool[0]>0 or prov.int_crewExt_pool[1]>0 or prov.int_crewExt_pool[2]>0):
                #Set the crewExt to look at, example, if Ontario has a fire, they would not look
                #at themselves (0) for EXT fire help, so would look at 1-Prov2, 2-Prov3
                temp1=0
                temp2=0
                if prov.name=="Ontario":
                    temp1=1
                    temp2=2 
                elif prov.name=="Prov2":
                    temp1=0
                    temp2=2
                else:
                    temp1=0
                    temp2=1
                                        
                if prov.int_crewExt_pool[temp1]>0:
                    ##print prov.int_crewExt_pool[temp1]
                    yield request,self,prov.serv_Crew1Ext
                    prov.int_crewExt_pool[temp1] -=1
                    self.int_Crews +=1
                    #set where the crew comes from (ie. what province)
                    yield hold, self, float(delayCrews("crews")/24.0)
                    yield release,self,prov.serv_Crew1Ext
                    prov.int_crewExt_pool[temp1] +=1
                    self.int_Crews -=1
                    #release the crew back to the proper province Ext pool
                    prov.int_crewExt_pool[temp1] +=1
                elif prov.int_crewExt_pool[temp2]>0:
                    yield request,self,prov.serv_Crew1Ext
                    prov.int_crewExt_pool[temp2] -=1
                    self.int_Crews +=1
                    #set where the crew comes from (ie. what province)
                    yield hold, self, float(delayCrews("crews")/24.0)
                    yield release,self,prov.serv_Crew1Ext
                    prov.int_crewExt_pool[temp2] +=1
                    self.int_Crews -=1
                    #release the crew back to the proper province Ext pool
                    prov.int_crewExt_pool[temp2] +=1
            else:    
                #Penalty for missing Airtankers
                self.dbl_probOfEscape=self.dbl_probOfEscape*dbl_missingAirtankerPenalty
                if prov.int_crew_pool>0:
                    yield request,self,prov.serv_Crew1
                    prov.int_crew_pool=prov.int_crew_pool-1
                    self.int_Crews=self.int_Crews+1
                    yield hold, self, float(delayCrews("crews")/24.0)
                    yield release,self,prov.serv_Crew1
                    prov.int_crew_pool=prov.int_crew_pool+1
                    self.int_Crews=self.int_Crews-1
                else:
                    if prov.bool_madeRequest and (prov.int_crewExt_pool[0]>0 or prov.int_crewExt_pool[1]>0 or prov.int_crewExt_pool[2]>0):
                        #Set the crewExt to look at, example, if Ontario has a fire, they would not look
                        #at themselves (0) for EXT fire help, so would look at 1-Prov2, 2-Prov3
                        temp1=0
                        temp2=0
                        if prov.name=="Ontario":
                            temp1=1
                            temp2=2 
                        elif prov.name=="Prov2":
                            temp1=0
                            temp2=2
                        else:
                            temp1=0
                            temp2=1
                                                
                        if prov.int_crewExt_pool[temp1]>0:
                            yield request,self,prov.serv_Crew1Ext
                            prov.int_crewExt_pool[temp1] -=1
                            self.int_Crews +=1
                            #set where the crew comes from (ie. what province)
                            yield hold, self, float(delayCrews("crews")/24.0)
                            yield release,self,prov.serv_Crew1Ext
                            prov.int_crewExt_pool[temp1] +=1
                            self.int_Crews -=1
                            #release the crew back to the proper province Ext pool
                            prov.int_crewExt_pool[temp1] +=1
                        elif prov.int_crewExt_pool[temp2]>0:
                            yield request,self,prov.serv_Crew1Ext
                            prov.int_crewExt_pool[temp2] -=1
                            self.int_Crews +=1
                            #set where the crew comes from (ie. what province)
                            yield hold, self, float(delayCrews("crews")/24.0)
                            yield release,self,prov.serv_Crew1Ext
                            prov.int_crewExt_pool[temp2] +=1
                            self.int_Crews -=1
                            #release the crew back to the proper province Ext pool
                            prov.int_crewExt_pool[temp2] +=1
                    else:
                        #Penalty for missing Crew1
                        self.dbl_probOfEscape=self.dbl_probOfEscape*dbl_missingCrewPenalty
                        if prov.int_crewtype2_pool>0:
                            yield request,self,prov.serv_Crew2
                            prov.int_crewtype2_pool=prov.int_crewtype2_pool-1
                            self.int_Crewtype2=self.int_Crewtype2+1
                            yield hold, self, float(delayCrews("type2crews")/24.0)
                            yield release,self,prov.serv_Crew2
                            prov.int_crewtype2_pool=prov.int_crewtype2_pool+1
                            self.int_Crewtype2=self.int_Crewtype2-1
                        else:
                            self.dbl_probOfEscape=self.dbl_probOfEscape*dbl_missingCrewPenalty
        #Determine if the fire has escaped IA, if so it is true and we move into the attack of the fire
        #with more resources
        self.bool_Burning=self.doesFireEscape()
        if self.bool_Burning:
            #We have an escaped fire so increase the value
            prov.int_EscapedFires += 1
            #print prov.name,prov.int_EscapedFires
            while self.bool_Burning:                
                self.calcNeededResources()
                #print now(),self.name," Perimeter:",self.dbl_Perimeter, "Crews: ",self.int_CrewsRequested, "Type2's:", self.int_Crewtype2Requested
                #print now(),self.name,"CrewPool:",prov.int_crew_pool,"Crew2",prov.int_crewtype2_pool
                #Need to find the crews that can be dispatched
                #can be less than or equal to the requested
                #print now(),self.name,prov.int_EscapedFires,self.int_Crews,self.int_CrewsRequested
                if self.int_Crews>=self.int_CrewsRequested:
                    #print self.name,"XXXXXXXXXXXXXXXX No Crews needed so no crews to add to the fire"
                    self.int_CrewsDispatched=0
                else:
                    if prov.name=="Ontario":
                        temp1=1
                        temp2=2 
                    elif prov.name=="Prov2":
                        temp1=0
                        temp2=2
                    else:
                        temp1=0
                        temp2=1
                    if prov.int_crew_pool>0 or prov.int_crewExt_pool[temp1]>0 or prov.int_crewExt_pool[temp2]>0:
                        ##print "There are some crews but not enough. Pool:",prov.int_crew_pool
                        #Adding crews to the fire, this could be the amount requested or those available in the pool
                        #Not enough crews to reach requested level but should still be able to send some
                        #print self.name,"Ext Crews",prov.int_crewExt_pool[temp1]+prov.int_crewExt_pool[temp2],"Crew Pool",prov.int_crew_pool,self.int_CrewsRequested-self.int_Crews
                        self.int_CrewsDispatched=min(prov.int_crewExt_pool[temp1]+prov.int_crewExt_pool[temp2]+prov.int_crew_pool,self.int_CrewsRequested-self.int_Crews)
                        #print now(),self.name,"XXX Crews to dispatch:",self.int_CrewsDispatched
                    else:
                        #print now(),self.name," No Crews Available"
                        #There are no additional crews available so none dispatched
                        #Punishment for this?
                        self.int_CrewsDispatched=0
                        
                #print self.name,"XXXXXX",self.int_CrewsDispatched
                #Loop through to take the crews set to dispatch
                #If no local crews are available then try to send External 
                #crews if they are present.
                if self.int_CrewsDispatched>0:
                    if prov.int_crew_pool>0:
                        yield request,self,prov.serv_CrewTemp
                        for i in range(self.int_CrewsDispatched):
                            yield request,self,prov.serv_Crew1
                            #The Crew pool is adjusted to show the "used" crews
                            #Arena Assign 325
                            prov.int_crew_pool=prov.int_crew_pool - 1
                            #print now(),self.name,"ZZZ Crews to dispatch:",self.int_CrewsDispatched
                        yield release,self,prov.serv_CrewTemp
                        if self.int_Crews==0 and self.int_CrewsExt[temp1]==0 and self.int_CrewsExt[temp2]==0:
                            #Delay arrival of crews to fire
                            yield hold, self, float(delayCrews("crews")/24.0)
                        #Add the crews dispatched to the crews at fire
                        self.int_Crews=self.int_Crews+self.int_CrewsDispatched
                        #print self.name,self.int_Crews
                    if prov.int_crewExt_pool[temp1]>0:
                        sendCrew1=min(self.int_CrewsDispatched,prov.int_crewExt_pool[temp1])
                        yield request,self,prov.serv_CrewTemp
                        for i in range(sendCrew1):
                            yield request,self,prov.serv_Crew1Ext
                            prov.int_crewExt_pool[temp1] -=1
                        yield release,self,prov.serv_CrewTemp
                        if self.int_Crews==0 and self.int_CrewsExt[temp1]==0 and self.int_CrewsExt[temp2]==0:
                            yield hold,self,float(delayCrews("crews")/24.0)
                        self.int_CrewsExt[temp1]+=sendCrew1
                    if prov.int_crewExt_pool[temp2]>0:
                        sendCrew1=min(self.int_CrewsDispatched,prov.int_crewExt_pool[temp2])
                        yield request,self,prov.serv_CrewTemp
                        for i in range(sendCrew1):
                            yield request,self,prov.serv_Crew2Ext
                            prov.int_crewExt_pool[temp1] -=1
                        yield release,self,prov.serv_CrewTemp
                        if self.int_Crews==0 and self.int_CrewsExt[temp1]==0 and self.int_CrewsExt[temp2]==0:
                            yield hold,self,float(delayCrews("crews")/24.0)
                        self.int_CrewsExt[temp2]+=sendCrew1
                    
                #TYPE 2 CREWS
                if self.int_Crewtype2>=self.int_Crewtype2Requested:
                    self.int_Crewtype2Dispatched=0
                else:
                    if prov.int_crewtype2_pool>0:
                        ##print "There are some type 2's but not enough. Pool:",prov.int_crewtype2_pool
                        ##print now(),self.name,"There are Type 2's and checking what we can take"
                        self.int_Crewtype2Dispatched=min(prov.int_crewtype2_pool,self.int_Crewtype2Requested-self.int_Crewtype2)
                    else:
                        #print "No Crews Type 2 Available"
                        #Punishment?
                        self.Crewtype2Dispatched=0
                        
                if self.int_Crewtype2Dispatched>0:
                    yield request,self,prov.serv_Crew2Temp
                    for i in range(self.int_Crewtype2Dispatched):
                        yield request,self,prov.serv_Crew2
                        #The Type Crew 2 pool is adjusted to show the "used" type 2crews
                        #Arena Assign 331
                        prov.int_crewtype2_pool=prov.int_crewtype2_pool - 1
                    yield release,self,prov.serv_Crew2Temp
                    if self.int_Crewtype2==0:                 
                        yield hold, self, float(delayCrews("type2crews")/24.0)     
                    self.int_Crewtype2=self.int_Crewtype2 + self.int_Crewtype2Dispatched

           
                if self.int_Airtankers>=1:
                    ##print now(),self.name," We have airtanker(s) already"
                    self.int_AirtankersDispatched=0
                else:
                    ##print now(),self.name," Checking if any AirTankers avail"
                    if prov.int_airtanker_pool>=1:
                        ##print now()," ", self.name, "Getting Airtanker"
                        self.int_AirtankersDispatched=1
                    else:
                        self.int_AirtankersDispatched=0
                    if self.int_AirtankersDispatched>0:
                        yield request,self,prov.serv_Airtanker
                        prov.int_airtanker_pool=prov.int_airtanker_pool-1
                        self.int_Airtankers=1
                        yield hold, self, float(delayCrews("airtanker")/24.0)
                        
                if self.int_Helicopters>=1:
                    ##print now(),self.name," We have heli's"
                    self.int_HelicopterDispatched=0
                else:
                    if prov.int_helicopter_pool>=1:
                        self.int_HelicopterDispatched=1
                    else:
                        self.int_HelicopterDispatched=0
                    if self.int_HelicopterDispatched>0:
                        yield request,self,prov.serv_Helicopter
                        prov.int_helicopter_pool=prov.int_helicopter_pool-1
                        self.int_Helicopters=1
                

                if prov.name=="Ontario":
                    temp1=1
                    temp2=2 
                elif prov.name=="Prov2":
                    temp1=0
                    temp2=2
                else:
                    temp1=0
                    temp2=1
                if self.areThereResources(self.int_CrewsExt[temp1]+self.int_CrewsExt[temp2]):
                    #Get the fire intensity for the fire
                    self.dbl_FireIntensity=self.Modellogic_UserFunction(2,prov)
                    #print now(),self.name, "Fire Intensity: ", self.dbl_FireIntensity
                    if self.dbl_FireIntensity<=4000:
                        if prov.name=="Ontario":
                            temp1=1
                            temp2=2 
                        elif prov.name=="Prov2":
                            temp1=0
                            temp2=2
                        else:
                            temp1=0
                            temp2=1
                        self.intensityClassSuppression(self.int_Fuel,self.int_CrewsExt[temp1]+self.int_CrewsExt[temp2])
                        if self.supportSuppressFire(prov):
                            #print now(), self.name, " Fire Under Control"
                            self.bool_Burning=False
                            self.writeContainFireSizes(prov)
                            #print self.name,"Contain written"
                        else:
                            if self.nonSpreadDay(prov,ecoregion):
                                if self.fireExtinguished(prov,ecoregion):
                                    #print now( ), self.name, " Fire Out from nature not hard work"
                                    self.bool_Burning=False
                                    self.writeExtFireSizes(prov)
                            else:
                                #Update the Fire Size
                                #Assign 227 from Arena
                                self.dbl_Size=self.Modellogic_UserFunction(1,prov)
                                #Delay till the next day
                                yield hold, self, 1 
                                self.writeFireGrowth(prov)
                            
                    else:
                        ##print now(),self.name,"This is a very intense fire"
                        if self.nonSpreadDay(prov,ecoregion):
                            if self.fireExtinguished(prov,ecoregion):
                                #print now( ), self.name, " Fire Out from nature not hard work, even though it appears to be very intense"
                                self.bool_Burning=False
                                self.writeExtFireSizes(prov)
                        else:
                            #Update the Fire Size
                            #Assign 227 from Arena
                            self.size=self.Modellogic_UserFunction(1,prov)
                            #Delay till the next day
                            yield hold, self, 1  
                            self.writeFireGrowth(prov)
                                
                else:
                    #print now(),self.name,"No Resources at fire"
                    if self.nonSpreadDay(prov,ecoregion):
                        if self.fireExtinguished(prov,ecoregion):
                            #print now( ), self.name, "Fire Out with no firefighting"
                            self.bool_Burning=False
                            self.writeExtFireSizes(prov)
                    else:
                            #Update the Fire Size
                            #Assign 227 from Arena
                            self.dbl_Size=self.Modellogic_UserFunction(1,prov)
                            #Delay till the next day
                            yield hold, self, 1  
                            self.writeFireGrowth(prov)          
                #print now(),self.name,"XXX",int(floor(now())),prov.int_lastDayResourcesChecked
                #Check the resources for expected fires
                if int(floor(now()))>prov.int_lastDayResourcesChecked:
                    prov.ResourcesVsFires(prov.str_sourcePrediction,True)
                    #Check to see if the province made a request, if not then it can see about 
                    #sharing with other provinces. Theory here is that all provinces will check
                    #if they don't it is because they are all requesting so it doesn't matter
                    if prov.bool_madeRequest ==False:
                        if prov.name=="Ontario":
                            ##print now(),self.name,"Making Request of Prov2"
                            prov2.checkForRequests()
                            ##print now(),self.name,"Making Request of Prov3"
                            prov3.checkForRequests()
                        elif prov.name=="Prov2":
                            ontario.checkForRequests()
                            prov3.checkForRequests()
                        else:
                            ontario.checkForRequests()
                            prov2.checkForRequests()
                    if ontario.bool_madeRequest==False:
                        #sending from Ontario if there is anyone to send to
                        if ontario.ExtCrews[1][2]>0:
                            #sending to prov 2 now
                            #print now(),"XXXXXXXXXXSending From Ontario to Prov2"
                            yield request,self,ontario.serv_CrewTemp
                            for i in range (ontario.ExtCrews[1][2]):
                                yield request,self,ontario.serv_Crew1
                                ontario.int_crew_pool=ontario.int_crew_pool-1
                                prov2.int_crewExt_pool[0]=prov2.int_crewExt_pool[0]+1
                                #prov2.requestedCrews[1]=prov2.requestedCrews[1]-1
                            yield release,self,ontario.serv_CrewTemp
                            ontario.ExtCrews[1][2]=0
                        if ontario.ExtCrews[2][2]>0:
                            #Sending to prov3 now
                            #print now(),"XXXXXXXXXXSending From Ontario to Prov3"
                            yield request,self,ontario.serv_CrewTemp
                            for i in range (ontario.ExtCrews[2][2]):
                                yield request,self,ontario.serv_Crew1
                                ontario.int_crew_pool=ontario.int_crew_pool-1
                                prov3.int_crewExt_pool[0]=prov3.int_crewExt_pool[0]+1
                                #prov3.requestedCrews[1]=prov3.requestedCrews[1]-1
                            yield release,self,ontario.serv_CrewTemp
                            ontario.ExtCrews[2][2]=0
                    if prov2.bool_madeRequest==False:
                        #sending from prov2 if there is anyone to send to
                        if prov2.ExtCrews[1][2]>0:
                            #sending to ontario now
                            #print now(),"XXXXXXXXXXSending From Prov2 to Ontario"
                            yield request,self,prov2.serv_CrewTemp
                            for i in range (prov2.ExtCrews[0][2]):
                                yield request,self,prov2.serv_Crew1
                                prov2.int_crew_pool=prov2.int_crew_pool-1
                                ontario.int_crewExt_pool[1]=ontario.int_crewExt_pool[1]+1
                                #prov2.requestedCrews[1]=prov2.requestedCrews[1]-1
                            yield release,self,prov2.serv_CrewTemp
                            prov2.ExtCrews[1][2]=0
                        if prov2.ExtCrews[2][2]>0:
                            #Sending to prov3 now
                            #print now(),"XXXXXXXXXXSending From Prov2 to Prov3"
                            yield request,self,prov2.serv_CrewTemp
                            for i in range (prov2.ExtCrews[2][2]):
                                yield request,self,prov2.serv_Crew1
                                prov2.int_crew_pool=prov2.int_crew_pool-1
                                prov3.int_crewExt_pool[1]=prov3.int_crewExt_pool[1]+1
                                #prov3.requestedCrews[1]=prov2.requestedCrews[1]-1
                            yield release,self,prov2.serv_CrewTemp
                            prov2.ExtCrews[2][2]=0
                    if prov3.bool_madeRequest==False:
                        #sending from prov3 if there is anyone to send to
                        if prov3.ExtCrews[1][2]>0:
                            #sending to ontario now
                            #print now(),"XXXXXXXXXXSending From Prov3 to Ontario"
                            yield request,self,prov3.serv_CrewTemp
                            for i in range (prov3.ExtCrews[0][2]):
                                yield request,self,prov2.serv_Crew1
                                prov3.int_crew_pool=prov3.int_crew_pool-1
                                ontario.int_crewExt_pool[2]=ontario.int_crewExt_pool[2]+1
                                #prov2.requestedCrews[1]=prov2.requestedCrews[1]-1
                            yield release,self,prov3.serv_CrewTemp
                            prov3.ExtCrews[1][2]=0
                        if prov3.ExtCrews[2][2]>0:
                            #Sending to prov2 now
                            #print now(),"XXXXXXXXXXSending From Prov3 to Prov2"
                            yield request,self,prov3.serv_CrewTemp
                            for i in range (prov3.ExtCrews[2][2]):
                                yield request,self,prov3.serv_Crew1
                                prov3.int_crew_pool=prov3.int_crew_pool-1
                                prov2.int_crewExt_pool[2]=prov2.int_crewExt_pool[2]+1
                                #prov3.requestedCrews[1]=prov2.requestedCrews[1]-1
                            yield release,self,prov3.serv_CrewTemp
                            prov3.ExtCrews[2][2]=0
                    prov.int_lastDayResourcesChecked=int(floor(now()))
            
            
            #Need to loop to release all the resources that were used
            if self.int_Crews>0:
                #print now(),self.name, "Releasing all resources because FIRE OUT"
                for i in range(self.int_Crews):
                    yield release,self,prov.serv_Crew1
            if self.int_Crewtype2>0:
                for i in range(self.int_Crewtype2):
                    yield release,self,prov.serv_Crew2
            if self.int_Airtankers>0:
            #for i in range(self.int_Airtankers):
                yield release,self,prov.serv_Airtanker
            if self.int_Helicopters>0:
            #for i in range(self.int_Helicopters):
                yield release,self,prov.serv_Helicopter
            prov.int_crew_pool=prov.int_crew_pool + self.int_Crews
            prov.int_crewtype2_pool=prov.int_crewtype2_pool + self.int_Crewtype2
            prov.int_airtanker_pool=prov.int_airtanker_pool+1
            prov.int_helicopter_pool=prov.int_helicopter_pool+1
            temp1=0
            temp2=0
            if prov.name=="Ontario":
                temp1=1
                temp2=2 
            elif prov.name=="Prov2":
                temp1=0
                temp2=2
            else:
                temp1=0
                temp2=1
            #return the ext crews from the fire to the prov ext pool
            if self.int_CrewsExt[temp1]>0:
                prov.int_crewExt_pool[temp1]= prov.int_crewExt_pool[temp1] + self.int_CrewsExt[temp1]
            if self.int_CrewsExt[temp2]>0:
                prov.int_crewExt_pool[temp2]= prov.int_crewExt_pool[temp2] + self.int_CrewsExt[temp2]
            #print self.name,"DONE"
        else:
            #print now(),self.name,"Initial Attack Success"
            prov.int_IASuccess=prov.int_IASuccess+1
            #Check the resources for expected fires            
            if int(floor(now()))>prov.int_lastDayResourcesChecked:
                prov.ResourcesVsFires(prov.str_sourcePrediction,True)
                if prov.bool_madeRequest ==False:
                    #Check for other provinces, if the province hasn't made a request
                    prov.checkForRequests()
                prov.int_lastDayResourcesChecked=int(floor(now()))

        #Now that crews released we should check if any of the crews are EXT
        #if they are we need to check when they came and if after days to search
        #we should release them
        
        if prov.int_crewExt_pool>0:
            if now()>=prov.requestedCrews[0]+7:
                faketemp=""
                #print now(),self.name,"Releasing EXT Crews"
            
            
    
    #Check to see if there are resources applied to the fire, return TRUE if 
    #there are resources applied to the fire
    #Decide 55 from Arena
    def areThereResources(self,int_ExtCrews):
        if self.int_Helicopters+self.int_Airtankers+self.int_Crewtype2+self.int_Crews+int_ExtCrews>0:
            #print now(),self.name, " Resources present: C1:", self.int_Crews," C2:",self.int_Crewtype2," A:",self.int_Airtankers,"H: ",self.int_Helicopters
            return True
        else:
            #print now(),self.name, "No Resources"
            return False
            
    
    #Check to see what resources can work as the fire may be too intense
    #for crews/type2's to work
    #Decide 45 from Arena
    def calcNeededResources(self):
        #Get resources to battle that blaze
        ##print now(), self.name," Starting Resource Request"
        self.calcPerimeter()
        if self.dbl_Perimeter <= 4000:
            self.int_CrewsRequested=4
            self.int_Crewtype2Requested=2
        elif self.dbl_Perimeter <=6000:
            self.int_CrewsRequested=6
            self.int_Crewtype2Requested=3
        elif self.dbl_Perimeter <=11000:
            self.int_CrewsRequested= 11
            self.int_Crewtype2Requested=5
        elif self.dbl_Perimeter <=15000:
            self.int_CrewsRequested= 15
            self.int_Crewtype2Requested=6
        elif self.dbl_Perimeter <=17000:
            self.int_CrewsRequested= 18
            self.int_Crewtype2Requested=8
        elif self.dbl_Perimeter <=24000:
            self.int_CrewsRequested= 20
            self.int_Crewtype2Requested=10
        elif self.dbl_Perimeter > 24000:
            self.int_CrewsRequested= 23
            self.int_Crewtype2Requested=12
        else:
            self.int_CrewsRequested= 0
            self.int_Crewtype2Requested=0
               
    
    def calcPerimeter(self):
        #Calculate the Perimeter of the fire        
        self.dbl_Perimeter=3.1416 * ((self.dbl_HeadAdvance + self.dbl_BackAdvance)/2 + self.dbl_FlankAdvance)
    

        


#This is the FireSuppression portion of the model. This
#will check the intensity of the fire and determine the 
#resources involved and their ability to build a fireline
    def intensityClassSuppression(self,fuelnow,int_ExtCrews):
    #If the fire intensity is < 10 kW/m, then Type 1, Type 2, 
    #and Airtankers can all work at high levels of productivity 
    #on the fire.
        ##print now(),self.name,"Int:",self.dbl_FireIntensity,"Fuelnow:",fuelnow,"FirelinePer:",self.dbl_FirelinePerimeter
        ##print now(),self.name,"C1:",self.int_Crews,"C2:",self.int_Crewtype2,"A:",self.int_Airtankers,"H:",self.int_Helicopters
        if self.dbl_FireIntensity<10:
            if fuelnow==1 or fuelnow==3 or fuelnow==4 or fuelnow==5 or fuelnow==6:
                #161
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(56+56*random.betavariate(3.97,6.46))) + 8*60*(1*self.int_Crewtype2 * 610/(56+56*random.betavariate(3.97,6.46)))
            elif fuelnow==2:
                #162
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(80+68*random.betavariate(4.59,6.39)))+8*60*(1*self.int_Crewtype2 * 610/(80+68*random.betavariate(4.59,6.39)))
            elif fuelnow==8 or fuelnow==132 or fuelnow==133:
                #163
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(130+92*random.betavariate(4.7,6.17)))+8*60*(1*self.int_Crewtype2 * 610/(130+92*random.betavariate(4.7,6.17)))
            elif fuelnow==9:
                #164
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(95+77*random.betavariate(4.45,6.33)))+8*60*(1*self.int_Crewtype2 * 610/(95+77*random.betavariate(4.45,6.33)))
            elif fuelnow==12:
                #165
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(29+34*random.betavariate(4,6.68)))+ 8*60*(1*self.int_Crewtype2 * 610/(29+34*random.betavariate(4,6.68)))
            else:
                #fuel now is 131 or other
                #166
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(63+63*random.betavariate(4.24,6.52)))+8*60*(1*self.int_Crewtype2 * 610/(63+63*random.betavariate(4.24,6.52)))
        
            #Apply the efforts of airtankers
            if fuelnow==9 or fuelnow==12:
                #160
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 3870)
            else:
                #168
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 2880)
        #All three kinds of line building resources can also work on 
        #Class 2 fires    
        elif self.dbl_FireIntensity<500:
            if fuelnow==1 or fuelnow==3 or fuelnow==4 or fuelnow==5 or fuelnow==6:
                #170, which seems to be a copy of 161 but I have left this in case we need to change it
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(56+56*random.betavariate(3.97,6.46))) + 8*60*(1*self.int_Crewtype2 * 610/(56+56*random.betavariate(3.97,6.46)))        
            elif fuelnow==2:
                #171, copy of 162 again
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(80+68*random.betavariate(4.59,6.39)))+8*60*(1*self.int_Crewtype2 * 610/(80+68*random.betavariate(4.59,6.39)))
            elif fuelnow==8 or fuelnow==132 or fuelnow==133:
                #172-163
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(130+92*random.betavariate(4.7,6.17)))+8*60*(1*self.int_Crewtype2 * 610/(130+92*random.betavariate(4.7,6.17)))
            elif fuelnow==9:
                #173-164
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(95+77*random.betavariate(4.45,6.33)))+8*60*(1*self.int_Crewtype2 * 610/(95+77*random.betavariate(4.45,6.33)))
            elif fuelnow==12:
                #174-165
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(29+34*random.betavariate(4,6.68)))+ 8*60*(1*self.int_Crewtype2 * 610/(29+34*random.betavariate(4,6.68)))
            else:
                #fuel now is 131 or other
                #175-166
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(63+63*random.betavariate(4.24,6.52)))+8*60*(1*self.int_Crewtype2 * 610/(63+63*random.betavariate(4.24,6.52)))   
            
            #Apply the efforts of Airtankers
            if fuelnow==9 or fuelnow==12:
                #169
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 3480)
            else:
                #177
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 2490)
        #At intensity class 3, Type 2 Crews cannot be used.
        elif self.dbl_FireIntensity<2000:
            if fuelnow==1 or fuelnow==3 or fuelnow==4 or fuelnow==5 or fuelnow==6:
                #179
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(56+56*random.betavariate(3.97,6.46))) + 8*60*(0*self.int_Crewtype2 * 610/(56+56*random.betavariate(3.97,6.46)))        
            elif fuelnow==2:
                #180
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(80+68*random.betavariate(4.59,6.39)))+8*60*(0*self.int_Crewtype2 * 610/(80+68*random.betavariate(4.59,6.39)))
            elif fuelnow==8 or fuelnow==132 or fuelnow==133:
                #181
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(130+92*random.betavariate(4.7,6.17)))+8*60*(0*self.int_Crewtype2 * 610/(130+92*random.betavariate(4.7,6.17)))
            elif fuelnow==9:
                #182
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(95+77*random.betavariate(4.45,6.33)))+8*60*(0*self.int_Crewtype2 * 610/(95+77*random.betavariate(4.45,6.33)))
            elif fuelnow==12:
                #183
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(29+34*random.betavariate(4,6.68)))+ 8*60*(0*self.int_Crewtype2 * 610/(29+34*random.betavariate(4,6.68)))
            else:
                #fuel now is 131 or other
                #184
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + 8*60*((self.int_Crews + int_ExtCrews) * 610/(63+63*random.betavariate(4.24,6.52)))+8*60*(0*self.int_Crewtype2 * 610/(63+63*random.betavariate(4.24,6.52)))           
            #Apply the efforts of the Airtankers
            if fuelnow==9 or fuelnow==12:
                #178
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 2010)
            else:
                #186
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 990)
        #At Intensity Class 4, only airtankers are effective, and even
        #airtankers are not very effective.
        else:
            if fuelnow==9 or fuelnow==12:
                #187
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 990)
            else:
                #189
                self.dbl_FirelinePerimeter=self.dbl_FirelinePerimeter + (self.int_Airtankers * 10)
    

    
    
    def supportSuppressFire(self,prov):
        #Decide 47 from the Arena model
        #print now(),self.name,"Fireline:" ,self.dbl_FirelinePerimeter, " Threshold:", self.dbl_Perimeter*dbl_perim_contain_threshold
        if self.dbl_FirelinePerimeter >=self.dbl_Perimeter*dbl_perim_contain_threshold:
            return True
        else:
            return False

    
    def nonSpreadDay(self,prov,ecoregion):
        #Decide 84 from Arena
        temp=prov.getIndicator(floor(now()),3,ecoregion)
        #print now(),self.name,"ISI: ",temp, "Threshold: ",prov.dbl_isi_grow_threshold
        if temp<=prov.dbl_isi_grow_threshold:
            return True
        else:
            return False
    
    def fireExtinguished(self,prov,ecoregion):
        date=int(now())
        temp=prov.getIndicator(floor(now()),2,ecoregion)
        #print now(),"DMC for ",date+intFirstDay, "ECO: ",ecoregion,"is: ",temp
        if temp<=30:
            return True
        else:
            return False
        
    
    def writeFireGrowth(self,prov):
        #Fire Arrival time, size, fireintensity, crews, crew pool, 
        #fireline perim, perim, fuelnow,
        ##print "Fire Growth"
        f=open(str(sys.argv[3])+"\\"+prov.str_FireGrowth+str(int_year_simulated)+".csv",'a')
        temp=str(now())+","+str(self.dbl_ArrivalTime)+","+str(self.dbl_Size)+","+str(self.dbl_FireIntensity)+","+str(self.int_Crews)+","+str(prov.int_crew_pool)+","+str(self.dbl_FirelinePerimeter)+","+str(self.dbl_Perimeter)+","+str(self.int_Fuel)
        temp=str(temp)
        f.write(temp + '\n')
        f.close()
        
    def writeExtFireSizes(self,prov):
        #Fire Arrival time, day,size, realfinalsize, crews, crew pool, 
        #airtankers, airtanker pool, fireline perim,perim, fuelnow
        ##print "Ext Fire Size"
        f=open(str(sys.argv[3])+"\\"+prov.str_ExtFireSize+str(int_year_simulated)+".csv",'a')
        temp=str(now())+","+str(self.dbl_ArrivalTime)+",day,"+str(self.dbl_Size)+",realfinalsize,"+str(self.int_Crews)+","+str(prov.int_crew_pool)+","+str(self.int_Airtankers)+","+str(prov.int_airtanker_pool)+","+str(self.dbl_FirelinePerimeter)+","+str(self.dbl_Perimeter)+","+str(self.int_Fuel)
        temp=str(temp)
        f.write(temp + '\n')
        f.close()
        
    def writeContainFireSizes(self,prov):
        #Fire Arrival time, day,size, realfinalsize, crews, crew pool, 
        #airtankers, airtanker pool, fireline perim,perim, fuelnow
        ##print "Contain Fire Size"
        f=open(str(sys.argv[3])+"\\"+prov.str_ContainFireSize+str(int_year_simulated)+".csv",'a')
        temp=str(sys.argv[1])+","+str(now())+","+str(self.dbl_ArrivalTime)+",day,"+str(self.dbl_Size)+",realfinalsize,"+str(self.int_Crews)+","+str(prov.int_crew_pool)+","+str(self.int_Airtankers)+","+str(prov.int_airtanker_pool)+","+str(self.dbl_FirelinePerimeter)+","+str(self.dbl_Perimeter)+","+str(self.int_Fuel)
        temp=str(temp)
        f.write(temp + '\n')
        f.close()

    def writeFireSizes(self):
        #probEscape,unit0to1,fireline perim,perim,eco region, fuelnow
        #crew pool, airtankers,airtanker pool, fire arrival time
        #day, crews,size, realfinalsize
        print "fireSize"

    def recordLTG(self,prov):
        #ontario.dbl_LTGAreaBurned=ontario.dbl_LTGAreaBurned+self.dbl_Size
        prov.int_LightningFireCount +=1
    
    def recordPPL(self,prov):
        #ontario.dbl_PPLAreaBurned=ontario.dbl_PPLAreaBurned+self.dbl_Size
        prov.int_HumanFireCount +=1

    #This is the VBA from the Arena Model called via UF in that model
    def Modellogic_UserFunction(self,functionID,prov):
        #set temp values up for fire entities
        nHeadAdvance=self.dbl_HeadAdvance
        nBackAdvance=self.dbl_BackAdvance 
        nFlankAdvance=self.dbl_FlankAdvance
        nSize=self.dbl_Size
        nFirelinePerimeter=self.dbl_FirelinePerimeter
        nPerimeter=self.dbl_Perimeter


        #getting the weather indices
        nFFMC=0.0
        nWS=0.0
        nBUI=0.0
        nISI=0.0
        nFuel=0.0

        #nFFMC=self.dbl_ffmcnow
        #nWS=self.dbl_wsnow
        #nBUI=self.dbl_buinow
        #nISI=self.dbl_isinow
        #nFuel=10.0 #FUEL NOW
        #Testing
        nFFMC=float(prov.getIndicator(floor(now()),1,self.int_ecoregion))
        nWS=float(prov.getIndicator(floor(now()),5,self.int_ecoregion))
        nBUI=float(prov.getIndicator(floor(now()),4,self.int_ecoregion))
        nISI=float(prov.getIndicator(floor(now()),3,self.int_ecoregion))
        nFuel=self.int_Fuel

    
        #set the weather indicies to acceptable values if they
        #lie outside of the correct values
        #FFMC cannot be higher than 100
        if nFFMC>=100:
            nFFMC=99.9
        #If BUI is 0 then set it to 1
        if nBUI==0:
            nBUI=1
        #ISI cannot be negative
        if nISI<0:
            nISI=0

        #Set constants for rate of spread calculation.  Load them all in at once
        #First, the buildup index constants ('bui0' and 'q' values for the buildup factor)
            
        bui0_c1 = 72#
        buiq_c1 = 0.9
        bui0_c2 = 64#
        buiq_c2 = 0.7
        bui0_c3 = 62#
        buiq_c3 = 0.75
        bui0_c4 = 66#
        buiq_c4 = 0.8
        bui0_c5 = 56#
        buiq_c5 = 0.8
        bui0_c6 = 62#
        buiq_c6 = 0.8
        bui0_c7 = 106#
        buiq_c7 = 0.85
        bui0_d1 = 32#
        buiq_d1 = 0.9
        bui0_m1 = 50#
        buiq_m1 = 0.8
        bui0_m2 = 50#
        buiq_m2 = 0.8
        bui0_m3 = 50#
        buiq_m3 = 0.8
        bui0_m4 = 50#
        buiq_m4 = 0.8
        bui0_s1 = 38#
        buiq_s1 = 0.75
        bui0_s2 = 63#
        buiq_s2 = 0.75
        bui0_s3 = 31#
        buiq_s3 = 0.75
        bui0_o1a = 1#
        buiq_o1a = 1
        bui0_o1b = 1#
        buiq_o1b = 1
        
        
        #These are the values of a, b, and c for the rsi_temp calculation (see
        #Forestry Canada Fire Danger Group Information Report ST-X-3: "Development and Structure
        #of the Canadian Forest Fire Behavior Prediction System".
        
        aRSI_c1 = 90
        aRSI_c2 = 110
        aRSI_c3 = 110
        aRSI_c4 = 110
        aRSI_c5 = 30
        aRSI_c6 = 30
        aRSI_c7 = 45
        aRSI_d1 = 30
        aRSI_s1 = 75
        aRSI_s2 = 40
        aRSI_s3 = 55
        aRSI_o1a = 190
        aRSI_o1b = 250
            
        bRSI_c1 = 0.0649
        bRSI_c2 = 0.0282
        bRSI_c3 = 0.0444
        bRSI_c4 = 0.0293
        bRSI_c5 = 0.0697
        bRSI_c6 = 0.08
        bRSI_c7 = 0.0305
        bRSI_d1 = 0.0232
        bRSI_s1 = 0.0297
        bRSI_s2 = 0.0438
        bRSI_s3 = 0.0829
        bRSI_o1a = 0.031
        bRSI_o1b = 0.035
            
        cRSI_c1 = 4.5
        cRSI_c2 = 1.5
        cRSI_c3 = 3#
        cRSI_c4 = 1.5
        cRSI_c5 = 4#
        cRSI_c6 = 3#
        cRSI_c7 = 2#
        cRSI_d1 = 1.6
        cRSI_s1 = 1.3
        cRSI_s2 = 1.7
        cRSI_s3 = 3.2
        cRSI_o1a = 1.4
        cRSI_o1b = 1.7
     
        #The length of the burning day is 6 hours
        BurningDay=6
        #The mysterious 'Rate of Spread Reduction Factor'
        SpreadReductionFactor = 1

        #Some variables for the rate of spread calculation
        Buildup=0.0
        Moisture=0.0
        FFMCFactor=0.0
        BackFireRate=0.0
        BackISI=0.0
        RSITemp=0.0
        LengthBreadthRatio=0.0
            
        #Rates of Spread and advance of the fire
        BackROS=0.0
        HeadROS=0.0
        FlankROS=0.0
        HeadAdvance=0.0
        BackAdvance=0.0
        FlankAdvance=0.0
            
        dCreateTime =0.0
        dCurrentTime=0.0

        #Moisture Factor
        Moisture = 147.2 * (101 - nFFMC) / (59.5 + nFFMC)
        #FFMC Factor
        FFMCFactor = 91.9 * (exp(-0.1386 * Moisture)) * (1 + pow(Moisture,5.31) / (49300000))
        #Back Fire Rate
        BackFireRate = exp(-0.05039 * nWS)
        #Back ISI
        BackISI = BackFireRate * FFMCFactor * 0.208

        if nFuel==1:
            Buildup = exp(50 * log(buiq_c1) * ((1 / nBUI) - (1 / bui0_c1)))
            RSITemp = aRSI_c1 * pow((1 - exp(-bRSI_c1 * nISI)),cRSI_c1)
            BackROS = Buildup * aRSI_c1 * pow((1 - exp(-bRSI_c1 * BackISI)),cRSI_c1)
        elif nFuel==2:
            Buildup = exp(50 * log(buiq_c2) * ((1 / nBUI) - (1 / bui0_c2)))
            RSITemp = aRSI_c2 * pow((1 - exp(-bRSI_c2 * nISI)),cRSI_c2)
            BackROS = Buildup * aRSI_c2 * pow((1 - exp(-bRSI_c2 * BackISI)),cRSI_c2)
        elif nFuel==3:
            Buildup = exp(50 * log(buiq_c3) * ((1 / nBUI) - (1 / bui0_c3)))
            RSITemp = aRSI_c3 * pow((1 - exp(-bRSI_c3 * nISI)),cRSI_c3)
            BackROS = Buildup * aRSI_c3 * pow((1 - exp(-bRSI_c3 * BackISI)),cRSI_c3)
        elif nFuel==4:
            Buildup = exp(50 * log(buiq_c4) * ((1 / nBUI) - (1 / bui0_c4)))
            RSITemp = aRSI_c4 * pow((1 - exp(-bRSI_c4 * nISI)),cRSI_c4)
            BackROS = Buildup * aRSI_c4 * pow((1 - exp(-bRSI_c4 * BackISI)),cRSI_c4)
        elif nFuel==5:
            Buildup = exp(50 * log(buiq_c5) * ((1 / nBUI) - (1 / bui0_c5)))
            RSITemp = aRSI_c5 * pow((1 - exp(-bRSI_c5 * nISI)),cRSI_c5)
            BackROS = Buildup * aRSI_c5 * pow((1 - exp(-bRSI_c5 * BackISI)),cRSI_c5)
        elif nFuel==6:
            Buildup = exp(50 * log(buiq_c6) * ((1 / nBUI) - (1 / bui0_c6)))
            RSITemp = aRSI_c6 * pow((1 - exp(-bRSI_c6 * nISI)),cRSI_c6)
            BackROS = Buildup * aRSI_c6 * pow((1 - exp(-bRSI_c6 * BackISI)),cRSI_c6)
        elif nFuel==7:
            Buildup = exp(50 * log(buiq_c7) * ((1 / nBUI) - (1 / bui0_c7)))
            RSITemp = aRSI_c7 * pow((1 - exp(-bRSI_c7 * nISI)),cRSI_c7)
            BackROS = Buildup * aRSI_c7 * pow((1 - exp(-bRSI_c7 * BackISI)),cRSI_c7)
        elif nFuel==8:
            Buildup = exp(50 * log(buiq_d1) * ((1 / nBUI) - (1 / bui0_d1)))
            RSITemp = aRSI_d1 * pow((1 - exp(-bRSI_d1 * nISI)),cRSI_d1)
            BackROS = Buildup * aRSI_d1 * pow((1 - exp(-bRSI_d1 * BackISI)),cRSI_d1)
        elif nFuel==131:
            Buildup = exp(50 * log(buiq_m1) * ((1 / nBUI) - (1 / bui0_m1)))
            #I'm using the a,b,c, for conifers because I can't find mixedwood values right now
            RSITemp = aRSI_c1 * pow((1 - exp(-bRSI_c1 * nISI)),cRSI_c1)
            BackROS = Buildup * aRSI_c1 * pow((1 - exp(-bRSI_c1 * BackISI)),cRSI_c1)
            #RSITemp = aRSI_c2 * (1 - exp(-bRSI_c2 * nISI)) ^ cRSI_c2
            #BackROS = Buildup * aRSI_c2 * (1 - exp(-bRSI_c2 * BackISI)) ^ cRSI_c2
            #Why is this different from the first one?
            #Case 131
            #    Buildup = exp(50 * log(buiq_m2) * ((1 / nBUI) - (1 / bui0_m2)))
        elif nFuel==132:
            Buildup = exp(50 * log(buiq_m3) * ((1 / nBUI) - (1 / bui0_m3)))
            RSITemp = aRSI_c3 * pow((1 - exp(-bRSI_c3 * nISI)),cRSI_c3)
            BackROS = Buildup * aRSI_c3 * pow((1 - exp(-bRSI_c3 * BackISI)),cRSI_c3)
        elif nFuel==133:
            Buildup = exp(50 * log(buiq_m4) * ((1 / nBUI) - (1 / bui0_m4)))
            RSITemp = aRSI_c4 * pow((1 - exp(-bRSI_c4 * nISI)),cRSI_c4)
            BackROS = Buildup * aRSI_c4 * pow((1 - exp(-bRSI_c4 * BackISI)),cRSI_c4)
        elif nFuel==9:
            Buildup = exp(50 * log(buiq_s1) * ((1 / nBUI) - (1 / bui0_s1)))
            RSITemp = aRSI_s1 * pow((1 - exp(-bRSI_s1 * nISI)),cRSI_s1)
            BackROS = Buildup * aRSI_s1 * pow((1 - exp(-bRSI_s1 * BackISI)),cRSI_s1)
        elif nFuel==10:
            Buildup = exp(50 * log(buiq_s2) * ((1 / nBUI) - (1 / bui0_s2)))
            RSITemp = aRSI_s2 * pow((1 - exp(-bRSI_s2 * nISI)),cRSI_s2)
            BackROS = Buildup * aRSI_s2 * pow((1 - exp(-bRSI_s2 * BackISI)),cRSI_s2)
        elif nFuel==11:
            Buildup = exp(50 * log(buiq_s3) * ((1 / nBUI) - (1 / bui0_s3)))
            RSITemp = aRSI_s3 * pow((1 - exp(-bRSI_s3 * nISI)),cRSI_s3)
            BackROS = Buildup * aRSI_s3 * pow((1 - exp(-bRSI_s3 * BackISI)),cRSI_s3)
        elif nFuel==12:
            Buildup = exp(50 * log(buiq_o1a) * ((1 / nBUI) - (1 / bui0_o1a)))
            RSITemp = aRSI_o1a * pow((1 - exp(-bRSI_o1a * nISI)),cRSI_o1a)
            BackROS = Buildup * aRSI_o1a * pow((1 - exp(-bRSI_o1a * BackISI)),cRSI_o1a)
        elif nFuel==52:
            Buildup = exp(50 * log(buiq_o1b) * ((1 / nBUI) - (1 / bui0_o1b)))
            RSITemp = aRSI_o1b * pow((1 - exp(-bRSI_o1b * nISI)),cRSI_o1b)
            BackROS = Buildup * aRSI_o1b * pow((1 - exp(-bRSI_o1b * BackISI)),cRSI_o1b)
        else:
            print "Invalid Fuel Type Number Code"


        #Length Breadth Ratio
        LengthBreadthRatio = 1 + 8.729 * pow((1 - exp(-0.03 * nWS)),2.155)
        
        #Rates of Spread
        HeadROS = RSITemp * Buildup
        FlankROS = (HeadROS + BackROS) / (2 * LengthBreadthRatio)
        
        #Incorporate the Spread Reduction Factor
        HeadROS = HeadROS * SpreadReductionFactor
        FlankROS = FlankROS * SpreadReductionFactor
        BackROS = BackROS * SpreadReductionFactor
                                                                              
        #FUEL CONSUMPTION CALCULATIONS
        
        #These are the constants for the crown fuel consumption calculation
        
        CBH_c1 = 2# 'Crown Base Height in m
        CBH_c2 = 3#
        CBH_c3 = 8#
        CBH_c4 = 4#
        CBH_c5 = 18#
        CBH_c6 = 7#
        CBH_c7 = 10#
        CBH_m1 = 6#
        CBH_m2 = 6#
        CBH_m3 = 6#
        CBH_m4 = 6#
        
        CFL_c1 = 0.75 #Crown Fuel Load in kg/m2
        CFL_c2 = 0.8
        CFL_c3 = 1.15
        CFL_c4 = 1.2
        CFL_c5 = 1.2
        CFL_c6 = 1.8
        CFL_c7 = 0.5
        CFL_m1 = 0.8
        CFL_m2 = 0.8
        CFL_m3 = 0.8
        CFL_m4 = 0.8
        
        #Consumption Variables
        FMC=0.0
        SFC=0.0
        CSI=0.0
        RSO=0.0
        CFB=0.0
        CFL=0.0
        CFC=0.0
        TFC=0.0
        FireIntensity=0.0 #Fire Intensity in kW/m
        
        
        # Foliar Moisture Content
        FMC = 97 #General estimate, can also calculate it


        if nFuel==1:
            if nFFMC > 84:
                SFC = 0.75 + 0.75 * pow((1 - exp(-0.23 * (nFFMC - 84))),0.5)
            else:
                SFC = 0.75 - 0.75 * pow((1 - exp(0.23 * (nFFMC - 84))),0.5)
            
            CSI = (0.001 * pow(CBH_c1,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c1
        elif nFuel==2:
            SFC = 5 * (1 - exp(-0.0115 * nBUI))
            CSI = (0.001 * pow(CBH_c2,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c2
        elif nFuel==3:
            SFC = 5 * pow((1 - exp(-0.0164 * nBUI)),2.24)
            CSI = (0.001 * pow(CBH_c3,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c3
        elif nFuel==4:
            SFC = 5 * pow((1 - exp(-0.0164 * nBUI)),2.24)
            CSI = (0.001 * pow(CBH_c4,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c4
        elif nFuel==5:
            SFC = 5 * pow((1 - exp(-0.0149 * nBUI)),2.48)
            CSI = (0.001 * pow(CBH_c5,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c5
        elif nFuel==6:
            SFC = 5 * pow((1 - exp(-0.0149 * nBUI)),2.48)
            CSI = (0.001 * pow(CBH_c6,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c6
        elif nFuel==7:
            SFC = 1.5 * (1 - exp(-0.0201 * nBUI)) + 2 * (1 - exp(-0.104 * (nFFMC - 70)))
            CSI = (0.001 * pow(CBH_c7,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_c7
        elif nFuel==8:
            SFC = 1.5 * (1 - exp(-0.0183 * nBUI))
            #Make Crown fraction burned and load zero for future calcs
            CFB = 1
            CFL = 0
            #I'm using the a,b,c, for conifers because I can't find mixedwood values right now
        elif nFuel==131:
            RSITemp = aRSI_c1 * pow((1 - exp(-bRSI_c1 * nISI)),cRSI_c1)
            BackROS = Buildup * aRSI_c1 * pow((1 - exp(-bRSI_c1 * BackISI)),cRSI_c1)
            SFC = 2.5 * (1 - exp(-0.0115 * nBUI)) + 0.75 * (1 - exp(-0.0183 * nBUI))
            CSI = (0.001 * pow(CBH_m1,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_m1
            #Case 131
            #RSITemp = aRSI_c2 * (1 - exp(-bRSI_c2 * nISI)) ^ cRSI_c2
            #BackROS = Buildup * aRSI_c2 * (1 - exp(-bRSI_c2 * BackISI)) ^ cRSI_c2
        elif nFuel==132:
            SFC = 3.75 * (1 - exp(-0.0115 * nBUI)) + 0.5 * (1 - exp(-0.0183 * nBUI))
            CSI = (0.001 * pow(CBH_m2,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
        
            CFL = CFL_m2
        elif nFuel==133:
            SFC = 5 * (1 - exp(-0.0115 * nBUI))
            CSI = (0.001 * pow(CBH_m3,1.5)) * pow((460 + 25.9 * FMC),1.5)
            RSO = CSI / (300 * SFC)
            if RSO > HeadROS:
                CFB = 0
            else:
                CFB = 1 - exp(-0.23 * (HeadROS - RSO))
            
            CFL = CFL_m3
        elif nFuel==9:
            SFC = 4 * (1 - exp(-0.025 * nBUI)) + 4 * (1 - exp(-0.034 * nBUI))
            #Make Crown fraction burned and load zero for future calcs
            CFB = 1
            CFL = 0
        elif nFuel==10:
            SFC = 10 * (1 - exp(-0.013 * nBUI)) + 6 * (1 - exp(-0.06 * nBUI))
            #Make Crown fraction burned and load zero for future calcs
            CFB = 1
            CFL = 0
        elif nFuel==11:
            SFC = 12 * (1 - exp(-0.0166 * nBUI)) + 20 * (1 - exp(-0.021 * nBUI))
            #Make Crown fraction burned and load zero for future calcs
            CFB = 1
            CFL = 0
        elif nFuel==12:
            SFC = 0.3 #that's the standard Grass Fuel Load (GFL)
            #Make Crown fraction burned and load zero for future calcs
            CFB = 1
            CFL = 0
        elif nFuel==52:
            SFC = 0.3 #estimated GFL
            #Make Crown fraction burned and load zero for future calcs
            CFB = 1
            CFL = 0
        else:
            print "Invalid Fuel Type Number Code"


        #Crown Fuel Consumption
        CFC = CFL * CFB
        
        #Total Fuel Consumption
        TFC = SFC + CFC
        
        #Fire intensity
        FireIntensity = 300 * TFC * HeadROS
        
        #Advance of the Fire
        HeadAdvance = nHeadAdvance + HeadROS * BurningDay * 60#
        BackAdvance = nBackAdvance + BackROS * BurningDay * 60#
        FlankAdvance = nFlankAdvance + FlankROS * BurningDay * 60#

        #Nonfireline and fireline-modified perimeters and areas
        FreePerimeterPrev=0.0
        FreePerimeter=0.0
        Perimeter=0.0
        FreeAreaBurnedPrev=0.0
        FreeAreaBurned=0.0
        AreaBurned=0.0
        #    'Dim MConstantPrev, MConstant As Double
        
        #Calculate them previous round
        #MConstantPrev = ((nHeadAdvance + nBackAdvance) * 0.5 - nFlankAdvance) / ((nHeadAdvance + nBackAdvance) * 0.5 + nFlankAdvance)
        
        FreePerimeterPrev = 3.1416 * ((nHeadAdvance + nBackAdvance) / 2 + nFlankAdvance)
        FreeAreaBurnedPrev = (nHeadAdvance + nBackAdvance) * 0.5 * nFlankAdvance * 3.1416 * 0.0001
        
        #Calculate them this round
        #MConstant = ((HeadAdvance + BackAdvance) * 0.5 - FlankAdvance) / ((HeadAdvance + BackAdvance) * 0.5 + FlankAdvance)
        FreePerimeter = 3.1416 * ((HeadAdvance + BackAdvance) / 2 + FlankAdvance)
        FreeAreaBurned = (HeadAdvance + BackAdvance) * 0.5 * FlankAdvance * 3.1416 * 0.0001

        #Calculate the suppression-adjusted area burned - comment this out unless you want Whitecourt mod
        AreaBurned = nSize + (1 - (nFirelinePerimeter / FreePerimeterPrev)) * (FreeAreaBurned - FreeAreaBurnedPrev)
        
        #The perimeter is calculated analogously - comment this out unless you want Whitecourt mod
        Perimeter = (1 - (nFirelinePerimeter / FreePerimeterPrev)) * (FreePerimeter - FreePerimeterPrev)

    
        if functionID==1:
            #Write a new value to these Attributes
            self.dbl_HeadAdvance = HeadAdvance
            self.dbl_BackAdvance = BackAdvance
            self.dbl_FlankAdvance = FlankAdvance
            self.dbl_Perimeter = FreePerimeter
            
            return AreaBurned   #Trying out the Whitecourt mod
            #Modellogic_UserFunction = FreeAreaBurned   (commented out because of Whitecourt mod)
        elif functionID==2:
            return FireIntensity
        else:
            print "User Function should be 1 for Area Burned Calc or 2 for Fire Intensity Calc"

#end of Fire



#Creating class for the provinces
class Province:
    #'Common base class for all employees'
    int_ProvCount = 0
    def __init__(self, name, crewPool,crew2Pool,crew2SecondPool,airTanker,helicopter):
        #Many variables for the province, all taken from the Arena version .28
        self.name = name
        Province.int_ProvCount += 1
        self.int_HumanFireCount=0
        self.int_LightningFireCount=0
        self.dbl_LTGAreaBurned=0.0
        self.dbl_PPLAreaBurned=0.0
        self.dbl_area_burned=0.0
        self.int_crew_pool=crewPool
        self.int_crewExt_pool=[0,0,0]
        self.int_airtanker_pool=airTanker
        self.int_crewtype2_pool=crew2Pool
        self.int_crewtype2second_pool=crew2SecondPool
        self.int_helicopter_pool=helicopter
        self.dbl_ffmcnow=0.0
        self.dbl_dmcnow=0.0
        self.dbl_isinow=2.0
        self.dbl_buinow=0.0
        self.dbl_wsnow=0.0
        self.dbl_probofescape_large=1.01
        self.dbl_probofescape_small=0.0
        self.dbl_provload=2.0
        self.dbl_sum_sizes=0.0
        self.dbl_isi_grow_threshold=7.5
        self.int_ecoregion=901
        #Output Files
        self.str_ExtFireSize=name+" Ext Fire Size.txt"
        self.str_ContainFireSize=name+" Contain Fire Size.txt"
        self.str_FireGrowth=name+" Fire Growth.txt"
        self.str_FireSizes=name+" Fire Sizes.txt"
        self.int_daysToCheck=7
        self.int_lastDayResourcesChecked=-1
        self.int_FiresForDaysToCheck=[]
        for i in range(0,7):
            self.int_FiresForDaysToCheck.append(0)
        #sys.argv[5]
        #2 means FWI
        #1 means count
        self.str_sourcePrediction=int(sys.argv[5])
        self.str_responsePrediction=int(sys.argv[5])
        self.int_EscapedFires=0
        self.int_IASuccess=0
        self.EcoZones=[]
        #0 Date requested
        #1 Amount requested
        self.requestedCrews=[0,0]
        self.bool_madeRequest=False
        #Each province has a 3x3 matrix 
        #First option is the province, 0- Ontario,1-Prov2,3-Prov3
        #Second Date, sent or recieved 
        #Third Amount sent or recieved
        #Last is amount to send, used to add in case of crews already sent/received
        self.ExtCrews=[[0,0,0],[0,0,0],[0,0,0]]
        self.intFirstDay=0
        self.weatherdata=[]
        self.firedata=[]
        self.fires = []
        #Creating the servers to fight the fires
        #Crews: serv_crew1, serv_crew2
        #AirTankers: serv_airTankers
        #Helicopters: serv_helicopters
        self.serv_Crew1 = Resource(capacity=crewPool,name='serv_Crew1',unitName='Crew')
        self.serv_Crew2 = Resource(capacity=crew2Pool,name='serv_Crew2',unitName='Crew2')
        self.serv_Airtanker = Resource(capacity=airTanker,name='serv_Airtanker',unitName='Airtanker')
        self.serv_Helicopter = Resource(capacity=helicopter,name='serv_Helicopter',unitName='Helicopter')
        self.serv_Crew1Ext = Resource(capacity=crewPool,name='serv_Crew1Ext',unitName='Crew')
        self.serv_Crew2Ext = Resource(capacity=crewPool,name='serv_Crew2Ext',unitName='Crew')
        #In order to eliminate the chance for a syncing error with multiple crew requests
        self.serv_CrewTemp = Resource(capacity=1,name='serv_CrewTemp',unitName='Crew')
        self.serv_Crew2Temp = Resource(capacity=1,name='serv_Crew2Temp',unitName='Crew2')

    
    #Read in the weatherdata, daily for each region
    #ExcelDate,
    #FFMC90, DMC90, ISI90, BUI90, WS90
    #FFMC91, DMC91, ISI91, BUI91, WS91
    #FFMC92, DMC92, ISI92, BUI92, WS92
    #FFMC93, DMC93, ISI93, BUI93, WS93
    #FFMC94, DMC94, ISI94, BUI94, WS94
    #FFMC95, DMC95, ISI95, BUI95, WS95
    #FFMC96, DMC96, ISI96, BUI96, WS96
    #FFMC97, DMC97, ISI97, BUI97, WS97
    #FFMC98, DMC98, ISI98, BUI98, WS98
    def importWeatherData(self,fileToOpen):
        #weatherdata = readInData(csvlist[0][3].rstrip(),"txt")
        if fileToOpen[-3:]=="txt":
            self.weatherdata = readInData(fileToOpen,"txt")
        else:
            self.weatherdata = readInData(fileToOpen,"csv")
            
    def importFireData(self,fileToOpen):
        if fileToOpen[-3:]=="txt":
            self.firedata = readInData(fileToOpen,"txt")
        else:
            self.firedata = readInData(fileToOpen,"csv")
        smallest = min(self.firedata, key=lambda L: L[0])
        #get rid of scientific notation 
        #on fire data
        try:
            self.intFirstDay=int(float(self.firedata[0][0]))
        except:
            self.intFirstDay=int(self.firedata[0][0])
        i=0
        for row in self.firedata:
            #convert the fire arrival date to a value not in scientific notation
            try:
                row[0]=int(float(row[0]))
            except:
                row[0]=int(row[0])
            #need to bring the date to a lower value
            #so that we aren't waiting 33726 seconds before
            #having a fire start
            #converting the fire arrival date to a value in simpy value
            row[0]=float(row[0]-self.intFirstDay)
            #converting the fire arrival time
            row[1]=float(row[1])
            #converting fire prov load
            row[2]=float(row[2])
            #converting fuelnow
            row[3]=float(row[3])
            #converting EcoRegion
            row[4]=int(float(row[4]))
            #converting the cause (1- LGHT, 2-Human)
            row[5]=int(float(row[5]))
            self.fires.append(Fire("{0}fire{1}".format(self.name,i)))
            activate(self.fires[i],self.fires[i].fireSpotted(self,row[2],row[3],row[4],row[5]),at=row[0])
            i=i+1    
        
    
    #Want to get the WSI from the weather data
    #Pass the province-self
    #intDate is the row in the array, likely to be now()-the first number in the data table
    #intType is which indicator 1-FFMC,2-DMC,3-ISI,4-BUI,5-WS
    #EcoRegion is the region the fire is taking place in
    #This replaces Decide 40 from the arena model
    def getIndicator(self,intDate,intType,intEcoRegion):
        intAddHowManyFives=0
        intCol=0
        if intEcoRegion==90:
            intAddHowManyFives=0
        elif intEcoRegion==91:
            intAddHowManyFives=1
        elif intEcoRegion==93:
            intAddHowManyFives=2
        elif intEcoRegion==94:
            intAddHowManyFives=3
        elif intEcoRegion==96:
            intAddHowManyFives=4
        elif intEcoRegion==97:
            intAddHowManyFives=5
        elif intEcoRegion==98:
            intAddHowManyFives=6
        else:
            intAddHowManyFives= 0
            ##print "INVALID ECOREGION:", intEcoRegion, " Requested for ", self.name, "on ", intDate, "for type: ",intType
        ##print intDate
        ##print (5*intAddHowManyFives)+int(intType)
        ##print now(), " ", self.name, "DMC found: ",self.weatherdata[int(intDate)][(5*intAddHowManyFives)+int(intType)]
        return self.weatherdata[min(int(intDate),len(self.weatherdata)-1)][(5*intAddHowManyFives)+int(intType)]
    
    def convertType(self,strEcoRegion):
        if strEcoRegion=="7" or strEcoRegion=="31" or strEcoRegion=="47" or strEcoRegion=="72" or strEcoRegion=="72" or strEcoRegion=="73" or strEcoRegion=="74" or strEcoRegion=="75" or strEcoRegion=="76" or strEcoRegion=="77" or strEcoRegion=="78" or strEcoRegion=="70" or strEcoRegion=="71":
            return "217"
        elif strEcoRegion=="100" or strEcoRegion=="101" or strEcoRegion=="103":
            return "96"
        elif strEcoRegion=="88" or strEcoRegion=="89":
            return "901"
        elif strEcoRegion=="99":
            return "97"
        elif strEcoRegion=="148" or strEcoRegion=="152" or strEcoRegion=="153" or strEcoRegion=="155" or strEcoRegion=="156" or strEcoRegion=="161" or strEcoRegion=="162" or strEcoRegion=="163" or strEcoRegion=="164" or strEcoRegion=="181":
            return "94"
        else:
            return strEcoRegion
    
    def getFiresFromWeather(self,theDate):
        #Read the indicies for each of the defined known indicies in Ontario
        #90,91,93,94,96,97,98
        theZones=[90,91,93,94,96,97,98]
        firesPerZone=[0,0,0,0,0,0,0]
        fireTotal=0
        i=0        
        
        for days in fireInOntario:
            if int(days[0])-intFirstDay==theDate:
                i=0
                for ecoZone in theZones:
                    ## print ecoZone,days[i*7+1],days[i*7+2]
                    ## temp=raw_input("Hi")
                    firesPerZone[i]=self.getFires(ecoZone,days[i*7+1],days[i*7+2])
                    i+=1
                break
        #print firesPerZone,"FIRES PER ZONE",self.name,theDate
        #each zone now has a number of fires expected
        
        
        i=0

        for eco in theZones:
            for provEco in self.EcoZones:
                if provEco==eco:
                    fireTotal=fireTotal+firesPerZone[i]
            i+=1
            
        #print fireTotal,"FIRES Per Prov",self.name,theDate
        return fireTotal
                        
                
    def getFires(self,intEco,FFMCVal,DMCVal):
        i=0.0        
        intEco=self.convertType(intEco)
        fieldInd=self.getFiresIndex(intEco)
        fieldInd=fieldInd*7+1
        listOfIndex=[]
        total=0.0
        FFMCVal=float(FFMCVal)
        DMCVal=float(DMCVal)
        #Need to loop through the days to find weather indicies (FFMC and DMC) and see the expected
        #fires(human and lightning caused), averaging all the 
        while len(listOfIndex)==0:
            for days in fireInOntario:
                if days[0]!="Date":
                    if FFMCVal-i*0.1<=float(days[fieldInd])<=FFMCVal+i*0.1 and DMCVal-i*0.1<=float(days[fieldInd+1])<=DMCVal+i*0.5:
                        #Get the total number of fires that meet the FFMC ratings for a given day
                        ## print fieldInd,days[fieldInd+5],days[fieldInd+6]
                        ## temp= raw_input("Enter something: ")
                        listOfIndex.append(days[fieldInd+5]+days[fieldInd+5])
                if len(listOfIndex)>=10:
                    break
                i+=1.0
        #We now have at least one item in the list
        total=0
        for i in range (0,len(listOfIndex)):
            total=total+int(listOfIndex[i])
        total=int(total/len(listOfIndex))    
        return total
                
    def getFiresIndex(self,intEco):
        if intEco==90 or intEco==901 or intEco==902:
            return 0
        elif intEco ==91:
            return 1
        elif intEco==93:
            return 2
        elif intEco==94:
            return 3
        elif intEco==96:
            return 4
        elif intEco==97:
            return 5
        else:
            return 6
    
    def ResourcesVsFires(self,str_firePredictionType,bool_Request):
        #print now(),self.name,"Checking Resource Levels vs expected fires"
        i=0
        int_reqCrews=0
        sumOfNumOfFires=0

        numOfFires=list(self.expectedFires(int(floor(now())),self.int_daysToCheck,str_firePredictionType))
        for i in range(0,self.int_daysToCheck):
            #print len(numOfFires)
            sumOfNumOfFires=sumOfNumOfFires+numOfFires[i]            
            numOfFires[i]=numOfFires[i]*dbl_AvgCrewsPerFire
                
        needCrews=self.checkPoolForDaysChecked(numOfFires,bool_Request)
        if bool_Request==True:
            if needCrews>0:
                #We don't expect to have enough crews so we will need to import
                #we do however need to calulate the number of crews in groups of 5 as that works
                #out to 20 crew members
                int_reqCrews=ceil(needCrews/5.0)*5
                self.makeRequest(int_reqCrews)
        else:
            print now(),self.name,"Extra Crews expected:",needCrews
    
    #essentially a copy of the ResourcesVsFire but this one returns the value of extra crews
    def extraCrewsAvailable(self,str_firePredictionType):
        #print self.name
        i=0
        int_reqCrews=0
        sumOfNumOfFires=0
        numOfFires=self.expectedFires(int(floor(now())),self.int_daysToCheck,str_firePredictionType)
        for i in range(0,self.int_daysToCheck):
            sumOfNumOfFires=sumOfNumOfFires+numOfFires[i]            
            numOfFires[i]=numOfFires[i]*dbl_AvgCrewsPerFire            
        needCrews=self.checkPoolForDaysChecked(numOfFires,False)
        return needCrews
    
    def checkPoolForDaysChecked(self,arrayOfFires,bool_Request):
        ##print "Checking for daily levels"
        i=0
        ##print arrayOfFires
        calcTempPool=self.int_crew_pool
        minOfPool=calcTempPool
        for i in range (0,self.int_daysToCheck):
            if i>1:
                calcTempPool=calcTempPool-arrayOfFires[i]+arrayOfFires[i-2]
            else:
                calcTempPool=calcTempPool-arrayOfFires[i]
            if calcTempPool<minOfPool:
                minOfPool=calcTempPool
        if minOfPool<0:                
            return minOfPool*-1
        else:
            if bool_Request==False:
                return minOfPool
            else:
                return 0
     
    
   
    
    def expectedFires(self,currentDay,days,str_firePredictionType):
        #print now(),self.name,"Checking for expected fires in the next ",days,"days"
        #Will need to search x # of days into the future to find the exepected number of fires
        #First option is to go through the actual fire days and get the exact number
        #This would obviously mean that the fire managers were 'guessing' the number
        #of fires at a 100% accuracy
        i=[]
        
        if self.int_lastDayResourcesChecked>-1:
            dayswithoutupdate=currentDay-self.int_lastDayResourcesChecked
        else:
            dayswithoutupdate=days
        
        for x in range(0,days):
            i.append(0)
        if str_firePredictionType==1:
            for row in self.firedata:                
                if int(row[0])>currentDay and int(row[0])<=currentDay+days:
                    i[int(row[0])-currentDay-1]=i[int(row[0])-currentDay-1]+1
            return i
    
        #Second option, compare the indicies to predict the number of fires expected from that
        #indicies.
        else:
            #print "AAAAAAAAAA",self.int_FiresForDaysToCheck, self.name
            #print currentDay,dayswithoutupdate
            #Read in the indicies for the regions and pass that to the calculation to 
            #get the number of fires expected in the region
            for x in range(0,dayswithoutupdate):
                self.int_FiresForDaysToCheck.pop(0)
                passDate=currentDay+x+1
                self.int_FiresForDaysToCheck.append(int(self.getFiresFromWeather(passDate)))
            #print self.int_FiresForDaysToCheck, len(self.int_FiresForDaysToCheck)    
            return self.int_FiresForDaysToCheck
    
    #The province is running low or out of crews, a request is made to shore up the 
    #crew pool by borrowing from the other province(s)
    def makeRequest(self,int_reqCrews):
        #print now(),self.name,"Making a request for Crews:",int_reqCrews
        if self.requestedCrews[1]==0:
            self.requestedCrews[0]=floor(now())
            self.requestedCrews[1]=int_reqCrews
        #April 17 2013 (AS)
        self.bool_madeRequest=True

        
    
    
    def checkForRequests(self):
        provPool=0
        sendEx1=0
        sendEx2=0
        provNum1=0
        provNum2=0
        remPool=0
        continueRequests=True
        if self.bool_madeRequest==False:
            if self.name=="Ontario":
                ext1=prov2
                ext2=prov3
                provNum1=1
                provNum2=2
            elif self.name=="Prov2":
                ext1=ontario
                ext2=prov3
            else:
                ext1=ontario
                ext2=prov2
            while continueRequests:
                provPool=self.extraCrewsAvailable(self.str_responsePrediction)-self.ExtCrews[1][2]-self.ExtCrews[2][2]
                #Does province still have crews to send (greater than 5)
                #Are crew requirements not met at other provinces
                #print provPool,ext1.name,ext1.requestedCrews[1],ext2.name,ext2.requestedCrews[1]
                #print sendEx1,sendEx2                
                if provPool>=5 and ext1.requestedCrews[1]>sendEx1 and ext2.requestedCrews[1]>sendEx2:                    
                    if ext1.requestedCrews[1]-sendEx1 > 0 and ext2.requestedCrews[1]-sendEx2>0:
                        if provPool>ext1.requestedCrews[1]+ext2.requestedCrews[1]-sendEx1-sendEx2:
                            sendEx1=ext1.requestedCrews[1]
                            sendEx2=ext2.requestedCrews[1]
                            provPool=provPool-sendEx1-sendEx2
                        else:
                            if intFillRequest==1:
                                #Which is the Larger Request?
                                if ext1.requestedCrews[1]-sendEx1>ext2.requestedCrews[1]-sendEx2:
                                    remPool=min(provPool,ext1.requestedCrews[1]-sendEx1)
                                    sendEx1=sendEx1+remPool
                                    provPool=provPool-remPool
                                elif ext1.requestedCrews[1]-sendEx1<ext2.requestedCrews[1]-sendEx2:
                                    remPool=min(provPool,ext2.requestedCrews[1]-sendEx2)
                                    sendEx2=sendEx2+remPool
                                    provPool=provPool-remPool
                                else:
                                    #Same number requested, see who was earlier
                                    #if they are the same day then split resources
                                    if ext1.requestedCrews[0]<ext2.requestedCrews[0]:
                                        remPool=min(provPool,ext1.requestedCrews[1]-sendEx1)
                                        sendEx1=sendEx1+remPool
                                        provPool=provPool-remPool
                                    elif ext1.requestedCrews[0]>ext2.requestedCrews[0]:
                                        remPool=min(provPool,ext2.requestedCrews[1]-sendEx2)
                                        sendEx2=sendEx2+remPool
                                        provPool=provPool-remPool
                                    else:
                                        remPool=min(ceil(provPool/2.0),ext1.requestedCrews[1]-sendEx1)
                                        sendEx1=sendEx1+remPool
                                        remPooltemp=min(provPool-remPool,ext2.requestedCrews[1]-sendEx2)
                                        sendEx2=sendEx2+remPooltemp
                                        provPool=provPool-remPool-remPooltemp
                                
                            else:
                                #FIFO Request processing
                                if ext1.requestedCrews[0]<ext2.requestedCrews[0]:
                                    remPool=min(provPool,ext1.requestedCrews[1]-sendEx1)
                                    sendEx1=sendEx1+remPool
                                    provPool=provPool-remPool
                                elif ext1.requestedCrews[0]>ext2.requestedCrews[0]:
                                    remPool=min(provPool,ext2.requestedCrews[1]-sendEx2)
                                    sendEx2=sendEx2+remPool
                                    provPool=provPool-remPool
                                else:
                                    #Requests have come in at the same time
                                    #Which is the Larger Request, if the same time and the same request
                                    #then split the resources
                                    if ext1.requestedCrews[1]-sendEx1>ext2.requestedCrews[1]-sendEx2:
                                        remPool=min(provPool,ext1.requestedCrews[1]-sendEx1)
                                        sendEx1=sendEx1+remPool
                                        provPool=provPool-remPool
                                    elif ext1.requestedCrews[1]-sendEx1<ext2.requestedCrews[1]-sendEx2:
                                        remPool=min(provPool,ext2.requestedCrews[1]-sendEx2)
                                        sendEx2=sendEx2+remPool
                                        provPool=provPool-remPool
                                    else:
                                        remPool=min(ceil(provPool/2.0),ext1.requestedCrews[1]-sendEx1)
                                        sendEx1=sendEx1+remPool
                                        remPooltemp=min(provPool-remPool,ext2.requestedCrews[1]-sendEx2)
                                        sendEx2=sendEx2+remPooltemp
                                        provPool=provPool-remPool-remPooltemp
                    elif ext1.requestedCrews[1]-sendEx1>0:
                        remPool=min(provPool,ext1.requestedCrews[1]-sendEx1)
                        sendEx1=sendEx1+remPool
                        provPool=provPool-remPool
                    else:
                        remPool=min(provPool,ext2.requestedCrews[1]-sendEx2)
                        sendEx2=sendEx2+remPool
                        provPool=provPool-remPool
                else:
                    #print "AAAAAAAAAAAAAAAAAAAAAAA"
                    continueRequests=False
            #print "Getting rid of crew requests"
            ext1.requestedCrews[1]=ext1.requestedCrews[1]-sendEx1
            ext2.requestedCrews[1]=ext2.requestedCrews[1]-sendEx2
            self.ExtCrews[1][2]=self.ExtCrews[1][2]+int(sendEx1)
            self.ExtCrews[2][2]=self.ExtCrews[2][2]+int(sendEx2)
            #return [sendEx1,sendEx2]
        
#end of province


def determineCurrentDay():
    return int(now()/24)


    



def setYearData():
        print "Running Sim For: "+ str(int_year_simulated)
    

def probOfEscape(int_ecoRegion,bool_Large,dbl_ISINow,dbl_provLoad):
    #replacing 'Assign wx based on Ecoregion', taking the ecoregion
    #and assigning the weather indexes for the region to the 'now' variables
    #Module: 4 ha ProbLarge: is completed using dbl_probofescape_small
    #Module: 100 hs ProbLarge: is completed using dbl_probofescape_large
    #comments for each ecoregion include the original equation from Arena
    

    if int_ecoRegion==91:
        ##print "Eco91"
        if bool_Large: 
            #prob large = 1/(1+EP(-(-6.57+0.15*ISINow+0.012*provload)))
            return 1 / (1 + exp(-(-6.57+0.15*dbl_ISINow + 0.012 * dbl_provLoad)))
        else:
            # prob small = 1/(1+EP(-(-4.02+0.15*ISINow+0.017*provload)))
            return 1 / (1 + exp(-(-4.02+0.15*dbl_ISINow + 0.017 * dbl_provLoad)))
    elif int_ecoRegion==92:
        ##print "Eco92"
        if bool_Large: 
            #prob large = 1/(1+EP(-(-6.57+0.15*ISINow+0.012*provload)))
            return 1 / (1 + exp(-(-6.57+0.15*dbl_ISINow + 0.012 * dbl_provLoad)))
        else:
            # prob small = 1/(1+EP(-(-4.02+0.15*ISINow+0.017*provload)))
            return 1 / (1 + exp(-(-4.02+0.15*dbl_ISINow + 0.017 * dbl_provLoad)))
    elif int_ecoRegion==93:
        ##print "Eco93"
        if bool_Large: 
            #prob large = 1/(1+EP(-(-7.37+0.17*ISINow+0.015*provload)))
            return 1 / (1 + exp(-(-7.37+0.17*dbl_ISINow + 0.015 * dbl_provLoad)))
        else:
            #prob small = 1/(1+EP(-(-4.03+0.16*ISINow+0.022*provload)))
            return 1 / (1 + exp(-(-4.03+0.16*dbl_ISINow + 0.022 * dbl_provLoad)))
    elif int_ecoRegion==94:
        ##print "Eco94"
        if bool_Large: 
            #prob large = 1/(1+EP(-(-5.00+0.15*ISINow+0.009*provload)))
            return 1 / (1 + exp(-(-5.00+0.15*dbl_ISINow + 0.009 * dbl_provLoad)))
        else:
            #prob small = 1/(1+EP(-(-3.56+0.13*ISINow+0.03*provload)))
            return 1 / (1 + exp(-(-3.56+0.13*dbl_ISINow + 0.03 * dbl_provLoad)))
    elif int_ecoRegion==96:
        ##print "Eco96"
        if bool_Large: 
            #prob large = 1/(1+EP(-(-4.84+0.12*ISINow+0.005*provload)))
            return 1 / (1 + exp(-(-4.84+0.12*dbl_ISINow + 0.005 * dbl_provLoad)))
        else:
            #prob small = 1/(1+EP(-(-2.52+0.1*ISINow)))
            return 1 / (1 + exp(-(-2.52+0.1*dbl_ISINow)))
    elif int_ecoRegion==901:
        ##print "Eco901"  
        if bool_Large:  
            # prob large= 1/(1+EP(-(-5.05+0.13*ISINow+0.008*provload)))        
            return 1 / (1 + exp(-(-5.05+0.13*dbl_ISINow + 0.008 * dbl_provLoad)))
        else:
            # prob small = 1/(1+EP(-(-3.68+0.14*ISINow+0.018*provload)))
            return 1 / (1 + exp(-(-3.68+0.14*dbl_ISINow + 0.018 * dbl_provLoad)))
        
        
    elif int_ecoRegion==98:
        ##print "Eco98"
        if bool_Large: 
            #prob large = 1/(1+EP(-(-7.91+0.13*ISINow+0.008*provload)))
            return 1 / (1 + exp(-(-7.91+0.13*dbl_ISINow + 0.008 * dbl_provLoad)))
        else:
            #prob small = 1/(1+EP(-(-3.91+0.13*ISINow+0.006*provload)))
            return 1 / (1 + exp(-(-3.91+0.13*dbl_ISINow + 0.006 * dbl_provLoad)))
    else:
        ##print "Eco97 or other"
        if bool_Large: 
            #prob large =1/(1+EP(-(-6.15+0.22*ISINow)))
            return 1 / (1 + exp(-(-6.15+0.22*dbl_ISINow)))
        else:
            #prob small = 1/(1+EP(-(-3.77+0.19*ISINow)))
            return 1 / (1 + exp(-(-3.77+0.19*dbl_ISINow)))
        

def isAirtankerAvailable(prov):
    #from Delay Resources for IA->Available Airtankers
    #if airtanker is available it returns True and reduces count by one
    #else it returns False
    if prov.int_airtanker_pool >0:
        prov.int_airtanker_pool -= 1
        return True
    else:
        return False
    

    

def isIACrewAvailable(prov,int_type,intNumRequest):
    #from Delay Resources for IA->IA Crew Available
    #if crew is available it returns True and reduces count by one
    #else it returns False
    #int_type =1 would mean the crew pool whereas other than
    #2 would mean that we are looking at crew2
    if int_type ==1:
        ##print prov.int_crew_pool
        if prov.int_crew_pool >= intNumRequest:
            prov.int_crew_pool -=intNumRequest
            return True
        else:
            return False
    else:
        if prov.int_crewtype2_pool >= intNumRequest:
            prov.int_crewtype2_pool -=intNumRequest
            return True
        else:
            return False
    



#Return is in Hours
#-1 if unknown delay Type requested
def delayCrews(str_Type):
    #from Delay Resources for IA->Delay IA/other crews
    #As there are different types of potential delays
    #each criteria need a different delay returned
    if str_Type=="crews":
        return int_hours_delay_IA_Crews
    elif str_Type=="type2crews":
        return int_hours_delay_IA_Type2Crews
    elif str_Type=="airtanker":
        return int_hours_delay_IA_AirTanker
    else:
        return -1


#declaring the variables
#In theory these are global 'variables' but may end up moving into the province if
#there is a need to differ them for each province

#starting day
int_day=0
#Used to check if the perimeter has been contained (.75 based on model)
dbl_perim_contain_threshold=0.75
#Calibration run=0 not on, 1 set for calibration(not enabled)
int_calibration_run=0
#Should be either 4 or 100 (based on the Arena model anyway)
int_escape_size_criteria=4
#Options for 1992-2003 (4 digit year)
int_year_simulated=int(sys.argv[2])
#Delay time for the resources (in hours)
int_hours_delay_IA_Crews=12
int_hours_delay_IA_Crews2=12
int_hours_delay_IA_Type2Crews=12
int_hours_delay_IA_Type2Crews2=12
int_hours_delay_IA_AirTanker=12
int_end_of_fire_season=182
#Request Processing type
#1 - Largest
#2 - FIFO
intFillRequest=int(sys.argv[4])
#Penalty for missing Crew1
dbl_missingCrewPenalty=1.5
#Sharing enabled or not
#1 means yes there is a share
#0 means no sharing
int_sharingEnabled=int(sys.argv[6])

#Penalty for missing Airtankers
dbl_missingAirtankerPenalty=1.2
#When "guessing" the number of crews needed this value will be used to 
#set the average number of crews per fire. Set as a float.
dbl_AvgCrewsPerFire=3.0
#Variable to enable or disable the use of the Type 2 crews
#which may not be available at the start of the season
#In Arena model they don't show up till the 45th day
bool_Type2_Crew = False
int_Day_For_Type2_Crew = 45
#Is it Day 45 (Decide 50 From Arena)
def useType2Crews():
    bool_Type2_Crew=True
# end of variable creation

    



#ontario = Province ("Ontario",200,100,9,12)    
setYearData()

#Read in the firedata
#FireExcelDate, Fire Arrival Time, provload, fuelnow, ecoregion, cause
#firedata = readInData(csvlist[0][2],"txt")

#Read in the list of Provinces
provinceList=readInData("resources.csv","csv")

#Historic fire weather for Ontario, this data is used to find the expected number of fires in the region
#Date,FFMC,DMC,ISI,BUI,WS,HumanFires,LightningFires (for ecoregion:90,91,93,94,96,97,98)
fireInOntario=readInData("number of fires per day ONT.csv","csv")
fireInOntario.pop(0)


ontario=Province(provinceList[0][0],int(provinceList[0][1]),int(provinceList[0][2]),int(provinceList[0][3]),int(provinceList[0][4]),int(provinceList[0][5]))
prov2=Province(provinceList[1][0],int(provinceList[1][1]),int(provinceList[1][2]),int(provinceList[1][3]),int(provinceList[1][4]),int(provinceList[1][5]))
prov3=Province(provinceList[2][0],int(provinceList[2][1]),int(provinceList[2][2]),int(provinceList[2][3]),int(provinceList[2][4]),int(provinceList[2][5]))
ontario.EcoZones=[90,91,93,94,96,97,98]
prov2.EcoZones=[90,90,90,91]
prov3.EcoZones=[90,90,90,96,96,96,96,97]



## print int_year_simulated
## temp=raw_input("Yo!")
i=0
initialize()
for eachRow in provinceList:
    for row in csvlist:
        if int(row[0])==int_year_simulated:
            ##print "Row:",row[1],"EachRow",eachRow[0]
            if row[1]==eachRow[0]:
                if row[1]=="Ontario":
                    ##print "ZZZZZZZZZ"
                    ontario.importWeatherData(row[3].rstrip())
                    ontario.importFireData(row[2])
                elif row[1]=="Prov2":
                    ##print "YYYYYYYYYY"
                    prov2.importWeatherData(row[3].rstrip())
                    prov2.importFireData(row[2])
                else:
                    ##print "XXXXXXXXX"
                    prov3.importWeatherData(row[3].rstrip())
                    prov3.importFireData(row[2])

intFirstDay=min(ontario.intFirstDay,prov2.intFirstDay,prov3.intFirstDay)
#simulate(until=int_end_of_fire_season)
#simulate(until=10)
simulate(min(len(ontario.weatherdata),int_end_of_fire_season))
#print len(ontario.weatherdata)
simFireStats()
## print "Ontario Human",ontario.int_HumanFireCount
## print "Ontario Cloud Static",ontario.int_LightningFireCount
## print "ON Escaped",ontario.int_EscapedFires
## print "ON IA Success",ontario.int_IASuccess
## print "prov2 Human",prov2.int_HumanFireCount
## print "prov2 Cloud Static",prov2.int_LightningFireCount
## print "prov2 Escaped",prov2.int_EscapedFires
## print "prov2 IA Success",prov2.int_IASuccess
## print "prov3 Human",prov3.int_HumanFireCount
## print "prov3 Cloud Static",prov3.int_LightningFireCount
## print "prov3 Escaped",prov3.int_EscapedFires
## print "prov3 IA Success",prov3.int_IASuccess