import subprocess
import os

from signal import SIGINT

# import ffmpeg
from pyrogram.raw.types import InputGroupCall
from pyrogram.raw.functions.phone import EditGroupCallTitle

from bot import alemiBot

class Session:
	def __init__(self):
		self.spotify_process = None
		self.ffmpeg_process = None
		self.group_call = None
		self.muted = False
		self.spoty_log = None
		self.ffmpeg_log = None
		self.chat_member = None

	async def set_title(self, title):
		call = InputGroupCall(
				id=self.group_call.group_call.id,
				access_hash=self.group_call.group_call.access_hash)
		raw_fun = EditGroupCallTitle(call=call, title=title)
		await self.group_call.client.send(raw_fun)

	def start(self, device_name="SpotyRobot", device_type="speaker", quiet=True):
		username = alemiBot.config.get("spotify", "username", fallback=None)
		password = alemiBot.config.get("spotify", "password", fallback=None)
		cwd = os.getcwd()
		try:
			os.mkfifo("plugins/spotyrobot/data/raw-fifo")
			os.mkfifo("plugins/spotyrobot/data/music-fifo")
		except FileExistsError:
			pass
		if quiet:
			self.spoty_log = open("plugins/spotyrobot/data/spoty.log", "w")
			self.ffmpeg_log = open("plugins/spotyrobot/data/ffmpeg.log", "w")
		self.spotify_process = subprocess.Popen(
			["./plugins/spotyrobot/data/librespot", "--name", device_name, "--device-type", device_type,
			 "--backend", "pipe", "--device", "plugins/spotyrobot/data/raw-fifo", "-u", username, "-p", password,
			 "--passthrough", "--onevent", f"{cwd}/plugins/spotyrobot/on_event.py" ],
			stderr=subprocess.STDOUT, stdout=self.spoty_log # if it's none it inherits stdout from parent
		)
		# # option "quiet" still sends output to pipe, need to send it to DEVNULL!
		# self.ffmpeg_process = ffmpeg.input("plugins/spotyrobot/data/raw-fifo").output(
		# 	"plugins/spotyrobot/data/music-fifo",
		# 	format='s16le',
		# 	acodec='pcm_s16le',
		# 	ac=2,
		# 	ar='48k'
		# ).overwrite_output().run_async(quiet=quiet)
		self.ffmpeg_process = subprocess.Popen(
			["ffmpeg", "-y", "-i", "plugins/spotyrobot/data/raw-fifo", "-f", "s16le", "-ac", "2",
			 "-ar", "48000", "-acodec", "pcm_s16le", "plugins/spotyrobot/data/music-fifo"],
			stderr=subprocess.STDOUT, stdout=self.ffmpeg_log,
		)

	def stop(self):
		try:
			self.spotify_process.send_signal(SIGINT)
			self.spotify_process.wait(timeout=5)
		except subprocess.TimeoutExpired:
			self.spotify_process.kill()
		if self.spoty_log is not None:
			self.spoty_log.close()
			self.spoty_log = None
		try:
			self.ffmpeg_process.send_signal(SIGINT)
			self.ffmpeg_process.wait(timeout=5)
		except subprocess.TimeoutExpired:
			self.ffmpeg_process.kill()
		if self.ffmpeg_log is not None:
			self.ffmpeg_log.close()
			self.ffmpeg_log = None
		self.chat_member = None

sess = Session()
