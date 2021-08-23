# python
##############################################################
# © Copyright 2020 All Rights Reverved: Andrew Buttigieg 
##############################################################
import lx
import modo

capture_file_type = lx.eval('user.value applicator.capture_file_type ?')
if capture_file_type == 'Live Link Face':
    neutral_file_path = modo.dialogs.customFile('fileOpen', 'Neutral capture csv', ('csv',), ('CSV File',), ('*.csv',))
elif capture_file_type == 'Face Cap':
    neutral_file_path = modo.dialogs.customFile('fileOpen', 'Neutral capture txt', ('txt',), ('TXT File',), ('*.txt',))

if neutral_file_path != None:
    lx.eval('user.value applicator.neutral_file_path [' + neutral_file_path + ']')    
