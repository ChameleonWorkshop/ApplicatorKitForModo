# python
##############################################################
# © Copyright 2020 All Rights Reverved: Andrew Buttigieg 
##############################################################
import lx
import modo

mapping_file_path = modo.dialogs.customFile('fileOpen', 'Mapping csv', ('csv',), ('CSV File',), ('*.csv',))
if mapping_file_path != None:
    lx.eval('user.value applicator.mapping_file_path [' + mapping_file_path + ']')    
