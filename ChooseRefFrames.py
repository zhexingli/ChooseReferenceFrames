################################################################################
#                           CHOOSEREFFRAMES
#
# This script contains a function that is to select the best images to use as a
# referece frame.
#
# Author        Date        Comments
# Zhexing Li    2015-09-09  Initial Version.
# Zhexing Li    2015-09-16  Added a feature which users could specify the maximum
#                           number of frames to be stacked as a reference frame.
# Zhexing Li    2015-10-07  Revised the criteria for selecting reference frame
#			    candidates.
# Zhexing Li    2015-10-09  Added codes to check if reflist file already exists
#                           in the directory.
# Zhexing Li    2016-04-05  Improved the code on the criteria for selecting reference
#			    frame candidates.
# Zhexing Li    2016-05-13  Further improved reference frame candidates quality.
#
################################################################################


################################

# IMPORT NECESSARY MODULES

import numpy as np
import os
from sys import argv
from parseredconfig import Parse_Red_Config


################################################################################
#
# MAIN FUNCTION: CHOOSEREFFRAMES
#
################################################################################

def ChooseRefFrames(red_dir,filter_id,RedConfig = None):
    '''
    Function to select the best images to use as a referece frame.
    
    Input parameters: red_dir: directory path to the top level reduction directory
                               for this data set.
                      filter_id: the filter ID code used for this dataset
    '''

    path0 = red_dir
    path = red_dir
    filters = filter_id

    # Specify the path of reflist file if there's one.

    if path0[-1] != '/':
        path0 = path0 + '/reflist.' + filters + '.txt'
    else:
        path0 = path0 + 'reflist.' + filters + '.txt'

    # Check to see if there's reflist file in the directory.

    check_ref = os.path.isfile(path0)

    # If reflist file already exists, ignore the rest of the code, if not, keep running.

    if check_ref:
        return None
    else:

        # Generate RedConfig as a dictionary if RedConfig is not passed as an argument.
        # It calls the Red_Config(path) function below.

        if RedConfig is None:
            RedConfig = Red_Config(path)
        else:
            pass

        # Specify the path to trendlog file in the directory.

        if path[-1] != '/':
            path = path + '/trends/trendlog.imred.' + filters + '.txt'
        else:
            path = path + 'trends/trendlog.imred.' + filters + '.txt'

        # Specify the directory path for reflist file to be put in.

        dirpath = red_dir
        if dirpath[-1] != '/':
            dirpath = dirpath + '/'
        else:
            pass
    
        infile = open(path,'r')

        # Put all numbers under the same category into lists.

        name = []
        sky = []
        skysigma = []
        FWHM = []
        ellipticity = []

        for line in infile:
            if line.startswith('/'):
                col = line.split()
		if (float(col[12]) != -1 and float(col[13]) != -1 and float(col[14]) != -1
                    and float(col[15]) != -1 and float(col[16]) > 50 and float(col[17]) != -1):
                    name.append(col[0])
                    sky.append(col[10])
                    skysigma.append(col[11])
                    FWHM.append(col[12])
                    ellipticity.append(col[15])

        # Convert all numbers in the list from string to float.

        sky = map(float,sky)
        skysigma = map(float,skysigma)
        FWHM = map(float,FWHM)
        ellipticity = map(float,ellipticity)

        # Set the criteria for each category for picking the desired data sets.

        sky_limit = np.median(sky)+ 50
        skysigma_limit = np.median(skysigma) + 10
        FWHM_limit = np.median(FWHM) + 0.5
        ellipticity_limit = np.median(ellipticity) - 0.05

        # Move the reading cursor back to the beginning of the input file.

        infile.seek(0)

        # Images selected that have good data quality.

        candidate = []
        for line in infile:
            if line.startswith('/'):
                col = line.split()
                if float(col[9]) == 0.00:
                    float(col[9]) = 1.00
                    
                if (float(col[10]) < sky_limit
                    and float(col[11]) < skysigma_limit
                    and float(col[12]) < FWHM_limit
                    and float(col[15]) > ellipticity_limit
                    and (float(col[10]) / float(col[9])) <= 10):
                    candidate.append(col[0])
           
        # List the dates of all images that are picked out.

        date = []            
        for path in candidate:
            name = (os.path.basename(path)).split('-',3)
            name = '-'.join(name[:3]),'-'.join(name[3:])
            date.append(name[0])
                
        # Count the number of occurrences of each date.

        counter = {}
        for item in date:
            if item in counter:
                counter[item] = counter[item] + 1
            else:
                counter[item] = 1

        # Pick out those dates that have multiple occurrences.

        same_date = []       
        for item in counter:
            if counter[item] > 1:
                same_date.append(item)

        # Specify the path to the reflist.filter.txt file.

        outfile = open(dirpath + 'reflist.' + filters + '.txt','w')

        # Specify the maximum number of frames to be stacked as reference frame.

        max_frames = int(RedConfig['max_nim'])
    
        # Pick reference frames in three cases.
        # One: if there's only one multiple-occurrence date that has the desired data quality.

        if len(same_date) == 1:
            new_candidate = []
            for path in candidate:
                for item in same_date:
                    if item in path:
                        new_candidate.append(path)
                    else:
                        pass

            # Check if no. of images exceeds the max_frames limit and write to the reflist file.

            if (len(new_candidate) <= max_frames):
                for item in new_candidate:
                    image = os.path.basename(item)
                    outfile.write("%s\n" % image)
            else:
                fwhm = []
                for item in new_candidate:
                    infile.seek(0)
                    for line in infile:
                        if line.startswith('/'):
                            col = line.split()
                            if item == col[0]:
                                fwhm.append([col[0],float(col[12])])
                fwhm = sorted(fwhm,key = lambda tup:tup[1])
                for item in fwhm[0:max_frames]:
                    image = os.path.basename(item[0])
                    outfile.write("%s\n" % image)                

        # Two: if there're several multiple-occurrece dates that have the desired data quality.
       
        if len(same_date) > 1:
            new_candidate = []
            FWHM_low = []
            for item in same_date:
                new_candidate.insert(0,[])
                for path in candidate:
                    if item in path:
                        new_candidate[0].append(path)
            for i in range(len(new_candidate)):
                FWHM_low.insert(0,[])
                for item in new_candidate[i]:
                    infile.seek(0)
                    for line in infile:
                        if line.startswith('/'):
                            col = line.split()
                            if item  == col[0]:
                                FWHM_low[0].append(float(col[12]))
                        
            average = []
            for item in FWHM_low:
                average.append(np.average(item))
            low_index = average.index(min(average))
            new_index = -(low_index) - 1

            # Check if no. of images exceeds the max_frames limit and write to the reflist file.

            if (len(new_candidate[new_index]) <= max_frames):
                for item in new_candidate[new_index]:
                    image = os.path.basename(item)
                    outfile.write("%s\n" % image)
            else:
                fwhm = []
                for item in new_candidate[new_index]:
                    infile.seek(0)
                    for line in infile:
                        if line.startswith('/'):
                            col = line.split()
                            if item == col[0]:
                                fwhm.append([col[0],float(col[12])])
                fwhm = sorted(fwhm, key = lambda tup:tup[1])

                for item in fwhm[0:max_frames]:
                    image = os.path.basename(item[0])
                    outfile.write("%s\n" % image)

        # Three: if there's is no multiple-occurrence date that has the desired data quality.
   
        if len(same_date) == 0:
            new_candidate = []
            new_FWHM = []  
            for path in candidate:
                infile.seek(0)
                for line in infile:
                    if line.startswith('/'):
                        col = line.split()
                        if path == col[0]:
                            new_FWHM.append(col[12])

            new_FWHM = map(float,new_FWHM)
            low_FWHM = min(new_FWHM)

            infile.seek(0)
            for line in infile:
                if line.startswith('/'):
                    col = line.split()
                    if float(col[12]) == low_FWHM:
                        new_candidate.append(col[0])
            
            for item in new_candidate:
                image = os.path.basename(item)
                outfile.write("%s\n" % image)

        # Close the input and output files.
         
        infile.close()
        outfile.close()


################################################################################
#
# FUNCTION: RED_CONFIG
#
################################################################################

def Red_Config(red_dir):
    '''
    Function to read the Red.Config file in the top level reduction directory
    and to generate the information in the file as a dictionary. It calls the
    Parse_Red_Config function in the parseredconfig script.

    Input parameter: red_dir: the top level reduction directory that Red.Config
                              file is in.
    '''

    path = red_dir
    name = os.path.basename(os.path.normpath(path)) + '.Red.Config'
    if path[-1] != '/':
        path = path + '/' + name
    else:
        path = path + name
    redconfig = Parse_Red_Config(path)
    RedConfig = redconfig[0]

    return RedConfig


################################################################################
# COMMANDLINE RUN SECTION

if __name__ == '__main__':
    if len(argv) == 3:
        red_dir = argv[1]
        filter_id = argv[2]
    else:
        red_dir = raw_input('Please enter the path to the datasets reduction'
                            ' directory:\n')
        filter_id = raw_input('Please enter the filter used for the dataset:\n')

    ChooseRefFrames(red_dir,filter_id,RedConfig = None)

