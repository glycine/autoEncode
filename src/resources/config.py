# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     02/02/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import codecs
import json
import os.path

class keys:
	class service_info:
		SERVICE_NAME = "service_name"
		MY_SERVICE_NAME = "my_service_name"
		SERVICE_NO = "service_no"
		SHOBOCAL_CHANNEL_ID = "shobocal_channel_id"
		VIDEO_TYPE = "video_type"

class filenames:
	SERVICE_INFO_FILE = "__serviceInfo.json"
	UTILITY_INFO_FILE = "__utilityInfo.json"

def config_filenames():
	return


def load_info( filename, dir_path ):
	info_file_path = os.path.join( dir_path, filename )
	if not ( os.path.exists( info_file_path )
				and os.path.isfile( info_file_path )):
		return False
	info_file = codecs.open( info_file_path, encoding = 'utf-8' )
	info = json.load( info_file, encoding = "utf-8" )
	info_file.close()
	return info
