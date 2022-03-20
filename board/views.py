from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import json
from .models import User, Message
from django.core.exceptions import ValidationError

# Create your views here.
def message(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)

    if request.method == 'GET':
        limit = request.GET.get('limit', default='100')
        offset = request.GET.get('offset', default='0')
        if not limit.isdigit():
            return gen_response(400, '{} is not a number'.format(limit))
        if not offset.isdigit():
            return gen_response(400, '{} is not a number'.format(offset))

        return gen_response(200, [
                {
                    'title': msg.title,
                    'content': msg.content,
                    'user': msg.user.name,
                    'timestamp': int(msg.pub_date.timestamp())
                }
                for msg in Message.objects.all().order_by('-pub_date')[int(offset) : int(offset) + int(limit)]
            ])

    elif request.method == 'POST':
        # 从cookie中获得user的名字，如果user不存在则新建一个
        # 如果cookie中没有user则使用"Unknown"作为默认用户名
        name = request.COOKIES['user'] if 'user' in request.COOKIES else 'Unknown'
        if name == 'Unknown':
            name = request.COOKIES['name'] if 'name' in request.COOKIES else 'Unknown'
        print(request.COOKIES)
        user = User.objects.filter(name=name).first()
        if not user:
            user = User(name = name)
            try:
                user.full_clean()
                user.save()
            except ValidationError as e:
                return gen_response(400, "Validation Error of user: {}".format(e))
        data_str = request.body
        # 验证请求的数据格式是否符合json规范，如果不符合则返回code 400
        # -------------------------------------------------------------------------------
        try:
            j = json.loads(data_str)
            title = j["title"]
            content = j["content"]
        except:
            return gen_response(400, "Invalid Json str.")

        # 验证请求数据是否满足接口要求，若通过所有的验证，则将新的消息添加到数据库中
        
        if not title:
            return gen_response(400, "No title.")
        if not content:
            return gen_response(400, "No content.")
        if len(title) > 100:
            return gen_response(400, "Title length should be no more than 100. Your lenth is {}.".format(len(title)))
        if len(content) > 500:
            return gen_response(400, "Content length should be no more than 500. Your lenth is {}.".format(len(content)))
        message = Message(user = user, title = title, content = content)
        message.save()
        # PS: {"title": "something", "content": "someting"} title和content均有最大长度限制
        # -------------------------------------------------------------------------------
        # 添加成功返回code 201
        return gen_response(201, "message was sent successfully")

    else:
        return gen_response(405, 'method {} not allowd'.format(request.method))

# 一键清空留言板接口 DONE
def clearmessage(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)
        
    Message.objects.all().delete()
    return gen_response(200, 'Delete all messages.')

# 返回某个用户的所有留言 TODO
def messages_for_user(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)
    
    data_str = request.body
    try:
        j = json.loads(data_str)
        user = j["user"]
    except:
        return gen_response(400, "Invalid Json str.")
    find_user = User.objects.filter(name = user).first()
    if not user:
        return gen_response(400, "No such user.")
    find_message = Message.objects.filter(user = find_user).order_by('-pub_date')
    ret = []
    for msg in find_message:
        ret.append(
            {
                'title':msg.title,
                'content': msg.content,
                'timestamp': int(msg.pub_date.timestamp())
            })
    return JsonResponse({
        'code': 200,
        'data': ret
    }, status = 200) 
    
# AVATAR 用户头像 TODO
def avatar(request):
    def gen_response(code: int, data: str):
        return JsonResponse({
            'code': code,
            'data': data
        }, status=code)
        
    if request.method == 'GET':
        if 'user' in request.GET:
            user = request.GET.get('user')
            find_user = User.objects.filter(name = user).first()
            if not find_user:
                return gen_response(300, "No such user.")
            if not find_user.avatar:
                return gen_response(302, 'No photo.')
            # 找到头像
            return HttpResponse(status = 400, content_type='image/png', content = find_user.avatar)
        else:
            return gen_response(301, 'Wrong form.')

    elif request.method == 'POST':
        # 提示
        try:
           user = request.POST['user'] 
           pic = request.FILES['pic']
        except:
            gen_response(301, "Wrong form.")
        if not user:
            return gen_response(301, 'Wrong form.')
        if not pic:
            return gen_response(301, 'Wrong form.')
        find_user = User.objects.filter(name = user).first()
        if not find_user:
            return gen_response(300, "No such user.")
        find_user.avatar = pic
        find_user.save()
        return gen_response(200, "Uploaded.")
        
    else:
        return HttpResponse('method {} not allowd'.format(request.method), status=405)
