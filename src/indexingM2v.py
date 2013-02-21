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
import sys
from functools import reduce
from optparse import OptionParser

# m2vファイルの拡張子
M2V_EXT = ".m2v"
# indexingのflagファイル名
INDEXING_FLAG_FILE = "__indexed"
# 設定ファイル名
UTIL_INFO_FILE = "__utilityInfo.json"

def __parse_args( args ):
   # ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション][引数]: m2vファイルのindexを作成します",
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
	util_info_file = os.path.join( options.config_directory, UTIL_INFO_FILE)
	if not (os.path.exists(util_info_file) and os.path.isfile(util_info_file)):
		parser.error( util_info_file + "が存在しません")
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
	# INDEXING_FLAG_FILEがあれば処理対象としない
	indexing_flag_file = os.path.join( workspace, INDEXING_FLAG_FILE)
	if (os.path.exists( indexing_flag_file) and os.path.isfile( indexing_flag_file)):
		return False
	# m2vファイルがないなら処理対象としない
	if not (__get_m2v_file( workspace )):
		return False
	return True

def __get_m2v_file( workspace ):
	filelist = [os.path.join( workspace, x) for x in os.listdir(workspace)]
	m2v_filelist = [x for x in filelist if x.endswith(M2V_EXT)]
	if len(m2v_filelist) < 1:
		return False
	return  m2v_filelist[0]

def __add_m2v_file_info( info_list ):
	m2v_filelist = [ __get_m2v_file(x[0]) for x in info_list ]
	return list(zip(
		[x[0] for x in info_list],
		[x[1] for x in info_list],
		[x[2] for x in info_list],
		[x[3] for x in info_list],
		m2v_filelist
		))
	return

def __indexing_m2v( m2v_file, util_info ):
	mme = util_info["mme"]
	os.system( mme["exec"] + " " + mme["opts"] + " " + m2v_file )
	return

def __gen_indexing_flag_file( workspace ):
	indexing_flag_file_path = os.path.join( workspace, INDEXING_FLAG_FILE )
	indexing_flag_file = open( indexing_flag_file_path, "w")
	indexing_flag_file.write("")
	indexing_flag_file.close()
	return

def main():
	options = __parse_args( sys.argv )
	util_info = __load_info( UTIL_INFO_FILE, options.config_directory )
	workspace_info = __get_workspace_list( options.target_directory )
	valid_workspace_info = [x for x in workspace_info if __check_workspace( x[0] )]
	m2v_info = __add_m2v_file_info(valid_workspace_info)
	[ __indexing_m2v( x[4], util_info) for x in m2v_info ]
	[ __gen_indexing_flag_file( x[0] ) for x in m2v_info ]

if __name__ == '__main__':
    main()
