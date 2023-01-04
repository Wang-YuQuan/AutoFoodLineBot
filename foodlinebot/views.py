from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from linebot.models import PostbackAction,URIAction, MessageAction, TemplateSendMessage, ButtonsTemplate, CarouselTemplate, CarouselColumn
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage
import requests
from urllib.parse import quote
 
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

def CTM(data):
    _columns = []
    URL_LINK = "https://ifoodie.tw/restaurant/"
    for i in data['response']:
        if('休息' not in i['opening_hours']):
            URL_LOCATEION = ("https://www.google.com.tw/maps/place/{}/").format(quote(i['address']))
            _columns.append(
                CarouselColumn(
                    thumbnail_image_url=i['cover_url'],
                    title=i['name'] + ' ' + '\n' + 'rating:' + str(i['rating']) + '★',
                    text=i['opening_hours'],
                    actions=[
                        # MessageAction(
                        #     label='message1',
                        #     text='message text1'
                        # ),
                        URIAction(
                            label='愛食記官方連結',
                            uri=(URL_LINK+i['id']+'-'+quote(i['name'])).replace(' ', '-')
                        ),
                        URIAction(
                            label='GOOGLE地址',
                            uri=URL_LOCATEION
                        ),
                    ]
                )
            )
    carousel_template_message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=_columns
        )
    )
    return carousel_template_message
 
@csrf_exempt
def callback(request):
 
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
 
        try:
            events = parser.parse(body, signature)  # 傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        for event in events:
            if isinstance(event, MessageEvent):  # 如果有訊息事件
                reply = ""
                # api-endpoint
                input = event.message.text.split(' ')
                city = "台中市"
                area = "沙鹿區"
                category = "火鍋"
                payload = {'q': category, 'city_name': city, 'area_name': area, 'limit': '10', 'order_by': 'recent'}
                URL = "https://ifoodie.tw/api/restaurant/explore/"

                # sending get request and saving the response as response object
                r = requests.get(url = URL, params = payload)
                # extracting data in json format
                data = r.json()
                line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    CTM(data)
                    #TextSendMessage(text=reply)
                    #TextSendMessage(text=event.message.text)
                )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()