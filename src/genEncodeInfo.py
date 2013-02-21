# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     15/01/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import codecs
import json
import math
import os
import os.path
import sys
import wave
from functools import reduce
from optparse import OptionParser

# waveファイルの拡張子
WAVE_EXT = ".wav"
# TSファイルの拡張子
TS_EXT = ".ts"
# encode設定のファイル名
ENC_INFO_FILE = "__encInfo.json"
# 旧バージョンのシステムで設定が作成されているものは無視する
IGNORE_FLAG_FILE = "__enc.config"
# エンコード処理を飛ばすためのファイル名
ENC_SKIP_FILE = "__skip_encode"
# 各種設定ファイル名
BASE_TITLE_INFO_FILE = "__baseTitleInfo.json"
PROGRAM_INFO_FILE = "__baseTitleInfo.json"
SERVICE_INFO_FILE = "__serviceInfo.json"
VIDEO_INFO_FILE = "__videoInfo.json"

def __parse_args(args):
   # ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション][引数]: encodeの設定ファイルをworkspace内に作成します",
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
	# return [(os.path.join(root_dir, base_title, service, x), x, service, base_title) for x in program_dirlist]
	return [{"workspace_path": os.path.join(root_dir, base_title, service, x),
				"workspace": x,
				"service": service,
				"base_title": base_title} for x in program_dirlist]

def __get_service_dirlist(base_title, root_dir):
	service_dirlist = os.listdir(os.path.join(root_dir, base_title))
	program_dirlist = [__get_program_dirlist(x, base_title, root_dir) for x in service_dirlist]
	return reduce(lambda a,b:a+b, program_dirlist)

def __get_workspace_list(root_dir):
	base_title_list = os.listdir(root_dir)
	service_dirlist = [__get_service_dirlist(x, root_dir) for x in base_title_list]
	return reduce(lambda a,b:a+b, service_dirlist)

def __check_workspace( workspace ):
	# 旧バージョンのシステムのエンコード設定ファイルがある場合は無視する
	ignore_flag = os.path.join( workspace, IGNORE_FLAG_FILE)
	if (os.path.exists(ignore_flag) and os.path.isfile(ignore_flag)):
		return False
	enc_info = os.path.join( workspace, ENC_INFO_FILE)
	if not (os.path.exists(enc_info) and os.path.isfile(enc_info)):
		return True
	return False

def __get_encode_size( service_name, service_info, video_info ):
	match_service_info = [x for x in service_info if x["my_service_name"] == service_name]
	if len(match_service_info) < 1:
		return False
	match_video_info = [x for x in video_info if x["video_type"] == match_service_info[0]["video_type"]]
	if len(match_service_info) < 1:
		return False
	video_bitrate = match_video_info[0]["video_bitrate"]
	audio_bitrate = match_video_info[0]["audio_bitrate"]
	return {"encode_size": -1,
				"video_bitrate": video_bitrate,
				"audio_bitrate":  audio_bitrate}

def __get_sar( my_service_name, service_info, video_info ):
	match_service_list = [ x for x in service_info if x["my_service_name"] == my_service_name]
	if len(match_service_list) < 1:
		return False
	match_service = match_service_list[0]
	match_video_list = [x for x in video_info if match_service["video_type"] == x["video_type"]]
	if len(match_video_list) < 1:
		return False
	match_video = match_video_list[0]
	return match_video["sar"]

def __get_ts_file( workspace ):
	filelist = [ os.path.join( workspace, x) for x in os.listdir( workspace ) ]
	ts_filelist = [ x for x in filelist if x.endswith( TS_EXT )]
	if len(ts_filelist) < 1:
		return False
	return ts_filelist[0]

def __get_wave_file( ts_file ):
	base, ext = os.path.splitext( ts_file )
	return base + WAVE_EXT

def __get_progressive_mode( base_title, base_title_info ):
	match_base_title = [x for x in base_title_info if x["base_title"] == base_title ]
	if len(match_base_title ) < 1:
		return False
	return {"is_progressive": match_base_title[0]["is_progressive"]}

def __save_encode_config( encode_info ):
	config = {}
	config["encode_size"] = encode_info["encode_size"]
	config["is_progressive"] = encode_info["is_progressive"]
	config["audio_bitrate"] = encode_info["audio_bitrate"]
	config["video_bitrate"] = encode_info["video_bitrate"]
	config["sar"] = encode_info["sar"]
	file_path = os.path.join( encode_info["workspace_path"], ENC_INFO_FILE )
	file = open( file_path, "bw" )
	file.write( json.dumps(config, indent=2, ensure_ascii=False).encode("utf-8"))
	file.close()
	# エンコードをスキップさせるためのflagファイル作成
	skip_file_path = os.path.join( encode_info["workspace_path"], ENC_SKIP_FILE )
	skip_file = open( skip_file_path, "w" )
	skip_file.write( "" )
	skip_file.close()
	return

def main():
	options = __parse_args(sys.argv)
	base_title_info = __load_info( BASE_TITLE_INFO_FILE, options.config_directory )
	program_info = __load_info( PROGRAM_INFO_FILE, options.config_directory )
	service_info = __load_info( SERVICE_INFO_FILE, options.config_directory )
	video_info = __load_info( VIDEO_INFO_FILE, options.config_directory )
	workspace_info = __get_workspace_list( options.target_directory )
	workspace_info = [x for x in workspace_info if __check_workspace(x["workspace_path"]) ]
	# sar情報の追加
	[x.update({"sar": __get_sar( x["service"], service_info, video_info)}) for x in workspace_info]
	# encode_sizeとaudio_bitrateの追加
	[x.update(__get_encode_size(x["service"], service_info, video_info ))
		for x in workspace_info]
	# is_progressiveの追加
	[x.update(__get_progressive_mode(x["base_title"], base_title_info)) for x in workspace_info if __get_progressive_mode(x["base_title"], base_title_info)]
	# encodeの設定をファイルに出力
	[__save_encode_config(x) for x in workspace_info]

if __name__ == '__main__':
    main()
