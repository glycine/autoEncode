# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     08/01/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import codecs
import json
import os
import os.path
import shutil
import sys
import time
import urllib.request
from functools import reduce
from optparse import OptionParser
from xml.etree.ElementTree import ElementTree

# 各種定数値
SERVICE_INFO_FILE = "__serviceInfo.json"
BASE_TITLE_INFO_FILE = "__baseTitleInfo.json"
SHOBOCAL_URL = "http://cal.syoboi.jp/db.php"
PROG_LOOKUP_COMMAND = "ProgLookup"
SPLIT_CHAR = "_"

def __parse_args__(args):
	#ヘルプなどの設定
	parser_config = {"usage": "%prog [オプション] [引数]: 各base_title/service内のtsファイルに対してworkspaceのディレクトリを作成します",
		"version": "%prog: ver 1.0"}
	# オプションの既定値の設定
	parser_defaults = {}
	#設定を読み込ませながら解析機を作成
	parser = OptionParser(**parser_config)
	# 既定値をまとめて設定
	parser.set_defaults(**parser_config)
	# 以下各オプションの設定
	parser.add_option( "-t", "--targetdir",
		dest = "target_directory",
		action = "store",
		type = "string",
		help = "処理対象のディレクトリを指定します",
		metavar = "TARGET_DIRECTORY")
	parser.add_option( "-c", "--configdir",
		dest = "config_directory",
		action = "store",
		type = "string",
		help = "設定ファイルが格納されたディレクトリを指定します",
		metavar = "CONFIG_DIRECTORY")
	(options, ars) = parser.parse_args()
	# 必要な引数がない場合のチェック
	if not options.target_directory:
		parser.error("処理対象のディレクトリが指定されていません")
	if not options.config_directory:
		parser.error("設定ファイルが格納されたディレクトリが指定されていません")
	service_info_file = os.path.join(options.config_directory, SERVICE_INFO_FILE)
	if not (os.path.exists(service_info_file) and os.path.isfile(service_info_file)):
		parser.error(service_info_file + "が存在しません")
	base_title_info_file = os.path.join(options.config_directory, BASE_TITLE_INFO_FILE)
	if not (os.path.exists(base_title_info_file) and os.path.isfile(base_title_info_file)):
		parser.error(base_title_info_file + "が存在しません")
	return options

def __load_info__( file_name, dir_path ):
	info_file = codecs.open( os.path.join(dir_path, file_name), encoding = 'utf-8')
	info = json.load(info_file, encoding = "utf-8")
	info_file.close()
	return info

def __get_service_dirlist__(base_title_dir, target_dir):
	service_dirlist = os.listdir( os.path.join( target_dir, base_title_dir))
	return [(base_title_dir, x) for x in service_dirlist]

def __get_base_title_and_service_list__(target_dir):
	base_title_dirlist = os.listdir(target_dir)
	base_title_and_service_list = [__get_service_dirlist__(x, target_dir) for x in base_title_dirlist]
	return reduce(lambda a,b:a+b, base_title_and_service_list)

def __get_ts_list__(base_title, service, target_dir):
	filelist = os.listdir( os.path.join(target_dir, base_title, service))
	abs_filelist = [os.path.join(target_dir, base_title, service,  x) for x in filelist]
	ts_filelist = [x for x in abs_filelist if x.endswith(".ts")]
	return [(base_title, service, x) for x in ts_filelist]

def __get_shobocal_channel_id__(my_service_name, service_info):
	service = [x for x in service_info if x["my_service_name"] == my_service_name]
	if len(service) < 1:
		return False
	return service[0]["shobocal_channel_id"]

def __get_shobocal_id__(base_title, base_title_info):
	matched_base_title = [x for x in base_title_info if x["base_title"] == base_title]
	if len(matched_base_title) < 1:
		return False
	return matched_base_title[0]["shobocal_id"], matched_base_title[0]["count_width"]

def __get_onair_time__( abs_ts_filename ):
	# TSのファイル名は，'_'で区切られている．
	# 0: iEPG上での番組タイトル
	# 1: service name
	# 2: service No
	# 3: 放送日時
	ts_filename = os.path.basename(abs_ts_filename)
	base, ext = os.path.splitext(ts_filename)
	tokens = base.split(SPLIT_CHAR)
	timeElem = time.strptime(tokens[3], "%Y%m%d-%H%M")
	year = "{0:04}".format(timeElem[0])
	month = "{0:02}".format(timeElem[1])
	day = "{0:02}".format(timeElem[2])
	hour = "{0:02}".format(timeElem[3])
	minute = "{0:02}".format(timeElem[4])
	start_time = year + month + day + "_" + hour + minute + "00"
	# end_time はstart_timeの30秒後とする
	end_time = year +month + day + "_" + hour + minute + "30"
	return start_time, end_time

def __get_program_count__(shobocal_channel_id, shobocal_id, start_time, end_time, count_width):
	url = SHOBOCAL_URL + "?Command=" + PROG_LOOKUP_COMMAND + "&TID=" + str(shobocal_id) + "&ChID=" + str(shobocal_channel_id) + "&StTime=" + start_time + "-" + end_time
	response = urllib.request.urlopen( url )
	dom = ElementTree( file = response )
	dom_root = dom.getroot()
	count = dom_root.find( 'ProgItems/ProgItem/Count' )
	count_format = "{0:0" + str(count_width) + "}"
	try:
		return count_format.format(int(count.text))
	except:
		return "Unknown"

def __generate_workspace__(ts_file, target_directory, base_title, service_name, count_str, start_time ):
	directory_name = base_title +"_" + str(count_str) + "_" + start_time
	workspace = os.path.join( target_directory, base_title, service_name, directory_name)
	if not (os.path.exists(workspace) and os.path.isdir(workspace)):
		os.makedirs(workspace)
	err_file = ts_file + ".err"
	info_file = ts_file + ".program.txt"
	if (os.path.exists(ts_file) and os.path.isfile(ts_file)):
		shutil.move(ts_file, workspace)
	else:
		print( ts_file )
		print( workspace )
	if (os.path.exists(err_file) and os.path.isfile(err_file)):
		shutil.move (err_file, workspace)
	if (os.path.exists(info_file) and os.path.isfile(info_file)):
		shutil.move (info_file, workspace)
	return

def __add_shobocal_info__(ts_filelist, service_info, base_title_info):
	shobocal_id_list = [__get_shobocal_id__(x[0], base_title_info) for x in ts_filelist]
	shobocal_channel_id_list = [__get_shobocal_channel_id__(x[1], service_info) for x in ts_filelist]
	return list(zip(
		[x[2] for x in ts_filelist],
		[x[0] for x in ts_filelist],
		[x[1] for x in ts_filelist],
		[x[0] for x in shobocal_id_list],
		shobocal_channel_id_list,
		[x[1] for x in shobocal_id_list]
		 ))

def __add_onair_time__( info_list ):
	onair_time_list = [__get_onair_time__(x[0] ) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		[x[5] for x in info_list],
		[x[0] for x in onair_time_list],
		[x[1] for x in onair_time_list]
		))

def __add_program_count__( info_list ):
	program_count_list = [__get_program_count__( x[4], x[3], x[6], x[7], x[5]) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		[x[5] for x in info_list],
		[x[6] for x in info_list],
		[x[7] for x in info_list],
		program_count_list
		))
	return

def __exec_generate_workspace__( info_list, target_root_directory):
	[__generate_workspace__( x[0], target_root_directory, x[1], x[2], x[8], x[6]) for x in info_list]
	return

def main():
	options = __parse_args__(sys.argv)
	service_info = __load_info__(SERVICE_INFO_FILE, options.config_directory)
	base_title_info = __load_info__(BASE_TITLE_INFO_FILE, options.config_directory)
	base_title_and_service_dirlist = __get_base_title_and_service_list__(options.target_directory)
	ts_filelist = reduce( lambda a,b: a+b, [__get_ts_list__(x[0], x[1], options.target_directory) for x in base_title_and_service_dirlist])
	shobocal_info = __add_shobocal_info__(ts_filelist, service_info, base_title_info)
	onair_time_info = __add_onair_time__(shobocal_info)
	program_count_info = __add_program_count__( onair_time_info )
	__exec_generate_workspace__( program_count_info, options.target_directory)


if __name__ == '__main__':
    main()
