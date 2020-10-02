from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from .models import Restaurant, Users
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from asgiref.sync import sync_to_async
from django.template import RequestContext
from django.shortcuts import render

# from .scraper import scraper_function, 
from .doordash import doordash, doordash_unparsed_list, doordash_data
from .postmates import postmates, postmates_unparsed_list, postmates_data
from .ubereats import ubereats, ubereats_unparsed_list, ubereats_data
import asyncio, time
from .forms import SearchForm, RestaurantForm, FavoriteForm

# Create your views here.

# LOGIN
def login_view(request):
    if request.method == 'POST':
        # try to log the user in
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            u = form.cleaned_data['username']
            p = form.cleaned_data['password']
            user = authenticate(username = u, password = p)
            if user is not None:
                if user.is_active:
                    login(request, user) # log the user in by creating a session
                    # return HttpResponseRedirect('/')
                    return HttpResponseRedirect('/about/user/'+u+'/')
                else:
                    print('The account has been disabled.')
        else:
            print('The username and/or password is incorrect.')
    else: # it was a GET request so send the empty login form
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return HttpResponseRedirect('/user/'+str(user))
        else:
            return HttpResponse('<h1>Try Again</h1>')
    else:
        form = UserCreationForm()
        return render(request, 'signup.html', {'form': form})

#PROFILE
@login_required
def profile(request, username):
    user = User.objects.get(username=username)
    # cats = Cat.objects.filter(user=user)
    return render(request, 'profile.html', {'username': username })

# DEFAULT
def about(request):
    return render(request, 'about.html')

def index(request):
    # Checks if the request is a POST 
    if request.method == "POST":
        # Will populate our form with what the user submits
        form = SearchForm(request.POST)
        # If what the user inputs works
        if form.is_valid():
            # Gets the data in a clean format
            location = form.cleaned_data['location']
            request.session['location'] = location
            asyncio.run(scraper_function(request))
            return HttpResponseRedirect('/data/')
    form = SearchForm()
    return render(request, 'index.html', 
        {
        'form': form, 
        })

async def scraper_function(request):
    location = request.session.get('location')
    # print(location)
    task1 = asyncio.ensure_future(doordash(location))
    task2 = asyncio.ensure_future(postmates(location))
    task3 = asyncio.ensure_future(ubereats(location))
    await asyncio.wait([
        task1, task2, task3
    ])

def data(request):
    final_dd_data = []
    final_pm_data = []
    final_ue_data = []
    for dd_data in doordash_unparsed_list:
        doordash_data(dd_data)
        final_dd_data.append(doordash_data.results)

    postmates_fixed_list = list(filter(None, postmates_unparsed_list))
    for pm_data in postmates_fixed_list:
        postmates_data(pm_data)
        final_pm_data.append(postmates_data.results)

    for ue_data in ubereats_unparsed_list:
        ubereats_data(ue_data)
        final_ue_data.append(ubereats_data.results)
    print(ubereats_unparsed_list)

    if request.method == "POST":
        # Will populate our form with what the user submits
        form = RestaurantForm(request.POST)
        # If what the user inputs works
        if form.is_valid():
            # Gets the data in a clean format
            restaurant = form.cleaned_data['restaurant']
            print('hi')

    form = RestaurantForm()
    return render(request, 'data.html', {
        'doordash': final_dd_data, 
        'postmates': final_pm_data,
        'ubereats': final_ue_data,
        'forms': form,
    })

def favorites_index(request, self):
    def get_faves(self, pk):
        favorites = Restaurant.objects.get(pk=pk)
        return favorites 

        if request.method == "POST":
            print("posting on favs page") ### this works
            # # postmates = request.POST[postmates.restaurant_name]
            favorites = self.get_faves(pk=request.id)
            # print(postmates)
        return render(request, 'Favorites/favorites.html')
    
    # if request.method == "post":
    #     print("*****POST")
        # model = Restaurant
        # fields = '__all__'
        # def form_valid(self, form):
        #     self.object = form.save(commit=False)
        #     print('!!!!! SELF.OBJECT:', self.object)
        #     self.object.user = self.request.user
        #     self.object.save()
        #     return HttpResponseRedirect('/')
        # doordash = Restaurant.objects.all()
        # return render(request, 'favorites/favorites.html')
        # return HttpResponseRedirect('/favorites/')

def favorites_show(request, restaurant_id):
    doordash = Restaurant.objects.get(id=restaurant_id)
    return render(request, 'favorites/show.html', {'doordash': doordash})

###################################################
#CRUD ROUTES FOR RESTAURANT MODEL
#CREATE
class RestaurantCreate(CreateView):
    model = Restaurant
    fields = '__all__'
    # success_url = '/restaurants/'
    def form_valid(self, form):
        self.object = form.save(commit=False)
        print('!!!!! SELF.OBJECT:', self.object)
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect('/')

#UPDATE
class RestaurantUpdate(UpdateView):
    model = Restaurant
    fields = '__all__'
    # success_url = '/restaurants/'

    def form_valid(self, form): # this will allow us to catch the pk to redirect to the show page
        self.object = form.save(commit=False) # don't post to the db until we say so
        self.object.save()
        # return HttpResponseRedirect('/cats/'+str(self.object.pk))

#DELETE
class RestaurantDelete(DeleteView):
    model = Restaurant
    success_url = '/favorites'


#CRUD ROUTES FOR USER MODEL
class UsersCreate(CreateView):
    model = Users
    success_url = '/'

class UsersDelete(DeleteView):
    model = Users
    success_url = '/'

# # ####404 error page ???
# def error_404(request):
#         data = {}
#         return render(request,'404.html', data)

# def error_404_view(request, exception):
#     return render(request, 'main_app/404.html')

# def error_500_view(request, exception):
#     return render(request, 'main_app/500.html')