# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     13/01/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import codecs
import json
import os.path
import shutil
import sys
from functools import reduce
from optparse import OptionParser

# 元々のキャプチャファイルを保存するためのディレクトリ名
SOURCE_DIR = "source"
# TSファイルの拡張子
TS_EXT = ".ts"
# errファイルの拡張子
ERR_EXT = ".err"
# infoファイルの拡張子
INFO_EXT = ".program.txt"
# 設定ファイルの名前
BASE_TITLE_INFO_FILE = "__baseTitleInfo.json"
UTILITY_INFO_FILE = "__utilityInfo.json"
SERVICE_INFO_FILE = "__serviceInfo.json"
# 文字列を分離するときのキャラクター
SPLIT_CHAR ="_"
# SPLITが行われたことを示すフラグファイル名
SPLIT_FLAG_FILE = "__splitted"

def __parse_arg(args):
	# ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション][引数]: 各workspace内のTSファイルを，番組情報などを元にsplitします",
							"version": "%prog : ver 1.0" }
	# オプションの既定値の設定
	parser_defaults = {"save_split_ts_files": False}
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
	parser.add_option( "-r", "--savesplittsfiles",
		dest = "save_split_ts_files",
		action = "store_true",
		help = "Split後のtsファイルを残します")
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
	util_info_file = os.path.join( options.config_directory, UTILITY_INFO_FILE )
	if not (os.path.exists( util_info_file ) and os.path.exists( util_info_file)):
		parser.error(util_info_file + "が存在しません")
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
	# SPLIT_FLAG_FILEがあれば処理対象としない
	skip_flag_file = os.path.join( workspace, SPLIT_FLAG_FILE )
	if (os.path.exists(skip_flag_file) and os.path.isfile(skip_flag_file)):
		return False
	filelist = os.listdir(workspace)
	abs_filelist = [os.path.join(workspace, x) for x in filelist]
	ts_filelist = [x for x in abs_filelist if x.endswith(TS_EXT)]
	if( len(ts_filelist) == 1 ):
		return True
	return False

def __move_source_files( workspace ):
	source_dir = os.path.join( workspace, SOURCE_DIR )
	if not (os.path.exists(source_dir) and os.path.isdir(source_dir)):
		os.makedirs(source_dir)
	filelist = os.listdir(workspace)
	abs_filelist = [os.path.join( workspace, x) for x in filelist]
	ts_filelist = [x for x in abs_filelist if x.endswith(TS_EXT)]
	if len(ts_filelist) == 0:
		return False
	ts_file = ts_filelist[0]
	err_file = ts_file + ERR_EXT
	info_file = ts_file + INFO_EXT
	shutil.move(ts_file, source_dir)
	#if (os.path.exists(err_file) and os.path.isfile(err_file)):
	if os.path.isfile( err_file ):
		shutil.move( err_file, source_dir )
		print( "move " + err_file)
	if (os.path.exists(info_file) and os.path.isfile( info_file)):
		shutil.move( info_file, source_dir)
		print( "move " + info_file)
	# 戻り値として，移動後のts_fileのパスを返す
	return os.path.join(source_dir, os.path.basename(ts_file))

def __add_ts_file_info( info_list ):
	ts_filelist = [__move_source_files(x[0]) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		ts_filelist
		))
	return

def __get_hd_sd_info_from_service( service, service_info ):
	match_service_list = [x for x in service_info if x["my_service_name"] == service]
	if len( match_service_list ) < 1:
		return True
	if match_service_list[0]["video_type"] == "sdtv":
		return False

	return True

def __get_hd_sd_info(base_title, service, base_title_info, service_info):
	match_base_title_list = [x for x in base_title_info if x["base_title"] == base_title_info]
	if len( match_base_title_list) < 1:
		return __get_hd_sd_info_from_service( service, service_info )
	match_base_title = match_base_title_list[0]
	if not match_base_title["is_hi_vision"]:
		return __get_hd_sd_info_from_service( service, service_info )
	if not match_base_title["is_hi_vision"][service]:
		return __get_hd_sd_info_from_service( service, service_info )
	return match_base_title["is_hi_vision"][service]

def __split_ts( ts_file, workspace, util_info, save_split_ts_files, is_hd ):
	ts_splitter_info = util_info["ts_splitter"]
	if is_hd:
		os.system( ts_splitter_info["exec"] + " "
			+ ts_splitter_info["outputdir_opt"] + " " + workspace + " "
			+ ts_splitter_info["opts"] + " "
			+ "\""+ ts_file + "\"")
	else:
		os.system( ts_splitter_info["exec"] + " "
			+ ts_splitter_info["outputdir_opt"] + " " + workspace + " "
			+ ts_splitter_info["sd_opts"] + " "
			+ "\""+ ts_file + "\"")
	# workspace内のTSファイルのリストを取得する
	filelist = [os.path.join( workspace, x) for x in os.listdir(workspace)]
	ts_filelist = [x for x in filelist if x.endswith(TS_EXT)]
	ts_filesize_list = [os.path.getsize(x) for x in ts_filelist]
	ts_filesize_list.sort()
	ts_filesize_list.reverse()
	max_filesize = ts_filesize_list[0]
	select_ts_filelist = [x for x in ts_filelist if os.path.getsize(x) == max_filesize]
	other_ts_filelist = [x for x in ts_filelist if os.path.getsize(x) != max_filesize ]
	if not save_split_ts_files:
		[os.remove(x) for x in other_ts_filelist]
	return select_ts_filelist[0]

def __add_split_ts_info( info_list, util_info, save_split_ts_files, base_title_info, service_info ):
	split_ts_filelist = [__split_ts(x[4], x[0], util_info, save_split_ts_files,
		__get_hd_sd_info(x[1], x[2], base_title_info, service_info))
		for x in info_list ]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		split_ts_filelist
		))

def __rename_ts( src_ts_file, workspace_name, workspace):
	tokens = workspace_name.split( SPLIT_CHAR )
	rename_ts_filename = tokens[0] + SPLIT_CHAR + tokens[1] + TS_EXT
	rename_ts_file = os.path.join(workspace, rename_ts_filename)
	shutil.move( src_ts_file, rename_ts_file )
	return rename_ts_file

def __add_rename_ts_info( info_list ):
	rename_ts_filelist = [__rename_ts( x[5], x[1], x[0] ) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		rename_ts_filelist
		))

def __copy_err_and_info_files( new_ts_file, old_ts_file, workspace ):
	old_err_file = old_ts_file + ERR_EXT
	old_info_file = old_ts_file + INFO_EXT
	new_err_file = new_ts_file + ERR_EXT
	new_info_file = new_ts_file + INFO_EXT
	shutil.copy( old_err_file, new_err_file )
	# shutil.copy( old_info_file, new_info_file )
	shutil.copy( old_info_file, workspace)
	return

def __gen_split_flag_file( workspace ):
	split_flag_file_path = os.path.join( workspace, SPLIT_FLAG_FILE )
	split_flag_file = open(split_flag_file_path, "w")
	split_flag_file.write("")
	split_flag_file.close()
	return

def main():
	options = __parse_arg(sys.argv)
	util_info = __load_info( UTILITY_INFO_FILE, options.config_directory )
	service_info = __load_info( SERVICE_INFO_FILE, options.config_directory )
	base_title_info = __load_info( BASE_TITLE_INFO_FILE, options.config_directory )
	workspace_list = __get_workspace_list(options.target_directory)
	valid_workspace_list = [x for x in workspace_list if __check_workspace(x[0]) ]
	ts_filelist = __add_ts_file_info(valid_workspace_list)
	split_ts_filelist = __add_split_ts_info(ts_filelist, util_info, options.save_split_ts_files,
		base_title_info, service_info)
	rename_ts_filelist = __add_rename_ts_info(split_ts_filelist)
	[__copy_err_and_info_files(x[5], x[4], x[0] ) for x in rename_ts_filelist]
	[__gen_split_flag_file( x[0] ) for x in rename_ts_filelist]

if __name__ == '__main__':
    main()
