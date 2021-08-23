# python
##############################################################
# © Copyright 2020 All Rights Reverved: Andrew Buttigieg 
##############################################################
import lx
import modo

capture_file_type = lx.eval('user.value applicator.capture_file_type ?')
if capture_file_type == 'Live Link Face':
    capture_file_path = modo.dialogs.customFile('fileOpen', 'Face capture csv', ('csv',), ('CSV File',), ('*.csv',))
elif capture_file_type == 'Face Cap':
    capture_file_path = modo.dialogs.customFile('fileOpen', 'Face capture txt', ('txt',), ('TXT File',), ('*.txt',))

if capture_file_path != None:
    lx.eval('user.value applicator.capture_file_path [' + capture_file_path + ']')    
