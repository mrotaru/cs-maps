#! /usr/bin/env python
"""
list, install, uninstall cs maps ( might work with other stuff )
----------------------------------------------------------------
What it does is basically trying to figure out where the contents of the
archive you give it as a parameter should be extracted. It is assumed it
contains a cs map. It can also list cs maps you currently have.
----------------------------------------------------------------
l - list maps
i - install map ( should also work with skins etc )
not implemented: u - uninstall - uninstall stuff installed with the i command
"""
import sys
import os
import glob
from subprocess import *
import commands

# global variables
cd = sys.path[0]
sep = os.path.sep
MAP_INFO='map-info'
CSTRIKE_DIR=""
CSTRIKE_STANDARD_DIRS=["DownloadLists", "addons", "bin", "cfg", "classes", "downloads", "logs", "maps", "materials",
"media", "models", "particles", "reslists_xbox", "resource", "scripts", "sound" ]

MAPLIST =  "maplist.txt"
MAPCYCLE = "mapcycle.txt"
CSSS_DIR=""

# output customisation
full_graph = True

# map lists
map_list_files={}
map_list_files[MAPLIST]=[]
map_list_files[MAPCYCLE]=[]
bsp_map_names=[]
nav_map_names=[]
all_map_names=[]


def is_exe(fpath):
    return os.path.exists(fpath) and os.access(fpath, os.X_OK)

#------------------------------------------------------------------------------
#  which - will look for 'program' in folders in the %PATH% env. variable
#------------------------------------------------------------------------------
def which(program):
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


#------------------------------------------------------------------------------
#  error printing
#------------------------------------------------------------------------------
def fatal_error( text, code ):
    print ("FATAL ERROR " + str(code)).ljust(20),": ",text
    raw_input( "Press Enter to exit..." )
    sys.exit( code )

def error( text, code ):
    print ("ERROR " + str(code)).ljust(20),": ",text

def warning( text ):
    print "WARNING: ".ljust(20),text.ljust(20)


#------------------------------------------------------------------------------
#  execute command, reuturn a tuple containing commands' output, stderr and return code
#------------------------------------------------------------------------------
# http://stackoverflow.com/questions/337863/python-popen-and-select-waiting-for-a-process-to-terminate-or-a-timeout 
def runCmd(cmd, timeout=None):
    ph_out = None # process output
    ph_err = None # stderr
    ph_ret = None # return code

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # if timeout is not set wait for process to complete
    if not timeout:
        ph_ret = p.wait()
    else:
        fin_time = time.time() + timeout
        while p.poll() == None and fin_time > time.time():
            time.sleep(1)

        # if timeout reached, raise an exception
        if fin_time < time.time():
            os.kill(p.pid, signal.SIGKILL)
            raise OSError("Process timeout has been reached")
        ph_ret = p.returncode

    ph_out, ph_err = p.communicate()
    return (ph_out, ph_err, ph_ret)

#------------------------------------------------------------------------------
#  some dirty functions for path manipulation
#------------------------------------------------------------------------------
def parent_name( full_path ):
    if not os.path.isdir( full_path ): fatal_error( "cannot find " + full_path, 3 )
    upp_dir = full_path.rsplit( os.path.sep, 2 )
    return upp_dir[1]

def parent_name_full( full_path ):
    if not os.path.isdir( full_path ): fatal_error( "cannot find " + full_path, 3 )
    upp_dir = full_path.rsplit( os.path.sep, 1 )
    return upp_dir[0]

def grandparent_name( full_path ):
    if not os.path.isdir( full_path ): fatal_error( "cannot find " + full_path, 3 )
    upp_dir = full_path.rsplit( os.path.sep, 3 )
    return upp_dir[1]

def grandparent_name_full( full_path ):
    if not os.path.isdir( full_path ): fatal_error( "cannot find " + full_path, 3 )
    upp_dir = full_path.rsplit( os.path.sep, 2 )
    return upp_dir[0]

def how_deep( path ):
    if os.path.isabs( path ):
        return path.count( sep ) - 1
    else:
        return path.count( sep )


#------------------------------------------------------------------------------
#  INSTALL MAP
#------------------------------------------------------------------------------
def install_map( map_archive ):
    print "-"*80
    print 'installing map: '.ljust(20),map_archive
    
    # make sure there is a folder named 'map-info' in the current directory
    mapinfo_full = cd + sep + MAP_INFO
    if not os.path.isdir( mapinfo_full ):
        print "folder '",mapinfo_full,"'does not exist, creating it..."
        os.mkdir( mapinfo_full )
    if not os.path.isdir( mapinfo_full ): fatal_error( "'" + mapinfo_full + "' folder was not created; exiting...", 1 )

    # create a text file with the name of the map with a 'txt' extension
    filename = mapinfo_full + sep + os.path.splitext(os.path.basename( map_archive ))[0]+'.txt'
    print 'map info filename: '.ljust(20),filename
    if os.path.isfile( filename ):
        warning( "file '" + filename + "' already exists; overwriting..." )
        os.remove( filename )

    f = open( filename, 'w' )

    # we use 7zip to tell us the structure of the files/folders inside the archive
    # therefore, we need to see if 7z is available
    # is it in Program Files ?
    sevenzip_exe = os.environ.get("ProgramFiles") + r'\7-Zip\7z.exe'
    if is_exe( sevenzip_exe ):
        print "7-Zip executable: ".ljust(20),sevenzip_exe
    else:
        # maybe it's somewhere in the PATH
        sevenzip_exe = which("7z.exe")
        if not sevenzip_exe:
            print "FATAL ERROR: cannot find 7-Zip executable; please make sure"
            print "7z.exe is in your $PATH environment variable."
            sys.exit(4)
        else:
            print "7-Zip executable: ".ljust(20),sevenzip_exe

    # we have 7z; now we use it to extract extract the folder structure from the 
    # archive, and put it in the corresponding text file ( map name with .txt extension )
    # note: all paths are relative to the 'cstrike' folder
    command = "\"" + str(sevenzip_exe) + "\"" + " l \"" + str( map_archive ) + "\""
    print "7-Zip list command: ".ljust(20),command
    pipe_output = Popen( command, stdout=PIPE, stderr=PIPE )
    lines = pipe_output.stdout.read()
    
    # check for 7-zip errors
    sz_retcode = pipe_output.wait()
    print "7-Zip return code: ".ljust(20), sz_retcode
    pipe_output.stdout.close()
    if sz_retcode != 0:
        if sz_retcode == 1:      warning( "7-Zip returned 1" )
        elif sz_retcode == 2:    fatal_error( "7-Zip returned 2", 7 )
        elif sz_retcode == 7:    fatal_error( "7-Zip returned 7 - command line error", 8 )
        elif sz_retcode == 8:    fatal_error( "7-Zip returned 8 - not enough memory", 9 )
        elif sz_retcode == 255:  fatal_error( "7-Zip returned 255 - process stopped by user", 9 )

    # process 7-Zip output - extract the folder structure and put it in the corresponding file
    sevenzip_lines = lines.split('\n')
    files_start = -1 # where does the file listing begin
    files_end = -1   # where does the file listing end
    number_of_files = 0
    number_of_folders = 0
    archive_files = []
    archive_folders = []
    top_level_folders = []
    standard_structure = True
    
    for i in range( 1, len( sevenzip_lines )):
        line = sevenzip_lines[i]
        if line.startswith( "-" ):
            if sevenzip_lines[ i+1 ].startswith(' '): files_end = i-1
            else: files_start = i+1
        else: # if we're in the file zone ( between -----'s )
            if files_start != -1 and files_end == -1:
                sevenzip_path = line[53:].strip()
                if line[20]=='D' and line[24]=='.':
                    number_of_folders += 1
                    #print "folder:'",sevenzip_path,"'; basename: '", os.path.basename( sevenzip_path ) + "'"
                    levels_deep = how_deep( sevenzip_path )
                    if levels_deep == 0:
                        top_level_folders.append( sevenzip_path )
                        if sevenzip_path.lower() not in CSTRIKE_STANDARD_DIRS:
                            print "not standard cstrike top-level folder: '" + sevenzip_path + "'"
                            standard_structure = False
                    archive_folders.append( sevenzip_path )
                    f.write( sevenzip_path.strip()+'\\'+ "\n")
                elif line[20]=='.' and line[24]=='A':
                    number_of_files += 1
                    #print "file:  ",sevenzip_path 
                    f.write( sevenzip_path + "\n")
                    archive_files.append( sevenzip_path )
                else:
                   warning("skipping line " + str(i) + " in the 7-Zip file listing (" + line[i] + ")")

    print "standard structure : " + str( standard_structure )
    
    # if we have at least one top-level folder that is non-standard ( ie, not "maps", "models", etc )
    # we check if the archive contains a single folder, and check it's contents for standard cstrike folders
    sf_standard_structure = True
    if standard_structure == False and len( top_level_folders ) == 1:
        print os.path.basename( map_archive ) + " contains a single top-level non-standard folder, checking it for standard folders..."
        if len( archive_folders ) >= 2:
            for folder_name in archive_folders:
                if folder_name != top_level_folders[0] and folder_name.startswith( str(top_level_folders) + sep ):
                    print "folder inside top-level folder: '" + folder_name + "'"
                    # each folder inside the non-standard folder MUST be a standard folder
                    if os.path.basename( folder_name ).lower() not in CSTRIKE_STANDARD_DIRS:
                        sf_standard_structure = False
            if sf_standard_structure == True:
                print "folder '" + top_level_folders[0] + "' contains only standard cstrike folders "
                print "extracting contents of '" + top_level_folders[0] + "' into your cstrike folder..."
                extract_command = sevenzip_exe + " x " + map_archive + " -o" + CSTRIKE_DIR + sep + "* -r"
                print "7-Zip extract command: ".ljust(20),extract_command
        else:
            fatal_error( "folder '" + top_level_folders[0] + "' does not contain any folders - cannot detect correct destination ", 7 )

    print "output len: ".ljust(20),len(sevenzip_lines)
    print "files:",number_of_files,"folders:",number_of_folders

    # else if more than one n-s csf: ERROR: cannot install - needs manual installation

    # unzip to a temp folder

    # copy needed files, ignoring images ( jpg, bmp, etc )

    # end
    print "-"*80


#------------------------------------------------------------------------------
#  LIST MAPS
#------------------------------------------------------------------------------
def list_maps():

    # add *.bsp files to the bsp_map_names list
    glob_pattern = CSTRIKE_DIR+'/maps/*.bsp'
    for f in glob.glob( glob_pattern ):
        bsp_map_names.append( os.path.basename( f )[:-4])

    # add *.nav files to the nav_map_names list
    glob_pattern = CSTRIKE_DIR+'/maps/*.nav'
    for f in glob.glob( glob_pattern ):
        nav_map_names.append( os.path.basename( f )[:-4])

    # add map names from map list files ( maplist, mapcycle, etc )
    for fname in map_list_files.keys():
        f = open( CSTRIKE_DIR + os.path.sep + fname )
        for line in f:
            map_list_files[ fname ].append( line.strip() )

#    for fname in map_list_files.keys():
#        print "maps in",fname,'(',len(map_list_files[ fname ]),"maps )"
#        for map_name in map_list_files[ fname ]:
#            print map_name.strip()

    # add all map names to a set ( so that each name appears only once )
    s = set( bsp_map_names );
    for mn in nav_map_names:
        s.add( mn );
    for fname in map_list_files.keys():
        for mn in map_list_files[ fname ]:
            s.add( mn );

    # print table header
    print '\n\n'
    print 'map name |'.rjust(20),' bsp |'.rjust(5),' nav |'.rjust(5),
    for fname in map_list_files.keys():
        print (repr(fname)+' |').rjust(15),
    print ''
    print '-'*80

    # print table rows
    for map_name in s:
        print (str(map_name)[:18]+' |').rjust(20),
        if map_name in bsp_map_names:
            print ' yes |'.center(5),
        else:
            print '  -  |'.center(5),

        if map_name in nav_map_names:
            print ' yes |'.center(5),
        else:
            print '  -  |'.center(5),

        for fname in map_list_files.keys():
            if map_name in map_list_files[ fname ]:
                print ' yes |'.center(15),
            else:
                print '  -  |'.center(15),
        print ''
        if full_graph : print '-'*80
    if not full_graph: print '-'*80



#------------------------------------------------------------------------------
#  MAIN FUNCTION
#------------------------------------------------------------------------------
if __name__ == "__main__":
    print "args: [",
    for arg in sys.argv: print arg,",",
    print "]"
    cd = sys.path[0]
    print '\nworking directory: ',cd
    folder_name = os.path.basename( cd )
#    print 'parent name: ',parent_name( cd )
#    print 'grandparent name: ',grandparent_name( cd )
#    print 'parent name full: ',parent_name_full( cd )
#    print 'grandparent name full: ',grandparent_name_full( cd )

    #--------------------------------------------------------------------------
    # figure out where is the cstrike folder
    #--------------------------------------------------------------------------
    if cd == 'cstrike':
        CSTRIKE_DIR = cd
    elif parent_name( cd ) == 'cstrike':
        CSTRIKE_DIR = parent_name_full( cd )
    elif grandparent_name( cd ) == 'cstrike':
        CSTRIKE_DIR = grandparent_name_full( cd )
    elif os.path.basename( cd ) == 'orangebox':
        CSTRIKE_DIR = cd + sep + 'cstrike'
    if not os.path.isdir( CSTRIKE_DIR ): 
        warning( "failed to auto-detetect cstrike folder" )
        

    #--------------------------------------------------------------------------
    # parse arguments
    #--------------------------------------------------------------------------
    n = len( sys.argv )
    i=1
    while i<n:
        if sys.argv[i] == "-csdir":
            if i+1>n: fatal_error("-csdir needs to be followed by the full path to cstrike", 5 )
            if os.path.isdir( sys.argv[i+1].strip()):
                CSTRIKE_DIR = sys.argv[i+1]
            else:
                print "FATAL ERROR 2: '",sys.argv[i+1].strip(),"' folder not found"
                sys.exit(2)
            i+=1
        elif sys.argv[i] == "i":
            if i==n-1: fatal_error("please provide the full path to the archive containing the map you want to install", 6 )
            if os.path.isfile( sys.argv[i+1] ):
                install_map( sys.argv[i+1] )
            else:
                print "skipping ",sys.argv[i+1],", no such file"
            i+=1
        elif sys.argv[i] == "l":
            list_maps()
        else:
            if os.path.isfile( sys.argv[i].strip() ):
                install_map( sys.argv[i].strip() )
            else:
                print "ERROR 1: file '",sys.argv[i],"' not found"
        i+=1

    print "cstrike dir: ".ljust(20), CSTRIKE_DIR
    print "map list files: ".ljust(20), map_list_files

raw_input( "Press Enter to exit..." )
