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

class keys:
	# 自分で定義したサービス名
	MY_SERVICE_NAME = "my_service_name"
	# ビデオタイプ
	VIDEO_TYPE = "video_type"
	# logoファイルパス
	LOGO_FILEPATH = "logo_filepath"
	# logoのパラメータファイルパス
	LOGO_PARAM_FILEPATH = "logo_param_filepath"

class consts:
	# ロゴファイルの拡張子
	LOGO_EXT = ".lgd"
	# ロゴファイルのパラメータの拡張子
	LOGO_PARAM_EXT = ".lgd.autoTune.param"
	# logoファイル名の分割キャラクタ
	SPLIT_CHAR = "_"

def get_logo_info( my_service_name, video_type, logo_filepathlist ):
	matched_list = [x for x in logo_filepathlist
				if x[keys.MY_SERVICE_NAME] == my_service_name
					and x[keys.VIDEO_TYPE] == video_type ]
	if not len( matched_list ) > 0:
		return
	return matched_list[0]

def get_logo_info_list( logo_dirpath ):
	if not os.path.isdir( logo_dirpath ):
		sys.stderr.writelines( logo_dirpath + "は存在しません")
		return False
	logo_filelist = [x for x in os.listdir( logo_dirpath)
						if x.endswith( consts.LOGO_EXT) ]
	logo_basenamelist = [ os.path.splitext(x)[0] for x in logo_filelist ]
	logo_basename_tokenlist = [ x.partition( consts.SPLIT_CHAR ) for x in logo_basenamelist ]
	logo_filepathlist = {}
	[logo_filepathlist.update( {(x[0], x[2]): __get_logo_filepath( x[0], x[2], logo_dirpath )}) for x in logo_basename_tokenlist]
	return logo_filepathlist

def __get_logo_filepath( my_service_name, video_type, logo_dirpath):
	logo_basename = my_service_name + consts.SPLIT_CHAR + video_type
	logo_filename = logo_basename + consts.LOGO_EXT
	logo_param_filename =logo_basename + consts.LOGO_PARAM_EXT
	logo_filepath = os.path.join( logo_dirpath, logo_filename )
	logo_param_filepath = os.path.join( logo_dirpath, logo_param_filename )
	return {keys.LOGO_FILEPATH: logo_filepath, keys.LOGO_PARAM_FILEPATH: logo_param_filepath }

def main():
	if len(sys.argv) < 2:
		print( "Usage: ${exec} logo_dir" )
		sys.exit()
	if not os.path.isdir( sys.argv[1] ):
		print( sys.argv[1] + " はディレクトリではありません" )
		sys.exit()

	logo_filelist = get_logo_info_list( sys.argv[1] )
	print( logo_filelist )

if __name__ == "__main__":
	main()