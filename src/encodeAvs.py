# -*- coding: utf8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      glycine
#
# Created:     01/02/2013
# Copyright:   (c) glycine 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

# 外部モジュール読込
import codecs
import math
import os
import os.path
import re
import shutil
import sys
import wave
from optparse import OptionParser
# 自前のモジュール群
from resources import config
from resources import workspace
from resources import x264

# エンコードのskipフラグファイル
ENC_SKIP_FILE = "__skip_encode"

# 拡張子など
AVS_EXT = ".avs"
LOG_EXT = ".log"
MP4_EXT = ".mp4"
AAC_EXT = ".aac"
WAV_EXT = ".wav"
MAIN_WAVE_EXT = "_main.wav"
SUB_WAVE_EXT = "_sub.wav"
TRIM_WAVE_EXT = ".trim.wav"
MAIN_TRIM_WAVE_EXT ="_main.trim.wav"
SUB_TRIM_WAVE_EXT = "_sub.trim.wav"
TRIM_AVS_EXT = ".trim.avs"

# 外部プログラムのパス
WAVI_PATH = "C:\\Utility\\WAVI\\wavi.exe"
NORMALIZE_PATH = "C:\\Utility\\Normalize\\normalize.exe"
NEROAACENC_PATH = "C:\\Utility\\NeroAacEnc\\neroAacEnc.exe"
MP4BOX_PATH = "C:\\Software\\MyMP4BoxGUI\\Tools\\MP4Box.exe"

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

	# 以下殻オプションの設定
	# 読込元のディレクトリ指定用のオプション
	parser.add_option( "-i", "--inputdir",
		dest = "input_directory",
		action = "store",
		type = "string",
		help = "読込元のディレクトリを指定します",
		metavar = "INPUT_DIRECTORY")

	# 出力先のディレクトリ指定用のオプション
	parser.add_option( "-o", "--outputdir",
		dest = "output_directory",
		action = "store",
		type = "string",
		help = "出力先のディレクトリを指定します",
		metavar = "OUTPUT_DIRECTORY")

	parser.add_option( "-c", "--configdir",
		dest = "config_directory",
		action = "store",
		type = "string",
		help = "設定ファイルが格納されたディレクトリを指定します",
		metavar = "CONFIG_DIRECTORY")

	# 解析実行
	(options, args) = parser.parse_args()

	# 必要なオプションの有無チェック
	if not options.input_directory:
		parser.error( "読込元のディレクトリが指定されていません" )
	if not options.output_directory:
		parser.error( "出力先のディレクトリが指定されていません")
	if not options.config_directory:
		parser.error( "設定ファイルが格納されたディレクトリが指定されていません")

	# 指定されたオプションが有効かのチェック
	if not ( os.path.exists( options.input_directory)
				and os.path.isdir( options.input_directory) ):
		parser.error( options.input_directory,"は存在しません" )
	if not ( os.path.exists( options.config_directory)
				and os.path.isdir( options.config_directory) ):
		parser.error( options.config_directory, "は存在しません" )
	return options

def gen_enc_skip_flag_file( workspace_path ):
	flag_filepath = os.path.join( workspace_path, ENC_SKIP_FILE )
	flag_file = open( flag_filepath, "w" )
	flag_file.write( "" )
	flag_file.close()
	return

def get_enc_info( workspace_path ):
	# skipフラグファイルがあればskipする
	enc_skip_filepath = os.path.join( workspace_path, ENC_SKIP_FILE )
	if os.path.exists( enc_skip_filepath ) and os.path.isfile( enc_skip_filepath ):
		return False

	enc_info = config.load_info( workspace.filenames.ENC_INFO_FILE, workspace_path )
	return enc_info

def get_wav_length( wav_filepath ):
	wav_obj = wave.open( wav_filepath )
	wav_length = math.ceil( wav_obj.getnframes() / wav_obj.getframerate() )
	wav_obj.close()
	return wav_length

def get_video_bitrate( encode_size, audio_length, audio_bitrate ):
	total_bit = encode_size * 1024 * 8
	bitrate = math.ceil( total_bit / audio_length )
	video_bitrate = bitrate - audio_bitrate
	return video_bitrate

def get_output_filepath( avs_filepath, base_title, output_root_dir ):
	avs_filename = os.path.basename( avs_filepath )
	base, ext= os.path.splitext( avs_filename )
	output_dir = os.path.join( output_root_dir, base_title )
	output_filepath = os.path.join( output_dir, (base + MP4_EXT))
	return {"output_filepath": output_filepath,
				"output_dir": output_dir}

def get_avs_info( workspace_path, workspace_name):
	avs_filelist = [os.path.join( workspace_path, x)
						for x in os.listdir( workspace_path )
						if x.endswith( AVS_EXT )]
	if len(avs_filelist) < 1:
		return False
	avs_filepath = avs_filelist[0]
	base, ext= os.path.splitext( avs_filepath )
	log_filepath = base + LOG_EXT
	mp4_filepath = base + MP4_EXT
	trim_wave_filepath = base + TRIM_WAVE_EXT
	aac_filepath = base+AAC_EXT
	return {"avs_filepath": avs_filepath,
				"log_filepath": log_filepath,
				"mp4_filepath": mp4_filepath,
				"trim_wav_filepath": trim_wave_filepath,
				"aac_filepath": aac_filepath}

def get_main_and_sub_wav_info( workspace_path, workspace_name ):
	main_wav_filelist = [os.path.join( workspace_path, x)
								for x in os.listdir( workspace_path)
								if x.endswith( MAIN_WAVE_EXT )]
	sub_wav_filelist = [os.path.join( workspace_path, x)
								for x in os.listdir( workspace_path)
								if x.endswith( SUB_WAVE_EXT)]
	# 主音声ないしは副音声のどちらかが無ければ無効とする
	if len( main_wav_filelist)< 1 or len( sub_wav_filelist)< 1:
		return {"main_wav_filepath": False,
					"sub_wav_filepath": False}

	wav_filelist = [os.path.join( workspace_path, x)
						for x in os.listdir( workspace_path)
						if x.endswith( WAV_EXT)
							and not x.endswith( MAIN_WAVE_EXT)
							and not x.endswith( SUB_WAVE_EXT)
							and not x.endswith( TRIM_WAVE_EXT)]
	# 置換元となる元のwavファイル名が取得できなければ無効とする
	if len( wav_filelist) < 1:
		return {"main_wav_filepath": False,
					"sub_wav_filepath": False}

	main_wav_filepath = main_wav_filelist[0]
	base, ext = os.path.splitext( main_wav_filepath )
	trim_main_wav_filepath = base + MAIN_TRIM_WAVE_EXT
	main_aac_filepath = base + AAC_EXT
	sub_wav_filepath = sub_wav_filelist[0]
	base2, ext2 = os.path.splitext( sub_wav_filepath )
	trim_sub_wav_filepath = base2 + SUB_TRIM_WAVE_EXT
	sub_aac_filepath = base2 + AAC_EXT


	return { "wav_filepath": wav_filelist[0],
				"main_wav_filepath": main_wav_filepath,
				"trim_main_wav_filepath": trim_main_wav_filepath,
				"main_aac_filepath": main_aac_filepath,
				"sub_wav_filepath": sub_wav_filepath,
				"trim_sub_wav_filepath": trim_sub_wav_filepath,
				"sub_aac_filepath": sub_aac_filepath}

def wavi( output_filepath, input_filepath ):
	command = WAVI_PATH
	command += " " + input_filepath
	command += " " + output_filepath
	os.system( command )
	return

def wavi_with_replacing_wav(output_filepath, avs_filepath, replace_wav_filepath, original_wav_filepath):
	replace_wav_filename = os.path.basename( replace_wav_filepath )
	original_wav_filename = os.path.basename( original_wav_filepath )
	print("replace " + original_wav_filename + " to " +  replace_wav_filename )
	base, ext= os.path.splitext( avs_filepath )
	temp_avs_filepath = base + TRIM_AVS_EXT

	# wavのファイル名を置換したavsファイルを作成する
	avs_file = codecs.open( avs_filepath, "r", "shift-jis")
	avs = avs_file.read()
	avs_file.close()
	temp_avs = re.sub( original_wav_filename, replace_wav_filename, avs )
	temp_avs_file = codecs.open( temp_avs_filepath, "w", "shift-jis")
	temp_avs_file.write( temp_avs )
	temp_avs_file.close()

	# 作成したavsを元にwaviを行う
	wavi( output_filepath, temp_avs_filepath )

	# 作成したavsファイルを削除する
	os.remove( temp_avs_filepath )
	return

def normalize_wav( wav_filepath ):
	command = NORMALIZE_PATH
	command += " " + wav_filepath
	os.system( command )
	return

def nero_aac_enc( aac_filepath, wav_filepath, bitrate ):
	command = NEROAACENC_PATH
	command += " -2pass"
	command += " -lc"
	command += " -br " + str( bitrate * 1024 )
	command += " -if " + wav_filepath
	command += " -of " + aac_filepath
	os.system( command )
	return

def mux_mp4_and_aac( output_filepath, mp4_filepath, aac_filepath ):
	command = MP4BOX_PATH
	command += " -new " + output_filepath
	command += " -lang jpn "
	command += " -cprt " + "\"Glycine Bleumer\""
	# 動画の追加
	command += " -add " + mp4_filepath
	command += "#video:name=Video:lang=jpn "
	# 音声の追加
	command += " -add " + aac_filepath
	command += "#audio:name=Audio:lang=jpn "
	os.system( command )
	return

def mux_mp4_and_multi_aac( output_filepath, mp4_filepath, main_aac_filepath, sub_aac_filepath ):
	command = MP4BOX_PATH
	command += " -new " + output_filepath
	command += " -lang jpn "
	command += " -cprt " + "\"Glycine Bleumer\""
	# 動画の追加
	command += " -add " + mp4_filepath
	command += "#video:name=Video:lang=jpn "
	# 音声の追加
	command += " -add " + main_aac_filepath + "#audio:name=MainAudio:lang=jpn"
	command += " -add " + sub_aac_filepath + "#audio:name=SubAudio:lang=en"
	os.system( command )
	return

def encode_avs( workspace_info_elem, x264_info ):
	info = workspace_info_elem
   # AVSファイルからwaveファイルを作成
	wavi( info["trim_wav_filepath"],
		info["avs_filepath"])
	if info["main_wav_filepath"]:
		wavi_with_replacing_wav( info["trim_main_wav_filepath"],
			info["avs_filepath"],
			info["main_wav_filepath"],
			info["wav_filepath"])
	if info["sub_wav_filepath"]:
		wavi_with_replacing_wav( info["trim_sub_wav_filepath"],
			info["avs_filepath"],
			info["sub_wav_filepath"],
			info["wav_filepath"])

	# wavファイルから長さを取得
	info.update( {"wav_length": get_wav_length( info["trim_wav_filepath"])})
	# video_bitrateを取得
	if info["encode_size"] > 0:
		info.update( {"video_bitrate": get_video_bitrate( info["encode_size"], info["wav_length"], info["audio_bitrate"])})

	# trimしたwavファイルをnormalize
	normalize_wav( info["trim_wav_filepath"])
	if info["main_wav_filepath"]:
		normalize_wav( info["trim_main_wav_filepath"])
	if info["sub_wav_filepath"]:
		normalize_wav( info["trim_sub_wav_filepath"])

	# wavをaacにエンコード
	nero_aac_enc( info["aac_filepath"], info["trim_wav_filepath"], info["audio_bitrate"])
	if info["main_wav_filepath"]:
		nero_aac_enc( info["main_aac_filepath"], info["trim_main_wav_filepath"], info["audio_bitrate"])
	if info["sub_wav_filepath"]:
		nero_aac_enc( info["sub_aac_filepath"], info["trim_sub_wav_filepath"], info["audio_bitrate"])

	# avsをmp4にエンコード
	x264.encode( info["mp4_filepath"], info["log_filepath"], info["avs_filepath"], info["video_bitrate"],
		1, info["sar"], info["is_progressive"], x264_info )
	x264.encode( info["mp4_filepath"], info["log_filepath"], info["avs_filepath"], info["video_bitrate"],
		2, info["sar"], info["is_progressive"], x264_info )

	# 最終的な出力先ディレクトリが無ければ作成
	if not (os.path.exists( info["output_dir"]) and os.path.isdir( info["output_dir"])):
		os.makedirs( info["output_dir"])

	if not info["main_wav_filepath"]:
		mux_mp4_and_aac( info["output_filepath"], info["mp4_filepath"], info["aac_filepath"])
	else:
		mux_mp4_and_multi_aac( info["output_filepath"], info["mp4_filepath"],
			info["main_aac_filepath"], info["sub_aac_filepath"])

	# エンコード後にフラグファイルを作成する
	gen_enc_skip_flag_file( info["workspace_path"])

	return

def main():
	options = __parse_args( sys.argv )
	x264_info = config.load_info( x264.X264_CONFIG_FILENAME, options.config_directory )

	while True:
		workspace_info = workspace.get_workspace_list( options.input_directory )
		# エンコード対象をフィルタ
		workspace_info =[x for x in workspace_info
			if get_enc_info( x[workspace.keys.WORKSPACE_PATH] )]
		# この時点でworkspace_infoのサイズが0であれば終了する
		if len( workspace_info ) < 1:
			sys.exit()

		# エンコード時の設定情報を読み込み
		[x.update( get_enc_info( x[workspace.keys.WORKSPACE_PATH]))
			for x in workspace_info
			if get_enc_info( x[workspace.keys.WORKSPACE_PATH])]

		# エンコード時の各種生成ファイルのパス情報追加
		[x.update( get_avs_info( x[workspace.keys.WORKSPACE_PATH], x[workspace.keys.WORKSPACE]))
			for x in workspace_info
			if get_avs_info( x[workspace.keys.WORKSPACE_PATH], x[workspace.keys.WORKSPACE])]
		# 主音声および副音声の情報を追加
		[x.update( get_main_and_sub_wav_info( x[workspace.keys.WORKSPACE_PATH], x[workspace.keys.WORKSPACE]))
			for x in workspace_info]
		# 最終的な出力先の情報を追加
		[x.update( get_output_filepath( x["avs_filepath"], x["base_title"], options.output_directory))
			for x in workspace_info]

		# 一連のエンコード
		[encode_avs(x, x264_info)
			for x in workspace_info]

if __name__ == '__main__':
    main()
