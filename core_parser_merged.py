#!/usr/bin/python
# -*- coding: latin-1 -*-

import configparser
import xml.etree.ElementTree as ET, os, sys, glob, re
from iv_class import *
from optparse import OptionParser
from datetime import datetime
from datetime import timedelta

# LASTDATE
# Max number of hours to recover from data files
lastdate = 2

# Get script current directory
scriptDir = os.path.dirname(os.path.abspath(__file__))

# List of directory to look-up
dirList =   {
                "/mnt/xml_tmp/",
                "/mnt/CORE_replica/sgwcg/xml/stn/" 
            }

# Parse command line arguments
parser = OptionParser()
parser.add_option("-t", "--topo", dest="outfile",
                  help="write topology to <FILENAME>", metavar="FILE")
parser.add_option("-d", "--data", dest="outdata",
                  help="write data to <FILENAME>", metavar="FILE")
parser.add_option("-v", "--verbose",
                  action="store_true", dest="debug", default=False,
                  help="Enable debug mode to stdout")
parser.add_option("-m", "--mode", dest="mode", default="ALL",
                  help="specify which instance kind to process (MSS/SIU/HLR...)")

(options, args) = parser.parse_args()

# Read configuration file parser.ini
config = configparser.ConfigParser()
config.read( scriptDir+"/parser_merged.ini" )


    
# Safe return of config parameter from parser.ini, return 0 if option is not found
def _get_config(_section, _parameter):
    try :  return config[_section][_parameter]
    except KeyError:
        print( "WARNING : Parameter \"", _parameter,"\" not defined for template : ", _section)
        print( "WARNING : Please review parser_merged.ini configuration")
        return 0

# Write parameter to config file parser.ini
def _set_config(_section, _parameter, _value):
    config.set(_section, _parameter, _value)
    with open ( scriptDir+"/parser_merged.ini", 'w' ) as configFile :
        config.write(configFile)
    
# Parse file using tag defined in parser.ini
def _parseFile(_file, wrap, parse_config):
    
    try : tree = ET.parse(_file)
    except  ParserErrors : print( "ERROR - Exception raised while parsing file :",_file ); return 0
    except FileNotFoundError: print ("ERROR - File was delete while processing :", _file); return 0

    if (debug) : print( "Parsing template used : ", parse_config)
               
    # Parse instance from file
    instance_parser = _get_config( parse_config, "instance_parser")
    instance_tag = _get_config( parse_config, "instance_tag" )
    instance_value =  _get_config( parse_config, "instance_value")

    
    for elem in tree.getiterator():
        regex = re.search(instance_parser, elem.tag)
        if (regex):
            if ( instance_value == "TEXT"):
                instanceN  =  elem.text
            elif ( instance_value == "ATTRIBUTE" ):
                instanceN = elem.attrib[instance_tag]
            else :
                print( "ERROR - No instance matching parsing config")
                return 0
            instanceN = _clear_instance(instanceN)
            if ( instanceN in wrap.instanceList) :
                if ( debug ) : print( "DEBUG - Instance", instanceN," already exist")
                instance = wrap.get_instance(instanceN)
            else :
                instance = Instance(instanceN)
                wrap.add_instance(instanceN, instance)
  
    # Parse proxy from file
    proxy_parser = _get_config( parse_config, 'proxy_parser')
    proxy_tag = _get_config( parse_config, "proxy_tag" ) 
    proxy_value = _get_config( parse_config, "proxy_value" )
 
    isProxy = False
    for nelem in tree.getiterator():
        regex = re.search(proxy_parser, nelem.tag)
        if (regex):
            if (proxy_value == 'ATTRIBUTE') :
                proxyN = nelem.attrib[proxy_tag]
                isProxy, proxyN = _clear_proxy(proxyN)
                if (isProxy) :
                    proxy = Proxy(proxyN, instance.name)
                    instance.add_proxy(proxy.name, proxy)
            elif (proxy_value == 'TEXT') :
                for pelem in nelem.getiterator(tag=proxy_tag):
                        proxyN = pelem.text
                        isProxy, proxyN = _clear_proxy(proxyN)
                        if (isProxy) :
                            if ( proxyN in instance.proxyList and debug) : print( "DEBUG : Proxy already exist :", proxyN, "for instance ", instance.name)
                            proxy = Proxy(proxyN, instance.name)
                            if (debug) : print( "DEBUG : Adding proxy:", proxy.name, "to instance ", instance.name)
                            instance.add_proxy(proxy.name, proxy)
            else :
                print("ERROR : proxy_value must be only ATTRIBUTE or TEXT, current value :",proxy_value)
                return 0
    
    if ( options.outdata ) :   
        _parse_counter(instance, tree, parse_config, _file)
                

def _parse_counter( instance, tree, parse_config, _file):
    # Parse counter from file
    counter_parser = _get_config( parse_config, "counter_parser" )
    counter_ts = _get_config( parse_config, "counter_timestamp" )
    
    if (counter_parser == 0 or counter_ts == 0) : return 0
       
    if ( "counter_timestamp_attrib" in config[parse_config] ):
        isAttrib = True
        ts_attrib = _get_config( parse_config, "counter_timestamp_attrib")
    else : isAttrib = False

    
    _counterList = {}
    counter_tag = _get_config( parse_config, "counter_tag" )
    counter_value = _get_config( parse_config, "counter_value" )
    proxy_value = _get_config( parse_config, "proxy_value" )
    proxy_tag = _get_config( parse_config, 'proxy_tag')
    proxy_parser = _get_config( parse_config, 'proxy_parser')

    instance_counter = _get_config( parse_config, "instance_counter_name")
    if ( not instance_counter == 0) : instance_counter = instance_counter.split('<>')
    proxy_counter = _get_config( parse_config, "proxy_counter_name")
    if (not proxy_counter == 0 ) : proxy_counter =  proxy_counter.split('<>')
    
    _last_TS = 0
    for elem in tree.getiterator() :
        regex = re.search(counter_parser, elem.tag)
        if (regex) :
            
            for timestamp in elem.getiterator() :
                regex = re.search(counter_ts, timestamp.tag)
                if (regex):
                    if (isAttrib) : ts = timestamp.attrib[ts_attrib]
                    else : ts =timestamp.text
                    
                    if ( ts is not None):
                        ts = _clear_timestamp(ts)
                        if ( int(ts) > int(_last_TS) ) : _last_TS = ts
                    elif ( not _last_TS == 0 ):
                        ts = _last_TS
                    else :
                        print ("ERROR - File ",_file," contain empty timestamps, skipping file..." )
                        return 0
                        
            if (ts == 0) :
                print("ERROR - Unable to extract timestamp value from file :", _file)
                return 0
            
            _counterName = []
            
            count = 0;
            # Loop through the counter tag
            for subelem in elem.getiterator():
                regex = re.search(counter_tag, subelem.tag)
                if (regex) :
                    _counterName.append(subelem.text)
                    count += 1
            
            _counterList = {}
            # Loop through the basic/proxy tag
            for subelem in elem.getiterator() :
                _counterList.clear()
                regex = re.search(proxy_parser, subelem.tag)
                if (regex) :
                    proxyN = ""
                    for subcount in subelem.getiterator() :
                        if (proxy_value == 'ATTRIBUTE') :
                            proxyN = subelem.attrib[proxy_tag]
                        else :
                            regex = re.search(proxy_tag, subcount.tag)
                            if (regex) :  proxyN = subcount.text
                    
                    isProxy, proxyN = _clear_proxy(proxyN)
                    _counterVal = []
                    
                    for subcount2 in subelem.getiterator() :
                        regex = re.search(counter_value, subcount2.tag)
                        if( regex ):
                            if (subcount2.text is not None):
                                match = re.search( "([0-9]+)", subcount2.text)
                                if ( match ) :
                                    _counterVal.append(match.group(1))
                                    #print("March counter_value", match.group(1))
                                else :
                                    _counterVal.append("")
                            else : _counterVal.append("")

                    #if (debug)  : print("COUNT : ",count," len(_counterVal):", len(_counterVal), "len(_counterName)", len(_counterName))
                    # Check if value list contain expected number of counter, if not fill/remove empty value
                    while ( len(_counterVal) > count ) : _counterVal.pop()
                    while ( len(_counterVal) < count) : _counterVal.append("")
                    
                    # Merge counter name with values in one associative dict
                    _counterList = dict(zip(_counterName, _counterVal))
                    _parsedList = {}
                    if (isProxy) :
                        proxy = instance.get_proxy(proxyN)
                        if ( not proxy_counter == 0 ) :
                            for kpi in sorted(proxy_counter) :
                                if ( kpi in _counterList ) :
                                    _parsedList[kpi] = _counterList[kpi]
                                else : _parsedList[kpi] = ''
                        else : _parsedList = _counterList
                        if( debug ) : print ("Adding counter to proxy")
                        try : proxy.add_counter(ts, _parsedList)
                        except KeyError : print ("ERROR - Adding counters:", _parsedList, " to proxy :", proxy.name)
                    else :
                        if ( not instance_counter == 0 ) :
                            for kpi in sorted(instance_counter) :
                                if ( kpi in _counterList ) :
                                    _parsedList[kpi] = _counterList[kpi]
                                else :
                                    if ( kpi in _parsedList) :
                                        print("Found multiple counter for KPI:", kpi, "on instance", instance.name)
                                    else : _parsedList[kpi] = ''
                        else : _parsedList = _counterList
                        #print(_parsedList)
                        try : instance.add_counter(ts, _parsedList)
                        except KeyError : print ("ERROR - Adding counters:", _parsedList, "to instance :", instance.name)

def _write_topo(wrapper) :
    separator = ','
    outDir = _get_config( "DEFAULT", "datadir")
    name_constant = _get_config( wrapper.kind, "instance_name_constant")
    name_spliter = _get_config( wrapper.kind, "instance_name_split")
    if ( options.outfile ) :
        out = outDir+options.outfile+"_"+wrapper.kind+".csv"
        #print ( "Printing output to ", out)
        fh = open (out, 'w')
        for instance in sorted(wrapper.instanceList) :
            if ( name_constant == 0 ) : instance_name = instance
            else : instance_name = name_constant+instance
            st = ("DBASIC", instance_name)
            fh.write( separator.join(st) )
            fh.write("\n")
            for proxy in sorted(wrapper.get_instance(instance).proxyList) :
                if (not name_spliter == 0) :
                    split = proxy.split(name_spliter)
                    try :
                        name = proxy
                        ntype = split[0]
                    except IndexError :
                        name = proxy
                        ntype = proxy
                else :
                    name = proxy
                    ntype = proxy
                st = ("DPROXY", name, ntype,instance_name)
                fh.write( separator.join(st) )
                fh.write("\n")

def _write_counter(wrapper) :
    separator = ','
    outDir = _get_config( "DEFAULT", "datadir")
    name_constant = _get_config( wrapper.kind, "instance_name_constant")
    name_spliter = _get_config( wrapper.kind, "instance_name_split")
    if ( options.outdata ) :
        out = outDir+options.outdata+"_"+wrapper.kind+".csv"
        fh = open (out, 'w')

        for instance in sorted(wrapper.instanceList) :
            once = True
            for _timestamp in sorted(wrapper.instanceList[instance].counterList) :
                if ( name_constant == 0 ) : instance_name = instance
                else : instance_name = name_constant+instance
                st = (_timestamp, instance_name)
                name_line = separator.join(st)
                value_line = separator.join(st)
                
                for counter in sorted(wrapper.instanceList[instance].counterList[_timestamp]) :
                    name_line += ","+counter
                    value_line += ","+wrapper.instanceList[instance].counterList[_timestamp][counter]
                if (once) :
                    once = False
                    fh.write("#")
                    fh.write(name_line)
                    fh.write("\n")
                fh.write(value_line)
                fh.write("\n")
                
        out = outDir+options.outdata+"_"+wrapper.kind+"_proxy.csv"
        fh = open (out, 'w')
        for instance in sorted(wrapper.instanceList) :
            if ( name_constant == 0 ) : instance_name = instance
            else : instance_name = name_constant+instance
            for proxy in sorted(wrapper.instanceList[instance].proxyList) :
                ponce = True
                for _timestamp in wrapper.instanceList[instance].proxyList[proxy].counterList :
                    name = instance_name+"_"+proxy
                    st = (_timestamp, name)
                    pname_line = separator.join(st)
                    pvalue_line = separator.join(st)
                    for pcounter in sorted(wrapper.instanceList[instance].proxyList[proxy].counterList[_timestamp]) :
                        pname_line += ","+pcounter
                        pvalue_line += ","+wrapper.instanceList[instance].proxyList[proxy].counterList[_timestamp][pcounter]
                       
                    if (ponce) :
                        ponce = False
                        fh.write('#')
                        fh.write( pname_line )
                        fh.write("\n")
                    fh.write( pvalue_line )
                    fh.write("\n")

# Function to extract value from instance based on regex list
def _clear_instance(instanceN) :
    instance_regex = _get_config( "DEFAULT", "global_instance_regex" )
    split = instance_regex.split('<>')
    
    for regex in split:
        match = re.match(regex, instanceN)
        if (match) : return match.group(1)
     
# Function to extract value from proxy based on regex list   
def _clear_proxy(proxyN) :
    proxy_regex = _get_config( "DEFAULT", "global_proxy_regex" )
    split = proxy_regex.split('<>')
        
    for regex in split:
        match = re.match(regex, proxyN)
        if (match) : return True, match.group(1)
    return False, 0

def _clear_timestamp(ts) :
    chars_to_remove = [':', '-', 'T', '+']
    for c in chars_to_remove :
        ts = ts.replace(c, '')
    ts_regex =[ "(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})" ]
    for regex in ts_regex:
        match = re.match(regex, ts)
        ts = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5)) )
        if (match) :
                ts - timedelta(minutes=15)
                time = ts.year+ts.month+ts.day+ts.hour+ts.minute
                return time
    return 0

def _isProcessed(fileN, last_TS) :
    file_regex = [ 'A(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})-\d{12}',
                   'A(\d{4})(\d{2})(\d{2}).(\d{2})(\d{2})',
                   'C(\d{4})(\d{2})(\d{2})\.(\d{2})(\d{2})' ]
    date_1 = datetime.now()
    #Find the most suitable minute for stats generation
    if date_1.minute < 15   :   date_1 = date_1.replace(minute=0)
    elif date_1.minute < 30 :   date_1 = date_1.replace(minute=15)
    elif date_1.minute < 45 :   date_1 = date_1.replace(minute=30)
    elif date_1.minute < 60 :   date_1 = date_1.replace(minute=45)
    
    #Contain parsing template, 0 if not defined
    parse_config = 0
    
    #Loop through config template and select template to use base on file_regex value
    for section in config:
        if (section == "DEFAULT" ): continue
        curr = config[section]["file_regex"]
        regex = re.search(curr, fileN)
        if ( regex ) :
            if (debug) : print("DEBUG : Found matching template :", section)
            parse_config = section
            break

    # Return 0 (failed) if no matching config is found
    if ( parse_config == 0) : return False, 0
    
    lastRun = _get_config( parse_config, "lastrun" )
    
    try  : lastRun = float(lastRun)
    except ValueError : lastRun = 0
    
    #Force lastrun to 0 if option -t|--topo enabled
    if ( options.outfile ): lastRun = 0
    
    for regex in file_regex :
        match = re.match(regex, fileN)
        if ( match ) :
            try : parse_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5)) )
            except ValueError:
                print ("ERROR - Error while parsing the timestamp, please review the regex in _isProcessed() function")
            if ( lastRun == 0 ) :
                lastRun_ts = date_1 - timedelta(hours=lastdate)
            else :
                lastRun_ts = datetime.fromtimestamp(float(lastRun))
            if( lastRun_ts < parse_date ) :
                if (debug) : print( "DEBUG - Current file ts: ", parse_date.isoformat(), "> last TimeStamp ", lastRun_ts.isoformat(), " -> File will be processed")
                if ( not parse_config in tmp_ts) :
                    tmp_ts[parse_config] = lastRun_ts
                    tmp_date = lastRun_ts
                else : tmp_date = datetime.fromtimestamp(tmp_ts[parse_config])
                if (parse_date > tmp_date ) :
                    tmp_ts[parse_config] = parse_date.timestamp()
                if (not tmp_date == 0 ) : last_TS[parse_config] = str(tmp_ts[parse_config])
                return True, parse_config
            else :
                if (debug) : print( "DEBUG - Current file ts: ", parse_date.isoformat(), "< last TimeStamp ", lastRun_ts.isoformat(), " -> File will not be processed")
                return False, 2
    return False, 1



# MAIN

if __name__ == '__main__':
    # Enable debug if option -v is specified
    if ( options.debug ) : debug = True
    else : debug = False
    
    # Wrapper container for all instances
    wrapperList = []
    # Wrapper for timestamp - keep track of latest file timestamps parsed per technologie kind
    last_TS = {}
    tmp_ts = {}
    
    # Check if option -m is set if none, running parsing on all types
    if ( options.mode ) : mode = options.mode
    else :   mode = "ALL"

    # Loop through directory list
    for directory in dirList :
        for root, dirs, files in os.walk(directory) :
            for basename in files :
                    # Discard not .xml files
                    if( basename.endswith(".xml") ) :
                        # Check for valid timestamp in filename and compare with last processed timestamp
                        isValid, template = _isProcessed(basename, last_TS)
                        if ( isValid ) :
                            # Select existing wrapper, or create a new one to store instance and proxy
                            # One wrapper per kind of file ex:(MSS, EPG...)
                            if ( mode == template or mode == "ALL" ) :
                                found = False
                                for wrapper in wrapperList :
                                    if (wrapper.kind == template) :
                                        wrap = wrapper
                                        found = True;   break
                                if (not found) :
                                    wrap = Wrapper(template)
                                    wrapperList.append(wrap)
                                print("INFO : Processing file :", basename)
                                if ( not _parseFile(os.path.join(root, basename), wrap, template ) == 0 ):
                                    print("\t\t--> OK")
                                else : print("\t\t--> ERROR : Parsing failed")
                        else :
                            if ( template == 0 ) :   print( "WARNING : No config template matching file header for file :", basename)
                            if ( template == 1 and debug ) :   print ("DEBUG - Unable to parse timestamp from file : ", basename)
                            if ( template == 2 and debug ) :   print ("DEBUG - Timestamp too old for file : ", basename)
                            if (debug) : print ("-> Skipping file...")
                    else : print( "INFO : Not an XML file, skipping :", basename)
    
    # Write lastRun parameter to parser.ini for each instance kind
    if (not options.outfile ):
        for k, ts in last_TS.items() :
            _set_config(k, "lastrun", ts)
        
    # Write topology to file
    if ( options.outfile ):
        for wrapper in wrapperList :
            print( "INFO : Printing topology file for instance type : ", wrapper.kind)
            if ( not wrapper.length() == 0 ) :
                _write_topo(wrapper)
            else :
                print ( "WARNING : No instance in wrapper - No file will be written for instance kind", wrapper.kind)
            
    # Write data to file
    if ( options.outdata ) :
        for wrapper in wrapperList :
            print ( "INFO : Printing counter data for instance type : ", wrapper.kind)
            if ( not wrapper.length() == 0) :
                _write_counter(wrapper)
            else :
                print ( "WARNING : No instance in wrapper - No file will be written for instance kind", wrapper.kind)
                       
    
    # Show resume of each wrapper
    for wrapper in wrapperList: 
        wrapper.brief()
