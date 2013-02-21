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

import os
from functools import reduce

# 設定ファイル名
X264_CONFIG_FILENAME =  "__x264.json"

# 外部プログラムのパス
X264_PATH = "C:\\Utility\\x264\\x264.exe"
X264_ITVFR_PATH = "C:\\Utility\\x264\\x264itvfr.exe"

x264_config_keylist = ["keyint",
								"min-keyint",
								"scenecut",
								"bframes",
								"ref",
								"b-adapt",
								"qpmin",
								"partitions",
								"direct",
								"me",
								"merange",
								"no-psy",
								"no-fast-pskip",
								"cqm",
								"psnr",
								"ssim"]


class params:
	INTARLACED = "interlaced"
	BITRATE = "bitrate"
	PASS = "pass"
	STATS = "stats"
	OUTPUT = "output"
	SAR = "sar"

class keys:
	KEYINT = "keyint"
	MIN_KEYINT = "min-keyint"
	SCENECUT = "scenecut"
	BFRAMES = "brames"
	REF = "ref"
	B_ADOPT = "b-adopt"
	QPMIN = "qpmin"
	PARTITIONS = "partitions"
	DIRECT = "direct"
	ME = "me"
	MERANGE = "merange"
	NO_PSY = "no-psy"
	NO_FAST_PSKIP = "no-fast-pskip"
	CQM = "cqm"
	PSNR = "psnr"
	SSIM = "ssim"

def __get_option_str( key, value ):
	return " --" + key + " " + str(value) + " "

def encode( output_filepath, log_filepath, input_filepath, bitrate, n_pass, sar, is_progressive, x264_config ):
	command_str = ""
	if is_progressive:
		command_str += X264_ITVFR_PATH
	else:
		command_str += X264_PATH
	command_str += reduce(lambda a,b:a+b, [__get_option_str( x, x264_config[x]) for x in x264_config_keylist])
	command_str += (" --" + params.INTARLACED + " ") if not is_progressive else ""
	command_str += __get_option_str( params.BITRATE, bitrate)
	command_str += __get_option_str( params.PASS, n_pass)
	command_str += __get_option_str( params.STATS, log_filepath )
	command_str += __get_option_str( params.OUTPUT, output_filepath)
	command_str += __get_option_str( params.SAR, sar)
	command_str += input_filepath
	os.system( command_str )
	return
