import os
import subprocess

def convert_aac_to_mp3_in_folder(input_folder_name="downloads"):
    """
    将指定文件夹内所有 .aac 文件转换为 .mp3 格式。

    Args:
        input_folder_name (str): 包含 AAC 文件的子文件夹名称。
    """
    current_dir = os.getcwd() # 获取当前脚本所在的目录
    full_input_dir = os.path.join(current_dir, input_folder_name)

    print(f"--- AAC to MP3 转换工具 ---")
    print(f"搜索 AAC 文件的目录: '{full_input_dir}'")

    # 1. 检查 FFmpeg 是否可用
    try:
        # 显式指定 encoding='utf-8' 来处理 FFmpeg 的输出
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, text=True, encoding='utf-8')
        print("FFmpeg 检查成功，已安装并可访问。")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n错误：FFmpeg 未安装或不在您的系统 PATH 中。")
        print("请访问 FFmpeg 官网安装 FFmpeg，并确保它在命令行中是可用的。")
        return

    # 2. 检查输入文件夹是否存在
    if not os.path.exists(full_input_dir):
        print(f"\n错误：文件夹 '{full_input_dir}' 不存在。")
        print("请确保在当前脚本目录下有名为 'downloads' 的子文件夹，并且里面有 AAC 文件。")
        return

    aac_files = []
    for filename in os.listdir(full_input_dir):
        if filename.lower().endswith(".aac"):
            aac_files.append(filename)

    if not aac_files:
        print(f"\n在 '{full_input_dir}' 目录中没有找到 .aac 文件。")
        return

    print(f"\n找到 {len(aac_files)} 个 AAC 文件，开始转换...")

    for aac_filename in aac_files:
        input_filepath = os.path.join(full_input_dir, aac_filename)
        # 获取不带扩展名的文件名
        name_without_ext = os.path.splitext(aac_filename)[0]
        output_filepath = os.path.join(full_input_dir, f"{name_without_ext}.mp3")

        # FFmpeg 转换命令
        command = [
            "ffmpeg",
            "-i", input_filepath,
            "-c:a", "libmp3lame",
            "-qscale:a", "2",
            output_filepath
        ]

        print(f"\n正在转换：'{aac_filename}' 为 '{os.path.basename(output_filepath)}'...")
        try:
            # 执行 FFmpeg 命令
            # 关键修改：添加 encoding='utf-8' 参数
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"√ 成功转换 '{aac_filename}'。")
            # 如果需要查看 FFmpeg 的详细输出，可以取消以下行的注释
            # print("FFmpeg 标准输出 (stdout):\n", result.stdout)
            # print("FFmpeg 错误输出 (stderr):\n", result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"× 转换 '{aac_filename}' 失败！")
            print(f"命令执行失败，返回码：{e.returncode}")
            print(f"FFmpeg 错误信息 (stderr):\n{e.stderr}")
        except FileNotFoundError:
            print("× 错误：'ffmpeg' 命令未找到。请确保 FFmpeg 已安装并添加到系统 PATH 中。")
            break

    print("\n--- 所有 AAC 文件转换任务完成。---")

if __name__ == "__main__":
    convert_aac_to_mp3_in_folder()
