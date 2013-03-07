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
# 元々のソースファイルが入ったディレクトリ名
SOURCE_DIR = "source"
# 文字列を分割する際のキャラクター
SPLIT_CHAR = "_"
# DEMUXが行われた事を示すフラグファイル名
DEMUX_FLAG_FILE = "__demuxed"
# 設定ファイルの名前
UTIL_INFO_FILE = "__utilityInfo.json"
SERVICE_INFO_FILE = "__serviceInfo.json"

def __parse_args(args):
   # ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション][引数]: TSファイルをdemuxします",
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
	# DEMUX_FLAG_FILEがあれば処理対象としない
	demux_flag_file = os.path.join( workspace, DEMUX_FLAG_FILE )
	if (os.path.exists( demux_flag_file ) and os.path.isfile( demux_flag_file)):
		return False
	return True

def __get_ts_file( workspace ):
	filelist = [ os.path.join( workspace, x ) for x in os.listdir( workspace )]
	ts_filelist = [x for x in filelist if x.endswith(TS_EXT)]
	if len(ts_filelist) < 1:
		return False
	return ts_filelist[0]

def __add_ts_file_info( info_list ):
	ts_filelist = [__get_ts_file( x[0] ) for x in info_list ]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		ts_filelist
		))

def __get_iepg_title( workspace ):
	source_dir = os.path.join(workspace, SOURCE_DIR )
	filelist = [ os.path.join( source_dir, x) for x in os.listdir( source_dir)]
	ts_filelist = [x for x in filelist if x.endswith(TS_EXT)]
	if len(ts_filelist) <1:
		return False
	ts_file = os.path.basename( ts_filelist[0] )
	base, ext = os.path.splitext( ts_file )
	tokens = base.split( SPLIT_CHAR )
	return tokens[0], tokens[2]

def __add_iepg_title_info( info_list ):
	iepg_info_title_list = [__get_iepg_title(x[0]) for x in info_list]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		[x[0] for x in iepg_info_title_list],
		[x[1] for x in iepg_info_title_list]
		))

def __analyse_iepg_title( iepg_title ):
	r = re.compile(r"\[.+?\]")
	matches = r.findall(iepg_title)
	flag_removed_iepg_title = re.sub( r"\[.+?\]", "", iepg_title)
	## flagを探す
	## 判別に利用するFlag
	# [字]: 字幕がある
	# [二]: 二ヶ国語放送
	# [多]: 複数音声ストリーム
	# [SS]: サラウンド
	## 無視するフラグ
	# [S]: ステレオ
	# [無]: 無料
	# [新]: 新番組
	# [終]: 最終回
	# [デ]: 番組連動データ放送
	# [HV]: ハイビジョン？
	sub_title = False
	if "[字]" in matches:
		sub_title = True
	multi_language = False
	if "[二]" in matches:
		multi_language = True
	multi_sound_stream = False
	if "[多]" in matches:
		multi_sound_stream = True
	surround = False
	if "[SS]" in matches:
		surround = True
	return flag_removed_iepg_title, (sub_title, multi_language, multi_sound_stream, surround)

def __add_iepg_flag_info( info_list ):
	iepg_flag_list = [__analyse_iepg_title(x[5]) for x in info_list]
	return list(zip (
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		[x[4] for x in info_list],
		[x[5] for x in info_list],
		[x[6] for x in info_list],
		[y[0] for y in iepg_flag_list],
		[y[1] for y in iepg_flag_list]
		))

def __demux_ts( ts_file, service_no, workspace, iepg_flags, util_info ):
	bon_ts_demux_info = util_info["bon_ts_demux"]
	base, ext = os.path.splitext( ts_file )
	# ビデオ & ステレオ出力
	os.system( bon_ts_demux_info["exec"] + " "
		+ bon_ts_demux_info["input_file_opt"] + " " + ts_file + " "
		+ bon_ts_demux_info["output_file_opt"] + " " + base + " "
		+ bon_ts_demux_info["service_no_opt"] + " " + service_no + " "
		+ bon_ts_demux_info["video_and_wave_demux"] + " "
		+ bon_ts_demux_info["stereo_sound_opt"] + " "
		+ bon_ts_demux_info["opts"]
		)
	if (iepg_flags[1] or iepg_flags[2]): #二ヶ国語放送と複数音声ストリーム
		os.system( bon_ts_demux_info["exec"] + " "
			+ bon_ts_demux_info["input_file_opt"] + " " + ts_file + " "
			+ bon_ts_demux_info["output_file_opt"] + " " + (base + "_main") + " "
			+ bon_ts_demux_info["service_no_opt"] + " " + service_no + " "
			+ bon_ts_demux_info["wave_demux"] + " "
			+ bon_ts_demux_info["main_sound_opt"] + " "
			+ bon_ts_demux_info["opts"]
			)
		os.system( bon_ts_demux_info["exec"] + " "
			+ bon_ts_demux_info["input_file_opt"] + " " + ts_file + " "
			+ bon_ts_demux_info["output_file_opt"] + " " + (base + "_sub") + " "
			+ bon_ts_demux_info["service_no_opt"] + " " + service_no + " "
			+ bon_ts_demux_info["wave_demux"] + " "
			+ bon_ts_demux_info["sub_sound_opt"] + " "
			+ bon_ts_demux_info["opts"]
			)
	if iepg_flags[3]: # aacをdemuxする
		os.system( bon_ts_demux_info["exec"] + " "
			+ bon_ts_demux_info["input_file_opt"] + " " + ts_file + " "
			+ bon_ts_demux_info["output_file_opt"] + " " + base + " "
			+ bon_ts_demux_info["service_no_opt"] + " " + service_no + " "
			+ bon_ts_demux_info["aac_demux"] + " "
			+ bon_ts_demux_info["surround_sound_opt"] + " "
			+ bon_ts_demux_info["opts"]
			)
	return

def __gen_demux_flag_file( workspace ):
	demux_flag_file_path = os.path.join( workspace, DEMUX_FLAG_FILE )
	demux_flag_file = open( demux_flag_file_path, "w" )
	demux_flag_file.write("")
	demux_flag_file.close()
	return

def main():
	options = __parse_args(sys.argv)
	util_info = __load_info( UTIL_INFO_FILE, options.config_directory )
	workspace_info = __get_workspace_list( options.target_directory )
	valid_workspace_info = [ x for x in workspace_info if __check_workspace(x[0])]
	ts_file_info = __add_ts_file_info( valid_workspace_info )
	iepg_title_info_list = __add_iepg_title_info( ts_file_info)
	iepg_flag_info_list = __add_iepg_flag_info( iepg_title_info_list)
	[__demux_ts( x[4], x[6], x[0], x[8], util_info) for x in iepg_flag_info_list]
	[__gen_demux_flag_file( x[0] ) for x in iepg_flag_info_list]

if __name__ == '__main__':
    main()
