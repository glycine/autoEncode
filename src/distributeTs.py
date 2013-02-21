# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        distributeTs
# Purpose:
#
# Author:      glycine
#
# Created:     31/12/2012
# Copyright:   (c) glycine 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import codecs
import json
import ntpath
import sys
import os
import os.path
import shutil
from optparse import OptionParser

# 各種定数値
ERR_FILE_EXT = ".err"
INFO_FILE_EXT = ".program.txt"
SERVICE_INFO_FILE = "__serviceInfo.json"
BASE_TITLE_INFO_FILE = "__baseTitleInfo.json"
SPLIT_TOKEN = "_"


def __parse_args__(args):
   # ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション] [引数]: TSファイルをbase_title/serviceのディレクトリに移動します",
	                  "version": "%prog : ver 1.0" }
	# オプションの既定値の設定
	parser_defaults = {"no_check_finished": False}
	# 設定を読み込ませながら解析気を作成
	parser = OptionParser(**parser_config)
	# 既定値をまとめて設定
	parser.set_defaults(**parser_defaults)
	# 以下，各オプションの設定
	# -fオプションをつけるとfilenameに後ろのファイル名が代入される
	parser.add_option("-s", "--srcdir",
		dest = "src_directory",
		action = "store",
		type = "string",
		help = "読込元のディレクトリを指定します",
		metavar ="SRC_DIRECTORY")
	parser.add_option("-d", "--destdir",
		dest = "dest_directory",
		action = "store",
		type = "string",
		help = "出力先のディレクトリを指定します")
	parser.add_option("-c", "--configdir",
		dest = "config_directory",
		action = "store",
		type = "string",
		help = "設定ファイルが格納されたディレクトリを指定します",
		metavar = "CONFIG_DIRECTORY")
	parser.add_option("-n", "--no-check-finished",
		dest = "no_check_finished",
		action = "store_true",
		help = "TSファイルのキャプチャ終了のチェックをしません")
	#解析実行
	(options, args) = parser.parse_args()
	# 必要な引数がない場合のチェック
	if not options.src_directory:
		parser.error("ルートディレクトリが指定されていません")
	if not options.dest_directory:
		parser.error("出力先のディレクトリが指定されていません")
	if not options.config_directory:
		parser.error("設定ファイルが格納されたディレクトリが指定されていません")
	# 必要ファイルがあるかどうかをチェック
	if not os.path.isdir(options.src_directory):
		parser.error("指定されたソースディレクトリが存在しません")
	service_info_file = os.path.join(options.config_directory, SERVICE_INFO_FILE)
	if not (os.path.exists(service_info_file) and os.path.isfile(service_info_file)):
		parser.error(SERVICE_INFO_FILE + "が指定されたディレクトリ内に存在しません")
	return options

def __get_ts_filelist__(dir_path):
	filelist = os.listdir(dir_path)
	abs_filelist = [os.path.join(dir_path, x) for x in filelist]
	ts_filelist = [x for x in abs_filelist if x.endswith(".ts")]
	return ts_filelist

def __check_capture_finished__(ts_file):
	err_file = ts_file + ERR_FILE_EXT
	info_file = ts_file + INFO_FILE_EXT
	if not os.path.isfile( err_file ):
		return False
	if not os.path.isfile(info_file):
		return False
	return True

def __load_info__( info_file, dir_path ):
	service_info_file = codecs.open( os.path.join(dir_path, info_file), encoding='utf-8')
	service_info = json.load(service_info_file, encoding="utf-8")
	service_info_file.close()
	return service_info

def __get_service_and_program_name__( ts_filename ):
	base, ext = os.path.splitext(os.path.basename(ts_filename))
	tokens = base.split(SPLIT_TOKEN)
	# 0番目：iepg上のprogram name
	# 1番目：iepg上のservice name
	# 2番目：iepg上のservice No.
	# 3番目：放送日時
	return tokens[1], tokens[0], ts_filename

def __get_my_service_name__(service_name, service_info ):
	matched_service_info = [x for x in service_info if x["service_name"] == service_name]
	if len(matched_service_info) == 0:
		return False
	return matched_service_info[0]["my_service_name"]

def __get_my_base_title__( program_name, base_title_info ):
	# matching_strで示される文字列のリストの中で，program_name中に含まれるものがあれば残す
	matched_base_title_info = [x for x in base_title_info if len([y for y in x["matching_str"] if program_name.find(y) >= 0]) > 0]
	if len(matched_base_title_info) == 0:
		return False
	return matched_base_title_info[0]["base_title"]

def __get_my_service_name_and_base_title__(service_name, program_name, ts_filename, service_info, base_title_info ):
	my_service_name = __get_my_service_name__(service_name, service_info)
	base_title = __get_my_base_title__(program_name, base_title_info)
	return my_service_name, base_title, ts_filename

def __distribute_ts_file__( my_service_name, base_title, ts_filename, dest_dir):
	distribute_dir = os.path.join(dest_dir, base_title, my_service_name)
	if not (os.path.exists(distribute_dir) and os.path.isdir(distribute_dir)):
		os.makedirs(distribute_dir)
	shutil.move(ts_filename, distribute_dir)
	err_file = ts_filename + ERR_FILE_EXT
	if (os.path.exists(err_file) and os.path.isfile(err_file)):
		shutil.move(err_file, distribute_dir)
	info_file = ts_filename + INFO_FILE_EXT
	if (os.path.exists(info_file) and os.path.isfile(info_file)):
		shutil.move(info_file, distribute_dir)
	return

def main():
	options = __parse_args__(sys.argv)
	ts_filelist = __get_ts_filelist__(options.src_directory)
	if not (options.no_check_finished):
		ts_filelist = [x for x in ts_filelist if __check_capture_finished__(x)]
	service_info = __load_info__(SERVICE_INFO_FILE, options.config_directory)
	base_title_info = __load_info__(BASE_TITLE_INFO_FILE, options.config_directory)
	service_and_program_name_list = [__get_service_and_program_name__(x) for x in ts_filelist]
	# service nameが定義されていないものを除去
	service_and_program_name_list = [x for x in service_and_program_name_list if __get_my_service_name__(x[0], service_info) ]
	# matching_strで見つからないものを除去
	service_and_program_name_list = [x for x in service_and_program_name_list if __get_my_base_title__(x[1], base_title_info)]
	# service nameとprogram_nameを自分の定義している文字列に置き換え
	my_service_name_and_base_title_list = [__get_my_service_name_and_base_title__(x[0], x[1], x[2], service_info, base_title_info) for x in service_and_program_name_list]
	# tsファイルとerrファイルとinfoファイルを移動させる
	[__distribute_ts_file__(x[0], x[1], x[2], options.dest_directory) for x in my_service_name_and_base_title_list]

if __name__ == '__main__':
    main()
