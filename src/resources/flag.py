# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     14/01/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os

class filenames:
	# 字幕抽出のflagファイル名
	SUBTITLE = "__subtitle"
	# ts splitのflagファイル名
	SPLIT_TS = "__splitted"
	# CM カットのflagファイル名
	CM_CUT = "__cm_cut"

def gen_flag_file( flag_filename, dir_path ):
	flag_filepath = os.path.join( dir_path, flag_filename )
	flag_file = open( flag_filepath, "w")
	flag_file.write("")
	flag_file.close()
	return

def check_flag_existence( flag_filename, dir_path):
	flag_filepath = os.path.join( dir_path, flag_filename)
	if (os.path.isfile( flag_filepath )):
		return True
	return False