# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        extractSubtitle
# Purpose:
#
# Author:      Haruhisa Ishida
#
# Created:     03/01/2013
# Copyright:   (c) Haruhisa Ishida 2013
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os
import sys
from optparse import OptionParser
# 自前のモジュール群
from resources import config
from resources import flag
from resources import workspace

TS_EXT = ".ts"
SPLIT_FLAG_FILENAME = "__splitted"

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

	# 解析実行
	(options, args) = parser.parse_args()

	# 必要なオプションの有無チェック
	if not options.target_directory:
		parser.error( "処理対象のルートディレクトリが指定されていません")
	if not options.config_directory:
		parser.error( "設定ファイルが格納されたディレクトリが指定されていません")

	# 指定されたオプションの有効性チェック
	if not (os.path.isdir( options.target_directory )):
		parser.error( options.target_directory, "は存在しません" )
	if not (os.path.isdir( options.config_directory )):
		parser.error( options.config_directory, "は存在しません" )
	return options

def __extract_subtitle( ts_filename, workspace_path, exec_path, format_opt ):
	os.system( exec_path + " "
			+ os.path.join( workspace_path, ts_filename) + " "
			+ format_opt )
	return

def main():
	options = __parse_args( sys.argv )
	# workspaceの一覧取得
	workspace_info = workspace.get_workspace_list( options.target_directory )
	workspace_info = [x for x in workspace_info
					if os.path.isfile(os.path.join( x[workspace.keys.WORKSPACE_PATH], SPLIT_FLAG_FILENAME))]
	workspace_info = [x for x in workspace_info
					if not flag.check_flag_existence(flag.filenames.SUBTITLE, x[workspace.keys.WORKSPACE_PATH])]
	utility_info = config.load_info(config.filenames.UTILITY_INFO_FILE, options.config_directory)
	tool_info = utility_info["caption_2_ass"]
	[__extract_subtitle( os.path.join( x[workspace.keys.BASE_NAME] + TS_EXT),
									x[workspace.keys.WORKSPACE_PATH],
									tool_info["exec"],
									tool_info["format_opt"])
					for x in workspace_info
					if x[workspace.keys.FLAGS][workspace.keys.VALID_SUB_TITLE] ]
	[flag.gen_flag_file(flag.filenames.SUBTITLE, x[workspace.keys.WORKSPACE_PATH])
		for x in workspace_info]

if __name__ == '__main__':
	main()