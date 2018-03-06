import logging
import requests

from flask import Flask, request, abort
from logging.handlers import RotatingFileHandler
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import *

app = Flask(__name__)

# botPush
channel_secret = "c57d24d63aec93a386f418ae958c2911"
channel_access_token = "YPDNya/4JsJUP5xoBvDTGaxuu6ud8X01SaDtkh57TtrgrfOV8/2/36Dp3J/v+NHAKfD91IYgRNp6iKxWuv4aLOOm/c3LfujJxf+uLG16fhQDe1c8DNwa4H7GUeyVoaWVh/uKEFs3xUHKJidDAHSUIwdB04t89/1O/w1cDnyilFU="

base_API_url = 'http://127.0.0.1/backend-bot'
# base_API_url = "https://backend-bot.000webhostapp.com"

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

def unhandledMessage(event):
	app.logger.warning("Unhandled TextMessage!!!")
	app.logger.debug("Raw message: {}".format(event.message))

	app.logger.info("sending help reply message")
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(
			text="coba deh ketik :help kak :D"
		)
	)

def sendErrorMessage(reply_token):
	app.logger.info("sending error message to user")
	line_bot_api.reply_message(
		reply_token,
		[
			StickerSendMessage(
				package_id='1',
				sticker_id='135'
			),
			TextSendMessage(
				text="Terjadi kesalahan pada server, maafin aku kak :("
			)
		]
	)

@app.route("/callback", methods=['POST'])
def callback():
	app.logger.info("Handling New Request!!!")
	signature = request.headers['X-Line-Signature']

	data = request.get_data(as_text=True)
	app.logger.debug("Raw Request Data: " + data)

	# handle webhook body
	try:
		handler.handle(data, signature)
	except InvalidSignatureError as e:
		app.logger.error("Error Occurred : {}".format(e))
	except LineBotApiError as l:
		app.logger.error("Error Occurred : {}".format(l))
	finally:
		app.logger.info("Finished!!!")

	return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
	app.logger.info("Handling MessageEvent")
	app.logger.debug("Raw MessageEvent Data: {}".format(event))

	try:
		if ':find ' in event.message.text:
			app.logger.info("User want to find comic!!!")
			string = event.message.text.split(' ')
			keyword = ''
			for s in range(0, len(string)):
				if s>0:
					if keyword:
						keyword = keyword+" "+string[s]
					else:
						keyword = string[s]

			response = requests.get(base_API_url+"/index.php/comic/find/"+keyword)
			app.logger.info("response from backend {}".format(response))

			obj = response.json()

			if len(obj) < 1:
				line_bot_api.reply_message(
					event.reply_token,
					TextSendMessage(
						text="wah aku gk nemu komik apapun nih ka :("
					)
				)

			else:
				msg = ''
				comicList = []

				for comic in obj:
					msg = msg + "\n" + comic
					comicList.append(MessageTemplateAction(label=comic[:20], text=":read "+comic))

				msg = 'ini daftar komiknya kaka :D :' + msg

				buttons_template = ButtonsTemplate(title='ini daftar komiknya kaka :D',text='klik aja buat baca chapter terbarunya kak :D!', actions=comicList)
				template_message = TemplateSendMessage(alt_text=msg, template=buttons_template)

				app.logger.info("sending comic list to {}".format(event.source.user_id))
				line_bot_api.reply_message(event.reply_token, template_message)

		elif ':read ' in event.message.text:
			string = event.message.text.split(' ')
			episode = ''
			comic = ''
			for s in range(0,len(string)):
				if string[s].isdigit() and not episode:
					episode = string[s]
				elif s>0:
					if comic:
						comic = comic+" "+string[s]
					else:
						comic = string[s]

			if episode:
				app.logger.info("user want to read comic with spesific episode!!!")
				app.logger.info("accessing backend")
				response = requests.get(base_API_url+"/index.php/comic/read/"+event.source.user_id+"/"+comic+"/"+episode)
			else:
				app.logger.info("user want to read comic with latest episode!!!")
				app.logger.info("accessing backend")
				response = requests.get(base_API_url+"/index.php/comic/read/"+event.source.user_id+"/"+comic)

			app.logger.debug("data from backend: " + response.text)
			obj = response.json()

			responseList=[]
			response_message=[]

			if 'episode' in obj:
				app.logger.info("processing backend data")
				response_message.append(TextSendMessage(
					text=obj['episode']['name']
				))

				pages = obj['episode']['page'];
				for page in pages:
					response_message.append(ImageSendMessage(original_content_url=page, preview_image_url=page))
					if len(response_message) == 5:
						responseList.append(response_message)
						response_message = []
					elif pages.index(page) == len(pages)-1 :
						responseList.append(response_message)

				app.logger.info("sending processed comic to "+ event.source.user_id)
				line_bot_api.reply_message(
					event.reply_token,
					responseList[0]
				)
				for r in responseList[1:]:
					line_bot_api.push_message(
						event.source.user_id,
						r
					)

			else:
				if 'name' not in obj:
					response_message.append(TextSendMessage(
						text='aku gk nemu komiknya kak :(, kayanya belum rilis deh hehehe :D'
					))
				else:
					response_message.append(TextSendMessage(
						text='aku gk nemu episodenya kak :(, kayanya belum rilis deh hehehe :D'
					))

				line_bot_api.reply_message(
					event.reply_token,
					response_message
				)
		elif ':help' in event.message.text:
			pass

		elif ':unfavorite ' in event.message.text:
			app.logger.info("user want to unfavorite a comic")
			stringParse = event.message.text.split(':unfavorite ')

			print(base_API_url+"/index.php/unfavorite/"+event.source.user_id+"/"+stringParse[1])
			response = requests.get(base_API_url+"/index.php/unfavorite/"+event.source.user_id+"/"+stringParse[1])

			print (response.text)

			if 'OK' in response.text:
				line_bot_api.reply_message(event.reply_token, TextSendMessage(text="kakak udah gk berlangganan komiknya lagi :("))
			else:
				line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ada error kak :("))

		elif ':favorite' in event.message.text:

			if ' ' not in event.message.text:
				app.logger.info("user want to see favorited comic!!!")
				response = requests.get(base_API_url+"/index.php/favorite/"+event.source.user_id)
				
				parentList = response.json()

				if len(parentList)<1:
					line_bot_api.reply_message(event.reply_token, TextSendMessage(text="kakak belum ngasih tau apa aja komik kesukaan kaka :(, kalo kak suka komik one piece, coba deh ketik :favorite one piece"))

				msg = ''
				comicList = []

				a=0
				for comic in parentList:
					a=a+1
					msg = msg + "\n" + comic['name']
					comicList.append(MessageTemplateAction(label=comic['name'][:20], text=":read "+comic['name']))
					if a==4:
						msg = 'ini daftar komik favorite kaka :D :' + msg
						buttons_template = ButtonsTemplate(title='ini daftar komik favorite kaka :D',text='klik aja buat baca chapter terbarunya kak :D!', actions=comicList)
						template_message = TemplateSendMessage(alt_text=msg, template=buttons_template)

						print(comicList)
						line_bot_api.push_message(event.source.user_id, template_message)
						msg=''
						comicList=[]
						a=0

				if len(comicList)>0:
					msg = 'ini daftar komik favorite kaka :D :' + msg
					buttons_template = ButtonsTemplate(title='ini daftar komik favorite kaka :D',text='klik aja buat baca chapter terbarunya kak :D!', actions=comicList)
					template_message = TemplateSendMessage(alt_text=msg, template=buttons_template)

					print(comicList)
					line_bot_api.push_message(event.source.user_id, template_message)

			else:
				app.logger.info("user want to add a comic to favorite list!!!")
				stringParse = event.message.text.split(':favorite ')

				comic={}
				comic['name']=stringParse[1]

				comicObj={}
				comicObj['comic']=comic

				app.logger.info("accessing backend")
				response = requests.post(base_API_url+"/index.php/favorite/"+event.source.user_id, json=comicObj)

				if "FAIL" in response.text:
					textMessage="waduh aku gk nemu komiknya ka, coba deh pake fungsi :find dulu"
				elif "OK" in response.text:
					textMessage="udah aku catet ya kak, nanti aku kasih tau deh kalo ada chapter terbarunya :D"
				elif "EXISTS" in response.text:
					textMessage="sekali aja cukup ko kak, udah aku catet ko, coba cek :favorite"
				else:
					textMessage="waduh ada error ka :("

				line_bot_api.reply_message(
					event.reply_token,
					TextSendMessage(text=textMessage)
				)

		elif event.reply_token == '00000000000000000000000000000000':
			app.logger.info("ignored verify message!!!")
		else:
			unhandledMessage(event)
	except Exception as e:
		app.logger.warning("error detected")
		sendErrorMessage(event.reply_token)

if __name__ == "__main__":
	logFileHandler = RotatingFileHandler("log.txt", maxBytes=10000, backupCount=1)
	logFleFormatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
	logFileHandler.setFormatter(logFleFormatter)

	app.logger.setLevel(logging.DEBUG)
	app.logger.addHandler(logFileHandler)

	app.run(debug=True)