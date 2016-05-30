#Class definitions
#Generic Script exception
import re

class ParserErrors(Exception):
    def __init__(self, message='Generic Error during script execution'):
        super(ParserErrors, self).__init__(message)
        self.message = message

class ClassErrors(ReferenceError):
    def __init__(self, message='Error : Not a class object'):
        super(ReferenceError, self).__init__(message)
        self.message = message
        
class ConfigParseError (Exception):
    def __init__(self, message='Error : Configuration parsing'):
        super(ParserErrors, self).__init__(message)
        self.message = message
       
class CounterGroup:
    def __init__(self,stat_type):
        self.stat_type = stat_type
        self.counterNames = []
        self.instances = []


class Instance:
    def __init__(self,name):
        self.name = name
        self.propertyList = {}
        # List of list of counter ordered by timestamp ex => counterList[20150402][success]->30
        self.counterList = {}
        # List of instantiated proxies for this instance
        self.proxyList = {}
        
    def add_counter(self, timestamp, counters):
        if (not timestamp in self.counterList ) :
            #print("INFO : Timestamp ", timestamp, " already exist for object ", self.name)
            self.counterList[timestamp] = {}
        for counter in counters:  
            if (counter in self.counterList[timestamp]) :
                #if ( debug ) : print("DEBUG - overwriting existing counter", counter," for instance", self.name)
               
                match = re.search( "([0-9]+)", counters[counter])
                if (  match ) :
                    self.counterList[timestamp][counter] = counters[counter]
                    #print("DEBUG - Previous ", self.counterList[timestamp][counter], "New Value ", counters[counter])
            else :
                self.counterList[timestamp][counter] = counters[counter]
                
    def del_counter(self, timestamp, counter):
       del self.counterList[timestamp][counter]
    def add_property(self, tag, prop):
        self.propertyList[tag] = prop
    def del_property(self, tag):
        del self.propertyList[tag]
    # Add proxy instance in proxyList
    def add_proxy(self, tag, proxy):
        self.proxyList[tag]  = proxy
    def del_proxy(self, tag):
        del self.proxyList[tag]
    # Return proxy instance
    def get_proxy(self, tag) :
        try : return self.proxyList[tag]
        except KeyError : print("ERROR - Failed to retrieve proxy : ", tag, "for instance : ", self.name)
    def get_counter(self) :
        return self.counterList
    def show_property(self, prop="ALL"):
        if prop == "ALL":
            #print(self.name)
            print("\t Property of:", self.name, " : ")
            for i in self.propertyList:
                print( "\t => ", i, self.propertyList.get(i) )
        else :
            find_counter(prop)
    def show_proxy(self, proxy="ALL") :
        if proxy == "ALL":
            print("\t Proxy of ", self.name, " :")
            for _proxy in sorted(self.proxyList.keys() ):
                print( "\t=>", _proxy )
        else :
            if ( proxy in proxyList ) : print( self.proxyList[proxy].name)
    def show_counter(self, counter="ALL") :
        if counter == "ALL" :
            for ts in self.counterList :
                print ("Timestamp" , ts)
                for k in self.counterList[ts] :
                    print("\t",k, "->", self.counterList[ts][k])

# Inherit from Instance class
class Proxy(Instance):
    def __init__(self,name,basic):
        super(Proxy, self).__init__(name)
        self.basic = basic
        

class Wrapper():
    def __init__(self, kind):
        self.instanceList = {}
        self.instanceCount  = 0
        self.kind = kind
    def length(self):
        return len(self.instanceList)
    def add_instance(self, tag ,instance):
        self.instanceList[tag] = instance
        self.instanceCount += 1
    def del_instance(self, tag):
        del self.instanceList[tag]
        self.instanceCount -= 1
    def get_instance(self, tag):
        return self.instanceList[tag]
    def show(self, tag="ALL"):
        if tag == "ALL":
            for i in self.instanceList:
                print(self.instanceList.get(i).name)
                print(self.instanceList.get(i).show_property() )
                print(self.instanceList.get(i).show_proxy())
                print(self.instanceList.get(i).show_counter())
        else :
            if ( tag in self.instanceList ) :
                print( self.instanceList[tag].show_property() )
                print( self.instanceList[tag].show_proxy() )
                print( self.instanceList[tag].show_counter() )
    def brief(self) :
        print("Total number of instance :", self.instanceCount)
        self.proxyCount = 0
        self.counterCount = 0
        for i in self.instanceList:
            self.proxyCount += len(self.instanceList.get(i).proxyList)
        print("Total number of proxies  : ", self.proxyCount)
            

        