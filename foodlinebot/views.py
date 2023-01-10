from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from linebot.models import PostbackAction,URIAction, MessageAction, TemplateSendMessage, ButtonsTemplate, CarouselTemplate, CarouselColumn, MessageTemplateAction
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage
import requests
from urllib.parse import quote
 
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

def GetRequest(url, param):
    return requests.get(url = url, params = param).json()

def GetCity():
    URL = "https://ifoodie.tw/api/location/search"
    data = GetRequest(URL, {"q": ""})
    _columns = []
    _action = [MessageAction(label='Default(不選擇)', text='縣市 Default(不選擇)')]
    for i in data['response']:
        _action.append(
            MessageAction(
                label=i['city'],
                text='縣市 ' + i['city']
            )
        )
    _action.append(MessageAction(label=' ', text=' '))
    _action.append(MessageAction(label=' ', text=' '))
    for i in range(0,len(_action)//3):
        _columns.append(
            CarouselColumn(
                text='選擇縣市',
                actions=_action[i*3:i*3+3]
            )
        )
    carousel_template_message = TemplateSendMessage(
        alt_text='城市選單',
        template=CarouselTemplate(
            columns=_columns
        )
    )
    return carousel_template_message

def GetArea(city):
    URL = "https://ifoodie.tw/api/location/search"
    data = GetRequest(URL, {"q": city})
    _columns = []
    _action = [MessageAction(label='Default(不選擇)', text='縣市 ' + city + '\n區域 Default(不選擇)')]
    for i in data['response']:
        if (i['area'] != None and i['area'] != ""):
            _action.append(
                MessageAction(
                    label=i['area'],
                    text='縣市 ' + city + '\n區域 ' + i['area']
                )
            )
    for i in range(0, len(_action)%3):
        _action.append(MessageAction(label=' ', text=' '))
    for i in range(0,len(_action)//3):
        _columns.append(
            CarouselColumn(
                text='選擇區域',
                actions=_action[i*3:i*3+3]
            )
        )
    carousel_template_message = TemplateSendMessage(
        alt_text='區域選單',
        template=CarouselTemplate(
            columns=_columns
        )
    )
    return carousel_template_message

def GetCategory(city, area):
    URL = "https://ifoodie.tw/api/category/auto_complete"
    data = GetRequest(URL, {"q": ""})
    _columns = []
    _action = [MessageAction(label='Default(不選擇)', text='縣市 ' + city + '\n區域 ' + area +'\n分類 Default(不選擇)')]
    for i in data['response']:
        _action.append(
            MessageAction(
                label=i,
                text='縣市 ' + city + '\n區域 ' + area + '\n分類 ' + i
            )
        )
    for i in range(0, len(_action)%3):
        _action.append(MessageAction(label=' ', text=' '))
    for i in range(0, 10):
        _columns.append(
            CarouselColumn(
                text='選擇分類',
                actions=_action[i*3:i*3+3]
            )
        )
    carousel_template_message = TemplateSendMessage(
        alt_text='分類選單',
        template=CarouselTemplate(
            columns=_columns
        )
    )
    return carousel_template_message

def GetRusult(data):
    _columns = []
    URL_LINK = "https://ifoodie.tw/restaurant/"
    for i in data['response']:
        if('休息' not in i['opening_hours']):
            URL_LOCATEION = ("https://www.google.com.tw/maps/place/{}/").format(quote(i['address']))
            _columns.append(
                CarouselColumn(
                    thumbnail_image_url=i['cover_url'],
                    title=i['name'] + ' ',
                    text='rating:' + str(i['rating']) + '★\n'+ i['opening_hours'],
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
        alt_text='選單',
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
                # api-endpoint
                input = event.message.text.split('\n')
                if('縣市' not in input[0]):
                    line_bot_api.reply_message(  # 回復傳入的訊息文字
                        event.reply_token,
                        GetCity()
                        #TextSendMessage(text=event.message.text)
                    )
                elif(len(input)==1):
                    if(input[0][3:len(input[0])] == "Default(不選擇)"):
                        line_bot_api.reply_message(  # 回復傳入的訊息文字
                            event.reply_token,
                            GetCategory('Default(不選擇)', 'Default(不選擇)')
                            #TextSendMessage(text=event.message.text)
                        )
                    else:
                        line_bot_api.reply_message(  # 回復傳入的訊息文字
                            event.reply_token,
                            GetArea(input[0][3:len(input[0])])
                            #TextSendMessage(text=event.message.text)
                        )
                elif(len(input)==2):
                    line_bot_api.reply_message(  # 回復傳入的訊息文字
                        event.reply_token,
                        GetCategory(input[0][3:len(input[0])], input[1][3:len(input[1])])
                        #TextSendMessage(text=event.message.text)
                    )
                elif(len(input)==3):
                    city = "" if input[0][3:len(input[0])]=="Default(不選擇)" else input[0][3:len(input[0])]
                    area = "" if input[1][3:len(input[1])]=="Default(不選擇)" else input[1][3:len(input[1])]
                    category = "" if input[2][3:len(input[2])]=="Default(不選擇)" else input[2][3:len(input[2])]
                    payload = {'q': category, 'city_name': city, 'area_name': area, 'limit': '10', 'order_by': 'rating'}
                    URL = "https://ifoodie.tw/api/restaurant/explore/"
                    data = GetRequest(URL, payload)
                    if len(data['response']) == 0:
                        line_bot_api.reply_message(  # 回復傳入的訊息文字
                            event.reply_token,
                            TextSendMessage(text="無查尋條件之餐廳")
                        )
                    else:
                        line_bot_api.reply_message(  # 回復傳入的訊息文字
                            event.reply_token,
                            GetRusult(data)
                            #TextSendMessage(text=event.message.text)
                        )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()