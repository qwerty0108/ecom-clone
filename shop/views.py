from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
import json
import razorpay
from mac.settings import RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY



client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET_KEY))

def index(request):
        
        allProds = []
        catprods = Product.objects.values('category', 'id')
        categories = {item['category'] for item in catprods}

        for cat in categories:
            prod = Product.objects.filter(category=cat)
            n = len(prod)
            nSlides = n//4 + ceil((n/4) - (n//4))

            allProds.append([prod, range(1, nSlides), nSlides])

        params = {'allProds': allProds}
        return render(request, 'shop/index.html', params)



def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    if request.method == "POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')

        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()

    return render(request, 'shop/contact.html')


def searchMatch(query, item):
    if query in item.product_name.lower() or query in item.desc.lower() or query in item.category.lower():
        return True
    return False

def search(request):

        query = request.GET.get('search')
        allProds = []
        catprods = Product.objects.values('category', 'id')
        categories = {item['category'] for item in catprods}

        for cat in categories:
            prodtemp = Product.objects.filter(category=cat)
            prod = [item for item in prodtemp if searchMatch(query, item)]
            n = len(prod)
            nSlides = n//4 + ceil((n/4) - (n//4))
            if len(prod) != 0:
                allProds.append([prod, range(1, nSlides), nSlides])

        params = {'allProds': allProds, 'msg': ""}
        if len(allProds) == 0:
            params = {'msg': "No search results found"}
        return render(request, 'shop/search.html', params)



def productView(request, myid):
    # Fetch the product using id
    
    product = Product.objects.filter(id=myid)
    return render(request, 'shop/productView.html', {'product': product[0]})



def checkout(request):
        if request.method == "POST":
            itemsJson = request.POST.get('itemsJson', '')
            name = request.POST.get('name', '')
            amount = request.POST.get('amount', '')
            email = request.POST.get('email', '')
            address = request.POST.get('address1', '')
            city = request.POST.get('city', '')
            state = request.POST.get('state', '')
            zip_code = request.POST.get('zip_code', '')
            phone = request.POST.get('phone', '')

            order = Orders(items_json=itemsJson, name=name, email=email,
                        address=address, city=city, state=state, zip_code=zip_code, phone=phone, amount=amount)
            order.save()
            update = OrderUpdate(order_id=order.order_id,
                                update_desc="The order has been placed")
            update.save()
            thank = True
            id = order.order_id
            return render(request, 'shop/checkout.html', {'thank': thank, 'id': id})

        return render(request, 'shop/checkout.html')


def tracker(request):

        if request.method == "POST":
            orderId = request.POST.get('orderId', '')
            email = request.POST.get('email', '')
            print(orderId)
            try:
                order = Orders.objects.filter(order_id=orderId, email=email)
                if len(order) > 0:
                    update = OrderUpdate.objects.filter(order_id=orderId)
                    updates = []
                    for item in update:
                        updates.append({'text': item.update_desc, 'time': item.timestamp})

                        response = json.dumps({"status":"success","updates":updates,"itemsJson": order[0].items_json}, default=str)
                    return HttpResponse(response)
                else:
                    return HttpResponse('{"status":"noitem"}')
            except:
                return HttpResponse('{"status":"noitem"}')

        return render(request, 'shop/tracker.html')


def pay(request, orderid):
    order = Orders.objects.filter(order_id=orderid)
    
    for i in order:
        order_amount = i.amount*100
        name = i.name
        phone = i.phone
        email = i.email


    order_currency = 'INR'

    payment_order = client.order.create(dict(amount=order_amount, currency=order_currency, payment_capture=1))
    payment_order_id = payment_order['id']

    context = {

        'amount': order_amount, 'api_key': RAZORPAY_API_KEY, 'order_id': payment_order_id, 'my_order_id': orderid, 'name': name, 'phone': phone, 'email': email
    }

    return render(request, 'shop/pay.html', context)
