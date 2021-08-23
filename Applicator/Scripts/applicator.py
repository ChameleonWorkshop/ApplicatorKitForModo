# python
#######################################################################
# Applicator Kit for Modo: Sync Apple AR Face Tracking Data to Modo
#
# Verision 1.2
#
# History:
# 1.2: Tested with Modo 15.0v1
# 1.2: Added support for both Python 2.7 and 3.7
# 1.1: Added logic to apply data to User Channels (to support RMC3)
# 1.0: Added Actor textbox back the UI
# 0.9: Added logic to get actor by selecting the actor group
# 0.9: Removed Actor from the UI
# 0.9: Removed mode from the UI
# 0.8: Added Skip Capture Frames UI
# 0.8: Added mode selection to the UI
# 0.7: In normal mode, for mesh items, parse the deformers
# 0.7: Added modes to cater for different logic
# 0.7: Set the licence file
# 0.6: Updated to allow adding data to existing Action
# 0.6: Mapping File Now Required
# 0.5: Added lpk
# 0.5: Added Action
# 0.5: Added Smoothing
# 0.4: Added Actor Selection/Application Support
# 0.4: Added Capture File Type Handling
# 0.3: Added UI using Modo forms
# 0.3: Added ValueShift logic
# 0.3: Added Smooth logic
# 0.2: Added item rotation logic
# 0.2: Reworked Application logic to traverse the selected item hoerarchy
# 0.1: Initial POC
# 
# © Copyright 2020 All Rights Reserved: Chameleon-Workshop.com 
#######################################################################
import csv
import lx
import math
import modo
import os.path

#Declare CONSTANTS (so to speak)
CAPTURE_FILE_TYPE = 'capture_file_type'
CAPTURE_FILE_PATH = 'capture_file_path'
NEUTRAL_FILE_PATH = 'neutral_file_path'
MAPPING_FILE_PATH= 'mapping_file_path'
ACTOR_NAME = 'actor_name'
ACTION_NAME = 'action_name'
START_FRAME = 'start_frame'
SKIP_FRAMES = 'skip_frames'
FILE_TYPE_CAPTURE ='Capture File'
FILE_TYPE_NEUTRAL ='Neutral File'
FILE_TYPE_MAPPING ='Mapping File'
MODE_ACTOR = 'Actor Mode'
MODE_ITEM = 'Item Mode'
BLEND_TARGET_TYPE = 'blend_target_type'
BLEND_TARGET_MORPH = 'Morph'
BLEND_TARGET_CHANNEL = 'Channel'

#######################################################################
# Gets the frames as list of dictionary items
#######################################################################
def list_csv_data(capture_path):
	result = []
	with open(capture_path) as csv_file:
		csv_reader = csv.DictReader(csv_file, delimiter=',')
		for row in csv_reader:
			result.append(row)
	return result

#######################################################################
# Determines which capture frames are applied to scene based on the scenes frame rate
# This function return a list of booleans representing which capture frames to apply
#######################################################################
def list_apply_capture_frames_to(fps, capture_frame_count):
	result = []
	apply_pattern = []

	#set the apply pattern
	if fps == 24.0:
		#YnYnYnnnYnYnnnYnYnYn|YnYnYnnnYnYnnnYnYnYn|YnYnYnnnYnYnnnYnYnYn|...
		apply_pattern = [True, False, True, False, True, False, False, False, True, False, True, False, False, False, True, False, True, False, True, False]	
	elif fps == 25.0:		
		#YnYnYnYnYnnn|YnYnYnYnYnnn|YnYnYnYnYnnn|....
		apply_pattern = [True, False, True, False, True, False, True, False, True, False, False, False]
	elif fps == 29.97:
		#Yn
		apply_pattern = [True, False]
	elif fps == 30.0:
		#Yn|Yn|Yn|...
		apply_pattern = [True, False]
	elif fps == 48.0:
		#YYYnYYnYYY|YYYnYYnYYY|YYYnYYnYYY|...
		apply_pattern = [True, True, True, False, True, True, False, True, True, True]	
	elif fps == 50.0:
		#YYYYYn|YYYYYn|YYYYYn|...
		apply_pattern = [True, True, True, True, True, False]
	else: #60
		#Y|Y|Y|...
		apply_pattern = [True]

	#string together to make the apply_capture_frames list to cover the length of the capture frames
	while len(result) <= capture_frame_count:
		result.extend(apply_pattern)
	
	#return the results
	return result

#######################################################################
# gets the face zero data 
# ARKit picks up the captured face's neautral weights differently
# so this is used to offset thoes charcteristics and give a more natral result
# the zero value is calulated by vareraging the middle thrid of frame values
# if no zero face frames are provide, then it will default to 0
#######################################################################
def get_face_neutral_from_frames(data_morph_names, face_neutral_frames):
	result = { data_morph_name : 0.0 for data_morph_name in data_morph_names }
	morph_tally = { data_morph_name : 0.0 for data_morph_name in data_morph_names }
	
	#calculate if we have data
	if face_neutral_frames != None:		
		#get the middle third
		frame_count = len(face_neutral_frames)
		frame_start = int(frame_count / 3)
		frame_end = int(frame_start) * 2		
		
		#tally up the rows
		for x in range(frame_start, frame_end):
			face_neutral_frame = face_neutral_frames[x]
			for data_morph_name in data_morph_names:
				morph_value = float(face_neutral_frame[data_morph_name])
				if morph_value > 1:
					morph_value = 1
				elif morph_value < 0:
					morph_value = 0	
				morph_tally[data_morph_name] += morph_value
		
		#divde by number of frames in the range (i.e. frame_start)
		for data_morph_name in data_morph_names:
			result[data_morph_name] = round(morph_tally[data_morph_name] / frame_start, 10)
		
	return result
	
#######################################################################
# Transforms the mapping data into the map file
#######################################################################
def get_maps(data_morph_names, data_item_names, mapping_data, blend_target_type):
	morph_result = []
	item_result = []
	channel_result = []
	
	#If not mapping file provided, create mapping data that will just pass the data through as is
	if mapping_data == None:
		#add the BlendShapes
		for data_morph_name in data_morph_names:
			mapping_row = {'Type':'BlendShape', 'Name': data_morph_name, 'Target':data_morph_name, 'Enabled':'Y', 'Multiplier':'1', 'ValueShift':'0', 'Smooth':'N'}
			morph_result.append(mapping_row)

		#add the items
		for data_item_name in data_item_names:
			target_name = data_item_name.replace('Yaw', '').replace('Pitch', '').replace('Roll', '')
			axis = data_item_name.replace('Head','').replace('LeftEye','').replace('RightEye','').replace('Yaw', 'Y').replace('Pitch', 'X').replace('Roll', 'Z')														
			mapping_row = {'Type':'Item', 'Name': data_item_name, 'Target':target_name, 'Axis':axis, 'Enabled':'Y', 'Multiplier':'1', 'ValueShift':'0', 'Smooth':'N'}
			item_result.append(mapping_row)

	else:
		#add the BlendShapes
		blend_shapes = [mapping for mapping in mapping_data if mapping['Type'] == 'BlendShape']
		for blend_shape in blend_shapes:
			if blend_shape['Target'] != '':
				if blend_target_type == BLEND_TARGET_MORPH:
					#we can target the same item to multiple targets morphs
					targets =  blend_shape['Target'].split('|')
					for target in targets:
						mapping_row = {'Type':'BlendShape', 'Name': blend_shape['Name'], 'Target':target, 'Enabled':blend_shape['Enabled'], 'Multiplier':blend_shape['Multiplier'], 'ValueShift':blend_shape['ValueShift'], 'Smooth':blend_shape['Smooth']}
						morph_result.append(mapping_row)
				elif blend_target_type == BLEND_TARGET_CHANNEL:
					targets =  blend_shape['Target'].split('|')
					for target in targets:
						channel_parts = target.split('.')
						if len(channel_parts) == 2: #got to make sure it is in the format <item>.<channel>
							channel_row = {'Type':'BlendShape', 'Name': blend_shape['Name'], 'TargetItem':channel_parts[0], 'TargetChannel':channel_parts[1], 'Enabled':blend_shape['Enabled'], 'Multiplier':blend_shape['Multiplier'], 'ValueShift':blend_shape['ValueShift'], 'Smooth':blend_shape['Smooth']}
							channel_result.append(channel_row)
		#add the items
		item_list = [mapping for mapping in mapping_data if mapping['Type'] == 'Item']	
		for item_row in item_list:
			item_name = item_row['Target']
			if len(item_name) > 0:
				item_row['Axis'] = item_name[-1:].upper()
				item_row['Target'] = item_name[:len(item_name)-2]
				item_result.append(item_row)

	return morph_result, item_result, channel_result

#######################################################################
# Apply capture values to the target channel
#######################################################################
def apply_channel(item, channel_name, capture_frames, capture_morph_name, strength_multiplier, value_shift, smooth, face_neutral, apply_capture_frames_to, start_frame, skip_frames, action_name):
	#print(item.type + ': ' + capture_morph_name + ' > ' + item.name)
	frame_to_time = lx.service.Value().FrameToTime
	current_frame_no = start_frame
	channel = item.channel(channel_name)
	
	#loop the capture frames and apply the morph strength
	capture_frames_count = len(capture_frames)
	if capture_frames_count > skip_frames:
		for y in range(skip_frames, capture_frames_count):
			capture_frame = capture_frames[y]

			#first test if we are applying this frame??
			if apply_capture_frames_to[y] == True:
				#get the strength (smooth style)
				if smooth == True:
					#smoothing applies a rolling 7 frame averages using the current frame, previous 3 frames, and next 3 frames
					range_count = 0
					range_sum = 0.0
					for x in range(y-3, y+4):
						if x >=0 and x < capture_frames_count:
							range_frame = capture_frames[x]
							range_count += 1
							range_sum += float(range_frame[capture_morph_name][:6])
					strength = range_sum / range_count
				else:
					strength = float(capture_frame[capture_morph_name][:6])
				
				#make sure the strength is within the range 0-1			
				if strength > 1:
					strength = 1
				elif strength < 0:
					strength = 0
				
				#apply the value shift
				strength = strength + value_shift
				
				#apply the miltiplier
				strength = strength * strength_multiplier
					
				#apply the Neutralizer
				#(Actual - Neutral)/(1-Neutral)
				strength = (strength - face_neutral[capture_morph_name]) / (1 - face_neutral[capture_morph_name])
				strength = round(strength ,4)
		
				#if the target type is an angle, covert value to be based between 0° & 45°
				if channel.evalType == 'angle':
					strength =  strength * 0.785398163397

				#set the keyframe
				if action_name != None:
					channel.set(strength, time=frame_to_time(current_frame_no), key=True, action=action_name)
				else:
					channel.set(strength, time=frame_to_time(current_frame_no), key=True)
				
				#incrament the frame counter
				current_frame_no += 1

#######################################################################
# Apply capture rotations to the item
#######################################################################
def apply_rotation(item, capture_frames, capture_morph_name, target_axis, strength_multiplier, value_shift, smooth, face_neutral, apply_capture_frames_to, start_frame, skip_frames, action_name):
	#print(item.type + ': ' + capture_morph_name + ' > ' + item.name + '.' + target_axis)
	frame_to_time = lx.service.Value().FrameToTime
	current_frame_no = start_frame

	#loop the capture frames and apply the morph strength
	capture_frames_count = len(capture_frames)
	if capture_frames_count > skip_frames:
		for y in range(skip_frames, capture_frames_count):
			capture_frame = capture_frames[y]

			#first test if we are applying this frame??
			if apply_capture_frames_to[y] == True:			
				#get the strength (smooth style)
				if smooth == True:
					#smoothing applies a rolling 7 frame averages using the current frame, previous 3 frames, and next 3 frames
					range_count = 0
					range_sum = 0.0
					for x in range(y-3, y+4):
						if x >=0 and x < capture_frames_count:
							range_frame = capture_frames[x]
							range_count += 1
							range_sum += float(range_frame[capture_morph_name][:6])
					strength = range_sum / range_count
				else:
					strength = float(capture_frame[capture_morph_name][:6])
				
				#make sure the strength is within the range 0-1			
				if strength > 1:
					strength = 1
				elif strength < -1:
					strength = -1
				
				#apply the value shift
				strength = strength + value_shift
				
				#convert to degrees
				strength = strength * 90
				
				#apply the miltiplier
				strength = strength * strength_multiplier
								
				#Note: No Neutralizer for rotations
				#set the rotation
				if target_axis.upper() == 'X':
					if action_name != None:
						item.rotation.x.set(math.radians(strength), time=frame_to_time(current_frame_no), key=True, action=action_name)
					else:
						item.rotation.x.set(math.radians(strength), time=frame_to_time(current_frame_no), key=True)
				elif target_axis.upper() == 'Y':
					if action_name != None:
						item.rotation.y.set(math.radians(strength), time=frame_to_time(current_frame_no), key=True, action=action_name)
					else:
						item.rotation.y.set(math.radians(strength), time=frame_to_time(current_frame_no), key=True)
				elif target_axis.upper() == 'Z':
					if action_name != None:
						item.rotation.z.set(math.radians(strength), time=frame_to_time(current_frame_no), key=True, action=action_name)
					else:
						item.rotation.z.set(math.radians(strength), time=frame_to_time(current_frame_no), key=True)
				
				#incrament the frame counter
				current_frame_no += 1

#######################################################################
# Process the items
#######################################################################
def process_item(item, capture_frames, face_neutral, morph_map, item_map, channel_map, apply_capture_frames, start_frame, skip_frames, action_name, mode, blend_target_type):
	#############################
	# Morph Mapping logic
	#############################
	#get the morph_map items that match the item's name (that are enabled)
	if blend_target_type == BLEND_TARGET_MORPH:
		morph_maps = [mapping for mapping in morph_map if mapping['Target'].upper() == item.name.upper() and mapping['Enabled'].upper() == 'Y']
		if item.type == 'morphDeform' and len(morph_maps) > 0:
			#get the Multiplier
			strength_multiplier = float(morph_maps[0]['Multiplier'])
			value_shift = float(morph_maps[0]['ValueShift'])
			smooth = (morph_maps[0]['Smooth'].upper() == 'Y')
			
			#apply the morph maps
			#we only apply one item to the morph as multiple will just override previous runs
			apply_channel(item, 'strength', capture_frames, morph_maps[0]['Name'], strength_multiplier, value_shift, smooth, face_neutral, apply_capture_frames_to, start_frame, skip_frames, action_name)

	#############################
	# Channel Mapping logic
	#############################
	elif blend_target_type == BLEND_TARGET_CHANNEL:
		channel_maps = [channel for channel in channel_map if channel['TargetItem'].upper() == item.name.upper() and channel['Enabled'].upper() == 'Y']
		if len(channel_maps) > 0:
			for map in channel_maps:
				if map['TargetChannel'] in item.channelNames:
					strength_multiplier = float(map['Multiplier'])
					value_shift = float(map['ValueShift'])
					smooth = (map['Smooth'].upper() == 'Y')
					#print(item.name + ' \ ' + map['TargetChannel'] + ' \ ' + map['Name'])
					apply_channel(item, map['TargetChannel'], capture_frames, map['Name'], strength_multiplier, value_shift, smooth, face_neutral, apply_capture_frames_to, start_frame, skip_frames, action_name)

	#############################
	# Item Mapping logic
	#############################
	#get the item_map items that match the item's name (that are enabled)
	item_maps = [mapping for mapping in item_map if mapping['Target'] == item.name and mapping['Enabled'].upper() == 'Y']
	if (item.type == 'locator' or item.type == 'mesh') and len(item_maps) > 0:	
		for map in item_maps:
			#get the Multiplier
			strength_multiplier = float(map['Multiplier'])
			value_shift = float(map['ValueShift'])
			smooth = (map['Smooth'].upper() == 'Y')
			
			#apply the rotations
			#we only apply one item to the morph as multiple will just override previous runs
			apply_rotation(item, capture_frames, map['Name'], map['Axis'], strength_multiplier, value_shift, smooth, face_neutral, apply_capture_frames_to, start_frame, skip_frames, action_name)

	#############################
	# process the morph deformers for meshes 
	# (Item Mode Only)
	#############################
	if item.type == 'mesh' and mode == MODE_ITEM:
		for deformer in item.deformers:
			if deformer.type == 'morphDeform':
				process_item(deformer, capture_frames, face_neutral, morph_map, item_map, channel_map, apply_capture_frames, start_frame, skip_frames, action_name, mode, blend_target_type)

	#############################
	# process the child items 
	# (Item Mode Only)
	#############################
	if mode == MODE_ITEM:
		child_items = item.children()
		for child_item in child_items:
			process_item(child_item, capture_frames, face_neutral, morph_map, item_map, channel_map, apply_capture_frames, start_frame, skip_frames, action_name, mode, blend_target_type)

#######################################################################
# Validate the file
#######################################################################
def validate_file(file_path, file_type, file_required, capture_file_type):
	result = True
	validation_message = ''

	#set file extension type
	if capture_file_type == 'Live Link Face':
		required_file_extension = '.csv'
		required_file_extension_name = 'CSV'
	elif capture_file_type == 'Face Cap':
		required_file_extension = '.txt'
		required_file_extension_name = 'TXT'
	file_extension = file_path[-4:].lower()

	#fiel path clean-up
	if file_path == None:
		file_path = ''
	file_path = file_path.strip()

	#file path can be blank if not required	
	if file_path == '' and file_required == False:
		result = True
	#make sure a file path is specified
	elif file_path == '' and file_required == True:
		validation_message = file_type + ' is required'
		result = False
	#make sure the file exists
	elif os.path.exists(file_path) == False:
		validation_message = 'Specified ' + file_type + ' does not exist:' + '\n' + file_path
		result = False
	#make sure the file ahs the right extension
	elif file_extension != required_file_extension:
		validation_message = 'Incorrect ' + file_type + ' type. Please select a ' + required_file_extension_name + ' file.'
		result = False

	#alert the issue (if one)
	if result == False:
		modo.dialogs.alert('Validation error', validation_message, dtype='warning')

	return result

#######################################################################
# Validate the scene's frame rate
#######################################################################
def validate_fps(supported_fps, fps):
	result = True

	if fps not in supported_fps:
		result = False

	if result == False:
		modo.dialogs.alert('Unsupported frame rate', 'Unsupported Frame Rate' + '\n' 
			+ 'Supported Frame Rates: ' + ', '.join(str(x) for x in supported_fps), dtype='warning')

	return result

#######################################################################
# Validate the action name
# If the action name exists, then make sure it is ok to add the data to the action
#######################################################################
def validate_action(item, action_name):
	result = True
	if item.type == 'actor' and action_name.strip() != '':
		#print(dir(item))
		for child_item in item.items:
			if child_item.type == 'actionclip' and action_name.strip().lower() == child_item.name.lower():
				if modo.dialogs.yesNo('Action exists', 'Action "' + action_name + '" already exists for "' + item.name + '".' + '\n \n'
					+ 'Add capture data to the action?'
					) != 'yes':
					result = False #set to false to stop processing
				break
	return result

#######################################################################
# Main Execution
#######################################################################
scene = modo.Scene()
mesh_item = None
supported_fps = (60.0, 50.0, 48.0, 30.0, 29.97, 25.0, 24.0)
data_morph_names = ['eyeBlinkRight', 'eyeLookDownRight', 'eyeLookInRight', 'eyeLookOutRight', 'eyeLookUpRight', 'eyeSquintRight', 'eyeWideRight', 'eyeBlinkLeft', 'eyeLookDownLeft', 'eyeLookInLeft', 'eyeLookOutLeft', 'eyeLookUpLeft', 'eyeSquintLeft', 'eyeWideLeft', 'jawForward', 'jawRight', 'jawLeft', 'jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthRight', 'mouthLeft', 'mouthSmileRight', 'mouthSmileLeft', 'mouthFrownRight', 'mouthFrownLeft', 'mouthDimpleRight', 'mouthDimpleLeft', 'mouthStretchRight', 'mouthStretchLeft', 'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper', 'mouthPressRight', 'mouthPressLeft', 'mouthLowerDownRight', 'mouthLowerDownLeft', 'mouthUpperUpRight', 'mouthUpperUpLeft', 'browDownRight', 'browDownLeft', 'browInnerUp', 'browOuterUpRight', 'browOuterUpLeft', 'cheekPuff', 'cheekSquintRight', 'cheekSquintLeft', 'noseSneerRight', 'noseSneerLeft', 'tongueOut']
data_item_names = ['HeadYaw', 'HeadPitch', 'HeadRoll', 'LeftEyeYaw', 'LeftEyePitch', 'LeftEyeRoll', 'RightEyeYaw', 'RightEyePitch', 'RightEyeRoll']
root_item = None

#############################
# get the parameter values
#############################
params = {}
params[CAPTURE_FILE_TYPE] = lx.eval('user.value applicator.capture_file_type ?')
params[CAPTURE_FILE_PATH] = lx.eval('user.value applicator.capture_file_path ?')
params[NEUTRAL_FILE_PATH] = lx.eval('user.value applicator.neutral_file_path ?')
params[MAPPING_FILE_PATH] = lx.eval('user.value applicator.mapping_file_path ?')
params[ACTOR_NAME] = lx.eval('user.value applicator.actor_name ?')
params[ACTION_NAME] = lx.eval('user.value applicator.action_name ?')
params[START_FRAME] = lx.eval('user.value applicator.start_frame ?')
params[SKIP_FRAMES] = lx.eval('user.value applicator.skip_frames ?')
params[BLEND_TARGET_TYPE] = lx.eval('user.value applicator.blend_target_type ?')

#############################
# Get the root item
#############################
#get the actor (if specified)
if len(params[ACTOR_NAME].strip()) > 0:
	has_actor = False
	actor_names = []
	for actor in scene.getGroups(gtype='actor'):
		actor_names.append(actor.name)
		if params[ACTOR_NAME].strip().lower() == actor.name.lower():
			root_item = actor
			has_actor = True
			break
	if has_actor == False:
		#we cannot find the specified actor
		modo.dialogs.alert('Bad Actor', '"' + params[ACTOR_NAME] + '" not in scene.' + '\n' 
			+ 'Available Actors: ' + '; '.join(str(x) for x in actor_names), dtype='error')
#get the selected item
elif len(scene.selected) == 1:
	root_item = scene.selected[0]
#sometime the scene is included in the select, so grab the second item
elif len(scene.selected) == 2:
	root_item = scene.selected[1]
else:
	modo.dialogs.alert('Select item', 'First select target from the scene.', dtype='warning')

#############################
# Process the item
#############################
if root_item != None:
	#for actors, get the actor object as root item will be a group object
	if root_item.type == 'actor':
		for actor in scene.getGroups(gtype='actor'):
			if actor.name == root_item.name:
				root_item = actor
				break

	#validate the input
	valid_fps = validate_fps(supported_fps, scene.fps)
	valid_capture_file = validate_file(params[CAPTURE_FILE_PATH], FILE_TYPE_CAPTURE, True, params[CAPTURE_FILE_TYPE])
	valid_mapping_file = validate_file(params[MAPPING_FILE_PATH], FILE_TYPE_MAPPING, True, params[CAPTURE_FILE_TYPE])
	valid_neutral_file = validate_file(params[NEUTRAL_FILE_PATH], FILE_TYPE_NEUTRAL, False, params[CAPTURE_FILE_TYPE])
	valid_action = validate_action(root_item, params[ACTION_NAME])

	#validation passed
	if valid_fps == True and valid_capture_file == True and valid_neutral_file == True and valid_mapping_file == True and valid_action == True:
		#final confirm
		if params[NEUTRAL_FILE_PATH] == None:
			neutral_caption = '(none)'
		else:
			neutral_caption = params[NEUTRAL_FILE_PATH]
			
		if params[MAPPING_FILE_PATH] == None:
			mapping_file_caption = '(none)'
		else:
			mapping_file_caption = params[MAPPING_FILE_PATH]
		
		action_message = ''
		if root_item.type == 'actor':
			target_type = 'Actor'
			action_message = '  - Action: ' + params[ACTION_NAME] + '\n'
		else:
			target_type = 'Item'

		confirmation_message = ('Selected values: ' + '\n'
			+ '  - Target ' + target_type + ': ' + root_item.name + '\n'
			+ action_message
			+ '  - Target type: ' + root_item.type + '\n'
			+ '  - BlendShape target type: ' + str(params[BLEND_TARGET_TYPE]) + '\n'
			+ '  - Start frame: ' + str(params[START_FRAME]) + '\n'
			+ '  - Skip capture frames: ' + str(params[SKIP_FRAMES]) + '\n'
			+ '  - Capture file: ' + params[CAPTURE_FILE_PATH] + '\n'
			+ '  - Mapping file: ' + params[MAPPING_FILE_PATH] + '\n'
			+ '  - Neutral file: ' + params[NEUTRAL_FILE_PATH] + '\n \n'
			+ 'Apply data?'
		)
			
		if(modo.dialogs.yesNo('Apply Data?', confirmation_message) == 'yes'):
			#############################
			# Apply the data to the scene
			#############################
			
			#get the capture frames from the file
			capture_frames = list_csv_data(params[CAPTURE_FILE_PATH])

			#get face neutral frames
			face_neutral_frames = None
			if params[NEUTRAL_FILE_PATH] != '':
				face_neutral_frames = list_csv_data(params[NEUTRAL_FILE_PATH])
			
			#get the face zero values
			face_neutral = get_face_neutral_from_frames(data_morph_names, face_neutral_frames)

			#get the mapping data
			mapping_data = None
			if params[MAPPING_FILE_PATH] != '':
				mapping_data = list_csv_data(params[MAPPING_FILE_PATH])
			
			#get the morph map
			morph_map, item_map, channel_map = get_maps(data_morph_names, data_item_names, mapping_data, params[BLEND_TARGET_TYPE])
			
			#see which frames we are apply the capture data to
			#these are the frames from the file we are to apply to the scene 
			apply_capture_frames_to = list_apply_capture_frames_to(scene.fps, len(capture_frames))

			#apply the data
			if root_item.type == 'actor':
				action_name = None
				if params[ACTION_NAME].strip() != '':
					action = None
					action_exists = False
					action_name = params[ACTION_NAME].strip()

					#check if the action exists
					for child_item in root_item.items:
						if child_item.type == 'actionclip' and action_name.strip().lower() == child_item.name.lower():
							action_exists = True
							action = child_item
							break
					
					#add an action if new
					#print("action_exists: " + str(action_exists))
					if action_exists == False:
						action = scene.addItem('actionclip', name=action_name)
						root_item.addItems(action)

					#active the action
					action.active = True
					lx.eval('select.item {%s} set' % root_item.id)
					lx.eval('layer.active {%s} type:actr' % action.id)

				#for actors, we loop through it's items collection
				for actor_item in root_item.items:
					process_item(actor_item, capture_frames, face_neutral, morph_map, item_map, channel_map, apply_capture_frames_to, params[START_FRAME], params[SKIP_FRAMES], action_name, MODE_ACTOR, params[BLEND_TARGET_TYPE])
				
				#for channel mode, we loop the actors's group channels and apply the data
				if params[BLEND_TARGET_TYPE] == BLEND_TARGET_CHANNEL:
					for groupChannel in actor.groupChannels:
						channel_maps = [channel for channel in channel_map if channel['TargetItem'].upper() == groupChannel.item.name.upper() and channel['TargetChannel'].upper() == groupChannel.name.upper() and channel['Enabled'].upper() == 'Y']
						if len(channel_maps) > 0:
							for map in channel_maps:
								strength_multiplier = float(map['Multiplier'])
								value_shift = float(map['ValueShift'])
								smooth = (map['Smooth'].upper() == 'Y')
								apply_channel(groupChannel.item, groupChannel.name, capture_frames, map['Name'], strength_multiplier, value_shift, smooth, face_neutral, apply_capture_frames_to, params[START_FRAME], params[SKIP_FRAMES], action_name)
			else:
				#process the selected item
				process_item(root_item, capture_frames, face_neutral, morph_map, item_map, channel_map, apply_capture_frames_to, params[START_FRAME], params[SKIP_FRAMES], None, MODE_ITEM, params[BLEND_TARGET_TYPE])
			
			#alert complete
			modo.dialogs.alert('Processing complete', 'Processing completed. Face capture data has been applied', dtype='info')
		