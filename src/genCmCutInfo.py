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
import sys
from optparse import OptionParser
# 自前のモジュール群
from resources import config
from resources import flag
from resources import logo
from resources import workspace

class keys:
	CM_INFO_FILENAME = "cm_info_filename"

class consts:
	M2V_EXT = ".m2v"
	CM_INFO_EXT = ".cmCutInfo"

def __parse_args( args ):
	# ヘルプなどの設定
	parser_config = { "usage": "%prog [オプション...][引数]",
							"version": "%prog : ver 1.0" }

	# オプションの既定値の設定
	parser_defaults = {}

	# 設定を読み込ませながら解析器を作成
	parser = OptionParser( **parser_config )

	# 既定値をまとめて設定
	parser.set_defaults( **parser_defaults )

	# オプションの設定
	parser.add_option( "-t", "--targetdir",
		dest = "target_directory",
		action = "store",
		type = "string",
		help = "処理対象のルートディレクトリを指定します",
		metavar = "TARGET_DIRECTORY")
	parser.add_option( "-c", "--configdir",
		dest = "config_directory",
		action = "store",
		type = "string",
		help = "設定ファイルが格納されたディレクトリを指定します",
		metavar = "CONFIG_DIRECTORY")
	parser.add_option( "-l", "--logodir",
		dest = "logo_directory",
		action = "store",
		type = "string",
		help = "ロゴ情報ファイルが格納されたディレクトリを指定します",
		metavar = "LOGO_DIRECTORY")

	# 解析実行
	(options, args) = parser.parse_args()

	# 必要なオプションの有無チェック
	if not options.target_directory:
		parser.error( "処理対象のルートディレクトリが指定されていません")
	if not options.config_directory:
		parser.error( "設定ファイルが格納されたディレクトリが指定されていません")
	if not options.logo_directory:
		parser.error( "ロゴ情報ファイルが格納されたディレクトリが指定されていません")
	# 指定されたオプションの有効性チェック
	if not (os.path.isdir( options.target_directory )):
		parser.error( options.target_directory, "は存在しません" )
	if not (os.path.isdir( options.config_directory )):
		parser.error( options.config_directory, "は存在しません" )
	if not (os.path.isdir( options.logo_directory )):
		parser.error( options.logo_directory, "は存在しません")
	return options

def __get_video_type( my_service_name , service_info_list ):
	matched_list = [x for x in service_info_list
				if x[config.keys.service_info.MY_SERVICE_NAME] == my_service_name]
	if not len(matched_list) > 0:
		return
	return matched_list[0][config.keys.service_info.VIDEO_TYPE]

def __gen_cm_cut_info( m2v_filename, output_filename, workspace_path, logo_filepath, logo_param_filepath,
					 exec_path, avs2yuv_path, m2v_vfp_path, opts ):
	os.system( exec_path + " "
			+ "-video " + os.path.join( workspace_path, m2v_filename ) + " "
			+ "-lgd " + logo_filepath + " "
			+ "-avs2x " + avs2yuv_path + " "
			+ "-avsPlg " + m2v_vfp_path + " "
			+ "-prm " + logo_param_filepath + " "
			+ "-out " + os.path.join( workspace_path, output_filename) + " "
			+ opts)
	return

def main():
	# 引数の解析
	options = __parse_args( sys.argv )
	# workspaceの一覧取得
	workspace_list = workspace.get_workspace_list( options.target_directory )
	# logo情報の一覧取得
	logo_info_list = logo.get_logo_info_list( options.logo_directory)
	# service情報の一覧取得
	service_info_list = config.load_info( config.filenames.SERVICE_INFO_FILE, options.config_directory)
	# 外部ツールの情報を取得
	utility_info_list = config.load_info( config.filenames.UTILITY_INFO_FILE, options.config_directory)
	# logo_guilloの情報
	logo_guillo_info = utility_info_list["logo_guillo"]
	print(logo_info_list)
	# tsがsplitされているか確認
	workspace_list = [x for x in workspace_list
					if flag.check_flag_existence( flag.filenames.SPLIT_TS, x[workspace.keys.WORKSPACE_PATH] )]
	# すでにcmカットされているか確認
	workspace_list = [x for x in workspace_list
					if not flag.check_flag_existence( flag.filenames.CM_CUT, x[workspace.keys.WORKSPACE_PATH])]
	# cmカット時に出力するファイル名を追加
	[x.update( {keys.CM_INFO_FILENAME: x[workspace.keys.BASE_NAME] + consts.CM_INFO_EXT} ) for x
		in workspace_list]
	# serviceのvideotypeを追加
	[x.update( {config.keys.service_info.VIDEO_TYPE: __get_video_type(x[workspace.keys.SERVICE], service_info_list)})
		for x in workspace_list
		if not __get_video_type(x[workspace.keys.SERVICE], service_info_list ) == None ]
	[__gen_cm_cut_info( x[workspace.keys.BASE_NAME] + consts.M2V_EXT,
						x[workspace.keys.BASE_NAME] + consts.CM_INFO_EXT,
						x[workspace.keys.WORKSPACE_PATH],
						logo_info_list[(x[workspace.keys.SERVICE], x[config.keys.service_info.VIDEO_TYPE])][logo.keys.LOGO_FILEPATH],
						logo_info_list[(x[workspace.keys.SERVICE], x[config.keys.service_info.VIDEO_TYPE])][logo.keys.LOGO_PARAM_FILEPATH],
						logo_guillo_info["exec"],
						logo_guillo_info["avs2yuv_path"],
						logo_guillo_info["m2v_vfp_path"],
						logo_guillo_info["opts"])
		for x in workspace_list
		if not logo_info_list[(x[workspace.keys.SERVICE], x[config.keys.service_info.VIDEO_TYPE])] == None ]
	[flag.gen_flag_file(flag.filenames.CM_CUT, x[workspace.keys.WORKSPACE_PATH]) for x
		in workspace_list]




if __name__ == '__main__':
	main()