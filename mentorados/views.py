from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404

from mentorados.auth import valida_token
from .models import Mentorados, Navigators, DisponibilidadeHorarios, Reuniao
from django.contrib import messages
from django.contrib.messages import constants
from datetime import datetime, timedelta

def mentorados(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'GET':
        navigators = Navigators.objects.filter(user=request.user)
        mentorados = Mentorados.objects.filter(user=request.user)
        
    
        estagios_flat = [i[1] for i in Mentorados.estagio_choices]
        
        qtd_estagios = []
        for i, j in Mentorados.estagio_choices:
            x = Mentorados.objects.filter(estagio=i).filter(user=request.user).count()
            qtd_estagios.append(x)
            
        print(estagios_flat)
        print(qtd_estagios)
        
        return render(request, 'mentorados.html', {'estagios': Mentorados.estagio_choices, 'navigators': navigators, 'mentorados': mentorados,
        'estagios_flat': estagios_flat, 'qtd_estagios': qtd_estagios})
        
    elif request.method == 'POST':
        nome = request.POST.get('nome')
        foto = request.FILES.get('foto')
        estagio = request.POST.get("estagio")
        navigator = request.POST.get('navigator')
        
        mentorado = Mentorados(
            nome=nome,
            foto=foto,
            estagio=estagio,
            navigator_id=navigator,
            user=request.user
        )

        mentorado.save()
        
        messages.add_message(request, constants.SUCCESS, 'Mentorado cadastrado com sucesso.')
        return redirect('mentorados')
    
def reunioes(request):
    if request.method == 'GET':
        return render(request, 'reunioes.html')
    elif request.method == 'POST':
        data = request.POST.get('data')
        data = datetime.strptime(data, '%Y-%m-%dT%H:%M')
        
        disponibilidade = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=(data - timedelta(minutes=50)),
            data_inicial__lte=(data + timedelta(minutes=50))
        )

        if disponibilidade.exists():
            messages.add_message(request, constants.ERROR, 'Você já possui uma reunião em aberto.')
            return redirect('reunioes')
        
    
        disponibilidade = DisponibilidadeHorarios(
            data_inicial=data,
            mentor=request.user

        )
        disponibilidade.save()
        
        messages.add_message(request, constants.SUCCESS, 'Horário disponibilizado com sucesso.')
        return redirect('reunioes')
   
def auth(request):
    if request.method == 'GET':
        return render(request, 'auth_mentorado.html')
    else:
        token = request.POST.get('token')

        if not Mentorados.objects.filter(token=token).exists():
            messages.add_message(request, constants.ERROR, 'Token inválido')
            return redirect('auth_mentorado')
        
        response = redirect('escolher_dia')
        response.set_cookie('auth_token', token, max_age=3600)
        return response
    
def escolher_dia(request):
    if not valida_token(request.COOKIES.get('auth_token')):
        return redirect('auth_mentorado')
    if request.method == 'GET':
        disponibilidades = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=datetime.now(),
            agendado=False
        ).values_list('data_inicial', flat=True)
        datas = []
        for i in disponibilidades:
            datas.append(i.date().strftime('%d-%m-%Y'))

        # Tornar o mês e o dia dinâmicos
        
        return render(request, 'escolher_dia.html', {'horarios': list(set(datas))})


def agendar_reuniao(request):
    if not valida_token(request.COOKIES.get('auth_token')):
        return redirect('auth_mentorado')
   
    if request.method == 'GET':
        data = request.GET.get("data")
        data = datetime.strptime(data, '%d-%m-%Y')
        mentorado = valida_token(request.COOKIES.get('auth_token'))
        
        horarios = DisponibilidadeHorarios.objects.filter(
            data_inicial__gte=data,
            data_inicial__lt=data + timedelta(days=1),
            agendado=False,
            mentor=mentorado.user
        )
        
        return render(request, 'agendar_reuniao.html', {'horarios': horarios, 'tags': Reuniao.tag_choices})