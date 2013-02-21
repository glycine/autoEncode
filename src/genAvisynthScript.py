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

import codecs
import json
import os
import os.path
import re
import sys
from functools import reduce
from optparse import OptionParser

# TSファイルの拡張子
TS_EXT = ".ts"
# AVSファイルの拡張子
AVS_EXT = ".avs"
# AVISynthのテンプレートファイル名
AVI_SYNTH_TEMPLATE_FILE = "__template.avs"
PROGRAM_INFO = "__baseTitleInfo.json"
SERVICE_INFO = "__serviceInfo.json"
VIDEO_INFO = "__videoInfo.json"

def __parse_args( args ):
   # ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション][引数]: AVISynthスクリプトを作成します",
							"version": "%prog : ver 1.0" }
	# オプションの既定値の設定
	parser_defaults = {}
	# 設定を読み込ませながら解析器を作成
	parser = OptionParser( **parser_config )
	# 既定値をまとめて設定
	parser.set_defaults( **parser_defaults )
	# 以下各オプションの設定
	parser.add_option( "-t", "--targetdir",
		dest = "target_directory",
		action = "store",
		type = "string",
		help = "対象のディレクトリを指定します",
		metavar = "TARGET_DIRECTORY")
	parser.add_option( "-c", "--configdir",
		dest = "config_directory",
		action = "store",
		type = "string",
		help = "設定ディレクトリを指定します",
		metavar = "CONFIG_DIRECTORY"
		)
	# 解析実行
	(options, args) = parser.parse_args()
	# 必要な引数がない場合のチェック
	if not options.target_directory:
		parser.error("対象のディレクトリが指定されていません")
	if not options.config_directory:
		parser.error("設定ディレクトリが指定されていません")
	# 必要なディレクトリ/ファイルがあるかどうかをチェック
	if not (os.path.exists(options.target_directory) and os.path.isdir(options.target_directory)):
		parser.error("対象のディレクトリが存在しません")
	if not (os.path.exists(options.config_directory) and os.path.isdir(options.config_directory)):
		parser.error("設定ディレクトリが存在しません")
	avi_synth_template_file = os.path.join( options.config_directory, AVI_SYNTH_TEMPLATE_FILE )
	if not (os.path.exists(avi_synth_template_file) and os.path.isfile(avi_synth_template_file)):
		parser.error(avi_synth_template_file + "が存在しません")
	program_info_file = os.path.join( options.config_directory, PROGRAM_INFO)
	if not (os.path.exists(program_info_file) and os.path.isfile(program_info_file)):
		parser.error(program_info_file + "が存在しません")
	service_info_file = os.path.join( options.config_directory, SERVICE_INFO)
	if not (os.path.exists( service_info_file) and os.path.isfile(service_info_file)):
		parser.error( service_info_file + "が存在しません")
	video_info = os.path.join( options.config_directory, VIDEO_INFO)
	if not (os.path.exists(video_info) and os.path.isfile(video_info)):
		parser.error( video_info + "が存在しません")
	return options

def __load_info(file_name, dir_path):
	info_file = codecs.open( os.path.join(dir_path, file_name), encoding = 'utf-8')
	info = json.load(info_file, encoding = "utf-8")
	info_file.close()
	return info

def __get_program_dirlist(service, base_title, root_dir ):
	program_dirlist = os.listdir(os.path.join( root_dir, base_title, service))
	return [(os.path.join(root_dir, base_title, service, x), x, service, base_title) for x in program_dirlist]

def __get_service_dirlist(base_title, root_dir):
	service_dirlist = os.listdir(os.path.join(root_dir, base_title))
	program_dirlist = [__get_program_dirlist(x, base_title, root_dir) for x in service_dirlist]
	return reduce(lambda a,b:a+b, program_dirlist)

def __get_workspace_list(root_dir):
	base_title_list = os.listdir(root_dir)
	service_dirlist = [__get_service_dirlist(x, root_dir) for x in base_title_list]
	return reduce(lambda a,b:a+b, service_dirlist)

def __check_workspace( workspace ):
	# AVSファイルがあれば処理対象としない
	filelist = [ os.path.join( workspace, x) for x in os.listdir(workspace)]
	avs_filelist = [ x for x in filelist if x.endswith(AVS_EXT)]
	if len(avs_filelist) > 0:
		return False
	return True

def __get_base_filename( workspace ):
	filelist =  os.listdir(workspace)
	ts_filelist =  [x for x in filelist if x.endswith(TS_EXT)]
	if len(ts_filelist) < 1:
		return False
	base, ext = os.path.splitext( ts_filelist[0])
	return base

def __add_base_filename_info( info_list ):
	base_filename_list = [__get_base_filename( x[0] ) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		base_filename_list
		))
	return

def __get_crop( base_title, program_info ):
	info = [ x for x in program_info if x["base_title"] == base_title]
	if len(info) < 1:
		return False
	return info[0]["crop"]

def __add_crop_info( info_list, program_info ):
	crop_info_list = [__get_crop(x[3], program_info) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		crop_info_list
		))
	return

def __get_crop_width( my_service_name, service_info, video_info):
	service_list = [x for x in service_info if x["my_service_name"] == my_service_name]
	if len(service_list) < 1:
		return 0
	service = service_list[0]
	video_list = [x for x in video_info if x["video_type"] == service["video_type"]]
	if len( video_list) < 1:
		return 0
	return video_list[0]["crop_width"]

def __add_crop_width_info( info_list, service_info, video_info ):
	crop_width_info_list = [__get_crop_width( x[2], service_info, video_info) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		[x[5] for x in info_list],
		crop_width_info_list
		))
	return

def __gen_avisynth_script( base_filename, workspace, crop_width, is_crop, avs_template_path):
	avs_template_file = open( avs_template_path )
	avs_template = avs_template_file.read()
	avs_template_file.close()
	work_dir = re.sub( "\\\\", "\\\\\\\\", workspace )
	avs = re.sub( "\${BASE_FILENAME}", base_filename, avs_template)
	avs = re.sub( "\${WORK_DIR}", work_dir, avs)
	if is_crop:
		avs = re.sub("\${CROP_WIDTH}", str(crop_width), avs)
	else:
		avs = re.sub("\${CROP_WIDTH}", "0", avs)
	avs_filename = os.path.join( workspace, (base_filename + AVS_EXT ))
	avs_file = open(avs_filename, "w")
	avs_file.write(avs)
	avs_file.close()
	return avs_filename

def main():
	options = __parse_args( sys.argv )
	program_info = __load_info( PROGRAM_INFO, options.config_directory )
	service_info = __load_info( SERVICE_INFO, options.config_directory )
	video_info = __load_info( VIDEO_INFO, options.config_directory )
	workspace_info = __get_workspace_list( options.target_directory )
	valid_workspace_info = [ x for x in workspace_info if __check_workspace(x[0])]
	base_filename_info = __add_base_filename_info( valid_workspace_info )
	crop_info = __add_crop_info( base_filename_info, program_info)
	crop_width_info = __add_crop_width_info( crop_info, service_info, video_info)
	avs_template_file = os.path.join( options.config_directory, AVI_SYNTH_TEMPLATE_FILE )
	[__gen_avisynth_script( x[4], x[0], x[6], x[5], avs_template_file) for x in crop_width_info]

if __name__ == '__main__':
    main()
