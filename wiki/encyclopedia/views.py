import random
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from markdown2 import Markdown

from . import util

class SearchForm(forms.Form):
    title = forms.CharField(label='', widget=forms.TextInput(attrs={
        "class": "search",
        "placeholder": "Пошук по Вікіпедії"
    }))

class CreateForm(forms.Form):
    title = forms.CharField(label='', required=True, widget=forms.TextInput(attrs={
        "placeholder": "Назва сторінки"
    }))
    text = forms.CharField(label='', widget=forms.Textarea(attrs={
        "placeholder": "Текст"
    }))

class EditForm(forms.Form):
    edit = forms.CharField(label='', widget=forms.Textarea(attrs={
        "placeholder": "Введіть вміст сторінки за допомогою Markdown"
    }))

def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries(),
        "search_form": SearchForm()
    })

def entry(request, title):
    entry_md = util.get_entry(title)

    if entry_md != None:
        entry_HTML = Markdown().convert(entry_md)
        return render(request, "encyclopedia/entry.html", {
            "title": title,
            "entry": entry_HTML,
            "search": SearchForm()
        })
    else:
        related_titles = util.related_titles(title)

        return render(request, "encyclopedia/error.html", {
          "title": title,
          "related_titles": related_titles,
          "search_form": SearchForm(),
        })

def search(request):
    if request.method == "POST":
        form = SearchForm(request.POST)

        # If form is valid try to search for title:
        if form.is_valid():
            title = form.cleaned_data["title"]
            entry_md = util.get_entry(title)

            print('search request: ', title)

            if entry_md:
                # If entry exists, redirect to entry view
                return redirect(reverse('entry', args=[title]))
            else:
                # Otherwise display relevant search results
                related_titles = util.related_titles(title)

                return render(request, "encyclopedia/search.html", {
                "title": title,
                "related_titles": related_titles,
                "search_form": SearchForm()
                })

    # Otherwise form not posted or form not valid, return to index page:
    return redirect(reverse('index'))

def create(request):
    """ Lets users create a new page on the wiki """

    # If reached via link, display the form:
    if request.method == "GET":
        return render(request, "encyclopedia/create.html", {
          "create_form": CreateForm(),
          "search_form": SearchForm()
        })

    # Otherwise if reached by form submission:
    elif request.method == "POST":
        form = CreateForm(request.POST)

        # If form is valid, process the form:
        if form.is_valid():
          title = form.cleaned_data['title']
          text = form.cleaned_data['text']
        else:
          messages.error(request, 'Форма запису недійсна, будь ласка спробуйте ще раз!')
          return render(request, "encyclopedia/create.html", {
            "create_form": form,
            "search_form": SearchForm()
          })

        # Check that title does not already exist:
        if util.get_entry(title):
            messages.error(request, 'Ця назва сторінки вже існує! Будь ласка, перейдіть на титульну сторінку та відредагуйте її!')
            return render(request, "encyclopedia/create.html", {
              "create_form": form,
              "search_form": SearchForm()
            })
        # Otherwise save new title file to disk, take user to new page:
        else:
            util.save_entry(title, text)
            messages.success(request, f'Нова сторінка "{title}" створена успішно!')
            return redirect(reverse('entry', args=[title]))

def edit(request, title):
    """ Lets users edit an already existing page on the wiki """

    # If reached via editing link, return form with post to edit:
    if request.method == "GET":
        text = util.get_entry(title)

        # If title does not exist, return to index with error:
        if text == None:
            messages.error(request, f'"{title}"" сторінка не інує і не може бути відредагована, будь ласка натомість створіть нову сторінку!')

        # Otherwise return pre-populated form:
        return render(request, "encyclopedia/edit.html", {
          "title": title,
          "edit_form": EditForm(initial={'text':text}),
          "search_form": SearchForm()
        })

    # If reached via posting form, updated page and redirect to page:
    elif request.method == "POST":
        form = EditForm(request.POST)

        if form.is_valid():
          text = form.cleaned_data['text']
          util.save_entry(title, text)
          messages.success(request, f'Сторінка "{title}" оновлена успішно!')
          return redirect(reverse('entry', args=[title]))

        else:
          messages.error(request, f'Форма редагування недійсна, спробуйте ще раз!')
          return render(request, "encyclopedia/edit.html", {
            "title": title,
            "edit_form": form,
            "search_form": SearchForm()
          })

def random_title(request):
    """ Takes user to a random encyclopedia entry """

    # Get list of titles, pick one at random:
    titles = util.list_entries()
    title = random.choice(titles)

    # Redirect to selected page:
    return redirect(reverse('entry', args=[title]))