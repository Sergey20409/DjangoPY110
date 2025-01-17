from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from .models import DATABASE
from logic.services import filtering_category
from django.shortcuts import redirect
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required

def products_view(request):
    if request.method == "GET":
        id = request.GET.get('id')
        if id:
            for i, values in DATABASE.items():
                if int(id) == values ['id']:
                    return JsonResponse(DATABASE[i], json_dumps_params={'ensure_ascii': False,
                                                                 'indent': 4})
            return HttpResponseNotFound("Данного продукта нет в базе данных")
        category_key = request.GET.get('category')
        data = None
        if ordering_key := request.GET.get("ordering"):  # Если в параметрах есть 'ordering'
            if request.GET.get("reverse") and request.GET.get('reverse').lower()  == 'true':
                data = filtering_category(DATABASE, category_key, ordering_key, reverse=True)
            else:
                data = filtering_category(DATABASE, category_key, ordering_key, reverse=False)
        else:
            data = filtering_category(DATABASE, category_key)
        if data:
            return JsonResponse(data, json_dumps_params={'ensure_ascii': False,
                                                                 'indent': 4}, safe=False)
        return JsonResponse(data, json_dumps_params={'ensure_ascii': False,
                                                     'indent': 4})

# Create your views here.
from django.http import HttpResponse

def shop_view(request):
    if request.method == "GET":
        return render(request,
                      'store/shop.html',
                      context={"products": DATABASE.values()})

def products_page_view(request, page):
    if request.method == "GET":
        for data in DATABASE.values():
            if data['html'] == page:  # Если значение переданного параметра совпадает именем html файла
                with open(f'store/products/{page}.html', encoding="utf-8") as f:
                    data = f.read()
                return HttpResponse(data)
        # TODO 1. Откройте файл open(f'store/products/{page}.html', encoding="utf-8") (Не забываем про контекстный менеджер with)
        # TODO 2. Прочитайте его содержимое
        # TODO 3. Верните HttpResponse c содержимым html файла

        # Если за всё время поиска не было совпадений, то значит по данному имени нет соответствующей
        # страницы товара и можно вернуть ответ с ошибкой HttpResponse(status=404)
        return HttpResponse(status=404)

def products_page_view(request, page):
    if request.method == "GET":
        if isinstance(page, str):
           # TODO Вставьте сюда тот код, что был ранее для обработки типа slug в products_page_view
           with open(f'store/products/{page}.html', encoding="utf-8") as f:
               data = f.read()
           return HttpResponse(data)

        elif isinstance(page, int):
            data = DATABASE.get(str(page))  # Получаем какой странице соответствует данный id
            if data:  # Если по данному page было найдено значение
                with open(f'store/products/{data["html"]}.html', encoding="utf-8") as f:
                    data = f.read()
                return HttpResponse(data)
                # TODO 1. Откройте файл open(f'store/products/{data["html"]}.html', encoding="utf-8") (Не забываем про контекстный менеджер with)
                # TODO 2. Прочитайте его содержимое
                # TODO 3. Верните HttpResponse c содержимым html файла

        return HttpResponse(status=404)

from logic.services import view_in_cart, add_to_cart, remove_from_cart


@login_required(login_url='login:login_view')
def cart_view(request):
    if request.method == "GET":
        current_user = get_user(request).username
        data = view_in_cart(request)[current_user]
        if request.GET.get('format') == 'JSON':
            return JsonResponse(data, json_dumps_params={'ensure_ascii': False,
                                                         'indent': 4})
        products = []  # Список продуктов
        for product_id, quantity in data['products'].items():
            product = DATABASE[product_id]
            product['quantity'] = quantity
            product["price_total"] = f"{quantity * product['price_after']:.2f}"
            products.append(product)
        return render(request, "store/cart.html", context={"products": products})

@login_required(login_url='login:login_view')
def cart_add_view(request, id_product):
    if request.method == "GET":
        result = add_to_cart(request, id_product) # TODO Вызвать ответственную за это действие функцию и передать необходимые параметры
        if result:
            return JsonResponse({"answer": "Продукт успешно добавлен в корзину"},
                                json_dumps_params={'ensure_ascii': False})

        return JsonResponse({"answer": "Неудачное добавление в корзину"},
                            status=404,
                            json_dumps_params={'ensure_ascii': False})


def cart_del_view(request, id_product):
    if request.method == "GET":
        result = remove_from_cart(request, id_product) # TODO Вызвать ответственную за это действие функцию и передать необходимые параметры
        if result:
            return JsonResponse({"answer": "Продукт успешно удалён из корзины"},
                                json_dumps_params={'ensure_ascii': False})

        return JsonResponse({"answer": "Неудачное удаление из корзины"},
                            status=404,
                            json_dumps_params={'ensure_ascii': False})

def coupon_check_view(request, name_coupon):
    # DATA_COUPON - база данных купонов: ключ - код купона (name_coupon); значение - словарь со значением скидки в процентах и
    # значением действителен ли купон или нет
    DATA_COUPON = {
        "coupon": {
            "value": 10,
            "is_valid": True},
        "coupon_old": {
            "value": 20,
            "is_valid": False},
    }
    if request.method == "GET":
        if name_coupon in DATA_COUPON.keys():
            return JsonResponse({"discount": DATA_COUPON[name_coupon]["value"], "is_valid": DATA_COUPON[name_coupon]["is_valid"]},
                                json_dumps_params={'ensure_ascii': False})
        else:
            return HttpResponseNotFound("Неверный купон")


        # TODO Проверьте, что купон есть в DATA_COUPON, если он есть, то верните JsonResponse в котором по ключу "discount"
        # получают значение скидки в процентах, а по ключу "is_valid" понимают действителен ли купон или нет (True, False)

        # TODO Если купона нет в базе, то верните HttpResponseNotFound("Неверный купон")

def delivery_estimate_view(request):
    # База данных по стоимости доставки. Ключ - Страна; Значение словарь с городами и ценами; Значение с ключом fix_price
    # применяется если нет города в данной стране
    DATA_PRICE = {
        "Россия": {
            "Москва": {"price": 80},
            "Санкт-Петербург": {"price": 80},
            "fix_price": 100,
        },
    }
    if request.method == "GET":
        data = request.GET
        country = data.get('country')
        city = data.get('city')
        if country in DATA_PRICE:
            country_info = DATA_PRICE[country]
            if city in country_info:
                return JsonResponse({"price": country_info[city]["price"]})
            return JsonResponse({"price": country_info["fix_price"]})
        return HttpResponseNotFound("Неверные данные")
        # if country in DATA_PRICE.keys() and city in DATA_PRICE.values():
        #     return JsonResponse({"price": DATA_PRICE[country][city]},
        #                     json_dumps_params={'ensure_ascii':False})
        # elif country in DATA_PRICE.keys() and city not in DATA_PRICE.values():
        #     return JsonResponse({"price": DATA_PRICE[country]["fix_price"]},
        #                         json_dumps_params={'ensure_ascii':False})
        # else:
        #     return HttpResponseNotFound("Неверные данные")


@login_required(login_url='login:login_view')
def cart_buy_now_view(request, id_product):
    if request.method == "GET":
        result = add_to_cart(request, id_product)
        if result:
            return redirect("store:cart_view")

        return HttpResponseNotFound("Неудачное добавление в корзину")


def cart_remove_view(request, id_product):
    if request.method == "GET":
        result = remove_from_cart(request, id_product) # TODO Вызвать функцию удаления из корзины
        if result:
            return redirect('store:cart_view') # TODO Вернуть перенаправление на корзину

        return HttpResponseNotFound("Неудачное удаление из корзины")