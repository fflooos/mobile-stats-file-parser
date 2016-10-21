# mobile-stats-file-parser

XML to csv parser especially designed for mobile stats files

- [INSTALLATION](#installation)
- [DESCRIPTION](#description)
- [OPTIONS](#options)
- [EXAMPLE](#example)

# INSTALLATION

To install it right away for all UNIX users (Linux, OS X, etc.), type:

    sudo apt-get install python3

To install python3 for CentOs (not in repo):

    yum install xz-libs
    yum groupinstall -y 'development tools'
    yum install openssl-devel


    wget http://python.org/ftp/python/3.4.5/Python-3.4.5.tar.xz
    xz -d Python-3.4.5.tar.xz
    tar xvf Python-3.4.5.tar.xz
    cd Python-3.4.5
    sudo ./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
    sudo make
    sudo make altinstall

To install it for windows :

    Install python3 installer (https://www.python.org/downloads/)

# CONFIGURATION

Setting up input files path :

    Edit file parser.py and update below line with the directories containing the data input files:
    # List of directory to look-up
    dirList =   {
                "/mnt/xml_tmp/",
                "/mnt/CORE_replica/sgwcg/xml/stn/"
                "/mnt/CORE_replica/sgwcg/xml/mgw"
            }

Defining lastdate parameter :
    lastdate parameter defined the time windows at which the script will look back in the past from now to process the files
    ie: if lastdate=2  ==> only file from last 2 hours will be processed
    NB: timestamp used to compute lastdate is extracted from the filename not from system time.
    Edit file parser.py and update below line:
    # LASTDATE
    # Max number of hours to recover from data files
    lastdate = 2



# OPTIONS

    usage: parser.py [-t] [-d] [-v] [-m]
        Retrieve GPS coordinated from gMaps using post address from input file
        positional arguments:
            input_file     input file
            output_file    output file
            set            List of columns containing postal address separated by ',' (Ex: "3,4,5")
        optional arguments:
            -h, --help     show this help message and exit
            -d, --debug    Enable debugging information
            -v, --version  Show debug information

