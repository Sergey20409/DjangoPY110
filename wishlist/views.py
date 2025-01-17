from django.shortcuts import render

# Create your views here.
def wishlist_view(request):
    if request.method == "GET":
        products = []
        return render(request,
                      'wishlist/wishlist.html',
                      context={"products": products})