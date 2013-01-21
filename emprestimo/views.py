# -*- coding: utf-8 -*-
#
#  Copyright (c) 2010 Wille Marcel Lima Malheiro and contributors
#
#  This file is part of VaiVem.
#
#  VaiVem is free software under terms of the GNU Affero General Public
#  License version 3 (AGPLv3) as published by the Free
#  Software Foundation. See the file README for copying conditions.
#

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
import datetime
from vaivem.emprestimo.models import Equipamento, Emprestimo, Usuario
from django.core.exceptions import ObjectDoesNotExist
import qsstats
from django.db.models import F


def index(request):
    return HttpResponseRedirect('/vaivem/admin/')


# lista os empréstimos com link para o termo de empréstimo
def emprestimosindex(request):
    emps = Emprestimo.objects.filter(devolvido=False)
    return render_to_response('comprovante-emprestimo-index.html', {'emps': emps})


# gera os termos de responsabilidade dos empréstimos
def comprovanteemprestimo(request, emprestimo_id):
    obj = Emprestimo.objects.get(id=emprestimo_id)
    data_emp = obj.data_emprestimo.strftime("%d/%m/%Y - %H:%M")
    prazo_dev = obj.prazo_devolucao.strftime("%d/%m/%Y - %H:%M")
    return render_to_response('comprovante-emprestimo.html', {'obj': obj, 'data_emp': data_emp, 'prazo_dev': prazo_dev})


# generate the loans list
# gera os relatórios de emprestimo
def relatorio(request, emprestimo_id):
    obj = Emprestimo.objects.get(id=emprestimo_id)
    data_emp = obj.data_emprestimo.strftime("%d/%m/%Y - %H:%M")
    prazo_dev = obj.prazo_devolucao.strftime("%d/%m/%Y - %H:%M")
    if obj.devolvido == True:
        data_dev = obj.data_devolucao.strftime("%d/%m/%Y - %H:%M")
    else:
        data_dev = 'Ainda não foi devolvido'
    return render_to_response('relatorio.html', {'obj': obj, 'data_emp': data_emp, 'data_dev': data_dev, 'prazo_dev': prazo_dev})


# search forms of loans
# formulário de busca de empréstimos
def search_form(request):
    return render_to_response('search_form.html')


# search results
# resultados da busca
def search(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        
        if request.GET['search_by'] == "equipamento":
            try:
                emps = Equipamento.objects.get(tombo=q).emprestimo_set.order_by('-id')
            except ObjectDoesNotExist:
                emps = []
        else:
            try:
                emps = Usuario.objects.get(matricula=q).emprestimo_set.order_by('-id')
            except ObjectDoesNotExist:
                emps = []

        if request.GET['devolvido'] == "true":
            emps = emps.filter(devolvido=True)
        elif request.GET['devolvido'] == "false":
            emps = emps.filter(devolvido=False)
            
        return render_to_response('search_results.html', {'emprestimos': emps, 'query': q})
    else:
        return render_to_response('search_form.html', {'error': True})


def stats(request):

    if 'year' in request.GET and request.GET['year']:
        year = int(request.GET['year'])

        if 'month' in request.GET and request.GET['month']:
            month = request.GET['month']
            qs = Emprestimo.objects.filter(data_emprestimo__year=year, data_emprestimo__month=month)

            results = [('Devolvidos com atraso', qs.filter(devolvido=True).filter(prazo_devolucao__lt=F('data_devolucao')).count()), ('Devolvidos no prazo', qs.filter(devolvido=True).filter(prazo_devolucao__gt=F('data_devolucao')).count()), ('Não devolvidos', qs.filter(devolvido=False).count())]

            return render_to_response('stats-by-month.html', {'year': year, 'month': month, 'results': results, 'total_month': qs.count()})

        else:
            # number of loans of a year by month
            qs = Emprestimo.objects.filter(data_emprestimo__year=year)
            qss = qsstats.QuerySetStats(qs, 'data_emprestimo')
            qss_bymonth = qss.time_series(datetime.date(year, 1,1), datetime.date(year, 12, 31), 'months')
            months = [i[0].strftime("%b") for i in qss_bymonth]
            number_loans = [i[1] for i in qss_bymonth]

            # number of loans returned without delay
            qs2 = Emprestimo.objects.filter(data_emprestimo__year=year).filter(devolvido=True).filter(prazo_devolucao__lt=F('data_devolucao'))
            qss2 = qsstats.QuerySetStats(qs2, 'data_emprestimo')
            qss2_bymonth = qss2.time_series(datetime.date(year, 1,1), datetime.date(year, 12, 31), 'months')
            no_delayed = [i[1] for i in qss2_bymonth]

            # number of loans returned with delay
            qs3 = Emprestimo.objects.filter(data_emprestimo__year=year).filter(devolvido=True).filter(prazo_devolucao__gt=F('data_devolucao'))
            qss3 = qsstats.QuerySetStats(qs3, 'data_emprestimo')
            qss3_bymonth = qss3.time_series(datetime.date(year, 1,1), datetime.date(year, 12, 31), 'months')
            delayed = [i[1] for i in qss3_bymonth]

            return render_to_response('stats-by-year.html', {'year': year, 'results': zip(months, number_loans, no_delayed, delayed), 'total_year': qs.count()})

    else:
        years = Emprestimo.objects.all().dates("data_emprestimo", "year")
        return render_to_response('stats.html', {'years': years})  

def page404(request):
    return render_to_response('404.html')


