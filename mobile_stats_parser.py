#!/usr/bin/python
# -*- coding: latin-1 -*-

import pandas as pd
import xml.etree.ElementTree as ET, os, sys, glob, re
from optparse import OptionParser
from datetime import datetime
from datetime import timedelta
import re

# Set options for better display in console
pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


# Get script current directory
scriptDir = os.path.dirname(os.path.abspath(__file__))

# List of directory to look-up
dirList =   {
                "$HOME/script/"
            }

# Parse command line arguments
parser = OptionParser()
parser.add_option("-d", "--data", dest="outdata",
                  help="write data to <FILENAME>", metavar="FILE")
parser.add_option("-v", "--verbose",
                  action="store_true", dest="debug", default=False,
                  help="Enable debug mode to stdout")

(options, args) = parser.parse_args()

# TO DO, handle multiple identical parameter => generate counter
def recusive_search( _tree, _max_size ):

    _wrapper = {}
    _row = {}
    _max_list = {}
    _int_ct = 0;

    for elem in _tree.iter():
        if not isinstance(elem.tag, str) and tag is not None:
            pass
        if elem.text :
            if (elem.tag == "GraphicString"):
                _tag = "GraphicString"+str(_int_ct)
                _int_ct +=1
            else : _tag = elem.tag
            _row[_tag]= elem.text
            _wrapper.update(_row)
            if (debug) : print ("Added to wrapper : ", elem.tag, elem.text)

    if (len(_wrapper) > _max_size ) :
        print ("New size:", len(_wrapper))
        _max_size = len(_wrapper)
        _max_list = _wrapper.keys
    return _max_size, _wrapper, _max_list
        
def create_dataframe(data, _max_list, _ts):
    time = {}
    # Generate dataframe per record timestamp
    df = pd.DataFrame(columns=_max_list)
    #_ts = datetime()
    s = str(_ts.isoformat())
    print("test")
    print (len(data))
    for i in range(len(data)):
        row = data[i]
        row["timestamp"] = s
        row_series = pd.Series(row)
        if (debug) : print( "ROW **************************************")
        if (debug) : print(row_series)
        row_series.name = i
        df = df.append(row_series)
    return df

# Parse file using tag defined in parser.ini
def _parseFile(_file, wrap):
    maxSize = 0
    item_list = {}
    max_list = {}
    
    try : tree = ET.parse(_file)
    except ParserErrors : print( "ERROR - Exception raised while parsing file :",_file ); return max_list, 0
    except FileNotFoundError: print ("ERROR - File was delete while processing :", _file); return max_list, 0
    
    if (not len(wrap) == 0 ) : i = 0
    else : i = len(wrap)
    
    for elem in tree.iter(tag="IMSRecord"):
        if (debug) : print ("************************************** NEW RECORD *****************************************")
        maxSize, item_list, max_list =  recusive_search(elem, maxSize)
        wrap[i] = item_list
        i += 1

    print ("Max size of item in list:",maxSize)
    return max_list, 1
    
def _extractTs(fileN) :
    file_regex = 'CCFL0_-_(\d{5})\.(\d{4})(\d{2})(\d{2})_-_(\d{2})(\d{2}).*.xml' 
    date_1 = datetime.now()
    
    match = re.match(file_regex, fileN)
    if ( match ) :
        try : parse_date = datetime(int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5)), int(match.group(6)) )
        except ValueError:
            print ("ERROR - Error while parsing the timestamp, please review the regex in _isProcessed() function")
            return 0, 0
        return int(match.group(1)), parse_date
    else :
        return 0, 0

# check if there is a next file in loop if not return false.
def lookahead(iterable):
    # Get an iterator and pull the first value.
    it = iter(iterable)
    last = next(it)
    print ("Last ",last)
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value.
        yield True
    # Report the last value.
    yield False


# MAIN

if __name__ == '__main__':
    # Enable debug if option -v is specified
    if ( options.debug ) : debug = True
    else : debug = False
    
    # Wrapper container for all dataframe
    wrapperList = {}
    max_list = {}
    # Wrapper for all rows in dataframe
    wrap ={}
    ccflo = 0
    last_ts = 0
    first = True
    
    # Loop through directory list
    for directory in dirList :
        for root, dirs, files in os.walk(directory) :
            f = lookahead(files)
            for basename in files :
                
                hasMore = f.__next__()
                print("hasMore: ",hasMore)
                # Discard not .xml files
                if( basename.endswith(".xml") ) :
                    # Extract CCFLO and ts from filename
                    
                    ccflo, ts = _extractTs(basename)
                    if ( not ccflo == 0) :
                            
                        print("(not ",ts," == ",last_ts," and not", first, ") or not", hasMore)
                        # If new timestamp different from last_ts
                        if ( (not (ts == last_ts) and not first) or not hasMore) : 
                            df = pd.DataFrame()
                            df = create_dataframe(wrap, max_list, ts)
                            
                            print ("Dataframe length:",len(df))
                            print ("Dataframe column:",df.columns)
    
                            wrapperList[ ccflo ] = df
                            # Reset wrapper for rows (new dataframe)
                            wrap.clear()
                            
                        last_ts = ts
                        #Parse XML file
                        max_list, status = _parseFile(os.path.join(root, basename), wrap)
                        print ("Number of items in wrap:",len(wrap))
                        if ( not status == 0):
                            print("\t\t--> OK")
                        else : print("\t\t--> ERROR : Parsing failed")
                    else : print( "ERROR : Unable to extract CCFLO/timestamp from filename", basename)
                    
                else :
                    print( "INFO : Not an XML file, skipping :", basename)
                if (first) : first = False

    for df in wrapperList :
        
        print(df)
        #date = df["sIP-Request-Timestamp"].values[0]
    
    #ts = datetime.strptime(date, "%y%m%d%H%M%S")
    
    #print ("Converted ts:", ts)
#CauseForRecordClosing ::= INTEGER
#{
#serviceDeliveryEndSuccessfully (0),
#unSuccessfulServiceDelivery (1),
#timeLimit (3),
#serviceChange (4), -- e.g. change in
#media due to Re-Invite
#managementIntervention (5) -- partial record
#generation reasons to be added
#-- Additional
#codes are for further study
#}

#group= df.serviceReasonReturnCode
#pd.Series(group).unique()
#
#filter out df[(df.causeForRecordClosing != "4
    
        # Generating subgroup with filtered column
        subgroup = df[["session-Id", "localRecordSequenceNumber", "sIP-Method", "domainName", "serviceRequestTimeStamp", "serviceDeliveryStartTimeStamp", "recordClosureTime", "causeForRecordClosing", "serviceReasonReturnCode"]]
        #subgroup.iloc[df.groupby( ["session-Id"] )['localRecordSequenceNumber'].agg(pd.Series.idxmax)]
        
        timestamp = df.serviceRequestTimeStamp.values[0]
        #datetime.strptime(timestamp, "%Y-%m-%d")
    # Select unique(session-Id) max(localRecordSequenceNumber)
        subgroup_unique = df.iloc[df.groupby( ["session-Id"] )['localRecordSequenceNumber'].agg(pd.Series.idxmax)]    
        #subgroup_unique["causeForRecordClosing"]
    # Test unique
        #test[(test["session-Id"] == "LU-1462788930519458-491628@stas-stdn.fsimsgroup0-001.qdc1ics01.ims.vodafone.com.qa")]
        
        count = 0
        group = subgroup_unique[(subgroup_unique.causeForRecordClosing == "0") ]
        for sessionId, group_data in  group.groupby( ["session-Id"]) :
            #print ("Session ID  ", sessionId)
            count +=1
    
        print ("Number of 0:serviceDeliveryEndSuccessfully calls", count)
    
        count = 0
        group = subgroup_unique[(subgroup_unique.causeForRecordClosing == "1") ]
        for sessionId, group_data in  group.groupby( ["session-Id"]) :
            #print ("Session ID  ", sessionId)
            count +=1
    
        print ("Number of 1:unSuccessfulServiceDelivery calls", count)
    
        count = 0
        group = subgroup_unique[(subgroup_unique.causeForRecordClosing == "2") ]
        for sessionId, group_data in  group.groupby( ["session-Id"]) :
            #print ("Session ID  ", sessionId)
            count +=1
    
        print ("Number of 2:? calls", count)
    
        count = 0
        group =subgroup_unique[(subgroup_unique.causeForRecordClosing == "3") ]
        for sessionId, group_data in  group.groupby( ["session-Id"]) :
            #print ("Session ID  ", sessionId)
            count +=1
    
        print ("Number of 3:timeLimit calls", count)
    
        count = 0
       
        count = 0
        group = subgroup_unique[(subgroup_unique.causeForRecordClosing == "4") ]
        for sessionId, group_data in  group.groupby( ["session-Id"]) :
            #print ("Session ID  ", sessionId)
            count +=1
    
        print ("Number of 4:serviceChange calls", count)
    
        count = 0
        group = subgroup_unique[(subgroup_unique.causeForRecordClosing == "5") ]
        for sessionId, group_data in  group.groupby( ["session-Id"]) :
            #print ("Session ID  ", sessionId)
            count +=1
    
        print ("Number of 5:managementIntervention calls", count)
        
        count = 0
        for sessionId, group_data in subgroup_unique.groupby( ["session-Id"]) :
            sid = group_data["serviceReasonReturnCode"].str.extract('(\d+)')
            #print (sid.values[0])
            if ( (int(sid.values[0]) >= 400) and (int(sid.values[0]) <= 412 ) ):
                print("ok")
                count +=1
    
        print ("Number sessionID  :serviceReasonReturnCode between 400 and 412 calls", count)
        
        
        #count = 0
        #group = df[(df.causeForRecordClosing != "4") & (df.causeForRecordClosing != "5") ]
        #for sessionId, group_data in  group.groupby( ["session-Id"]) :
        #    print ("Session ID  ", sessionId)
        #    count +=1
        
        #print ("Number of total calls", count)
    
        #count = 0
        #group = df[(df.causeForRecordClosing == "0") ]
        #for sessionId, group_data in  group.groupby( ["session-Id"]) :
        #    print ("Session ID  ", sessionId)
        #    count +=1
        
        #print ("Number of successfull calls", count)
        
        
        #group= df.serviceReasonReturnCode.unique
        
        #for sessionId in df[df.causeForRecordClosing != "4" && df.causeForRecordClosing != "5" ][["session-Id"]]
