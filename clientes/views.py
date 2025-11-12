from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from .models import Cliente


@login_required
def client_register(request):
    if request.method == 'POST':
        # Detectar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            nombre_comercial = request.POST['nombreComercial']
            cif = request.POST['cif'].strip().upper()
            telefono_oficina = request.POST['telefonoOficina']
            telefono_adicional = request.POST.get('telefonoSegundario', '')
            email = request.POST.get('email', '').lower().strip() or None
            direccion_fiscal = request.POST['direccionFiscal']
            ciudad_fiscal = request.POST['ciudadFiscal'].strip().title()
            codigo_postal_fiscal = request.POST['codigoPostalFiscal']
            direccion_entrega = request.POST.get('direccionEntrega', '')
            ciudad_entrega = request.POST.get(
                'ciudadEntrega', '').strip().title()
            codigo_postal_entrega = request.POST.get('codigoPostalEntrega')

            estado_cliente = True if request.POST.get(
                'estadoCliente') == 'on' else False

            username = request.POST.get('username')
            empleado = None
            if username:
                try:
                    empleado = User.objects.get(username=username)
                except User.DoesNotExist:
                    error_message = f"El código de empleado '{username}' no existe."
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': error_message})
                    messages.warning(request, error_message)
                    return render(request, 'clientes/clients_form.html')

            # Crear el cliente
            nuevo_cliente = Cliente.objects.create(
                nombre_comercial=nombre_comercial,
                cif=cif,
                telefono_oficina=telefono_oficina,
                telefono_adicional=telefono_adicional or None,
                email=email,
                direccion_fiscal=direccion_fiscal,
                direccion_entrega=direccion_entrega or None,
                ciudad_entrega=ciudad_entrega or None,
                codigo_postal_entrega=codigo_postal_entrega or None,
                ciudad_fiscal=ciudad_fiscal,
                codigo_postal_fiscal=codigo_postal_fiscal,
                activo=estado_cliente,
                empleado_asignado=empleado
            )

            success_message = "Cliente registrado con éxito."

            # Respuesta para AJAX
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'cliente_id': nuevo_cliente.id,
                    'cliente_nombre': nuevo_cliente.nombre_comercial,
                    'cliente_cif': nuevo_cliente.cif
                })

            # Respuesta para formulario normal
            messages.success(request, success_message)
            return redirect('listado_clientes')

        except IntegrityError:
            error_message = f"Ya existe un cliente con CIF/NIF {str(cif)}"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            return redirect('registro_cliente')

        except Exception as e:
            error_message = f"Ocurrió un error al registrar el cliente: {str(e)}"
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            print(f'El error es {type(e).__name__} {str(e)}')
            return redirect('registro_cliente')

    return render(request, 'clientes/clients_form.html')


@login_required
def list_client(request):
    query = request.GET.get('buscarCliente')
    cliente = Cliente.objects.all()

    if query:
        cliente = cliente.filter(nombre_comercial__icontains=query)

    return render(request, 'clientes/list_client.html', {"clientes": cliente, "query": query})


@login_required
def detail_client(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == "POST":
        try:
            cliente.nombre_comercial = request.POST.get(
                'nombreComercial', cliente.nombre_comercial)
            cliente.email = request.POST.get('email') or None
            cliente.telefono_oficina = request.POST.get(
                'telefonoOficina', cliente.telefono_oficina)
            cliente.telefono_adicional = request.POST.get(
                'telefonoAdicional') or None
            cliente.direccion_fiscal = request.POST.get(
                'direccionFiscal', cliente.direccion_fiscal)
            cliente.ciudad_fiscal = request.POST.get(
                'ciudadFiscal', cliente.ciudad_fiscal)
            cliente.codigo_postal_fiscal = request.POST.get(
                'codigoPostalFiscal') or cliente.codigo_postal_fiscal
            cliente.direccion_entrega = request.POST.get(
                'direccionEntrega') or None
            cliente.ciudad_entrega = request.POST.get('ciudadEntrega') or None
            cliente.codigo_postal_entrega = request.POST.get(
                'codigoPostalEntrega') or None
            cliente.cif = request.POST.get('cif', cliente.cif)

            cliente.activo = True if request.POST.get(
                'estadoCliente') == 'on' else False

            username = request.POST.get('username')
            if username:
                try:
                    empleado = User.objects.get(username=username)
                    cliente.empleado_asignado = empleado
                except User.DoesNotExist:
                    cliente.empleado_asignado = None
                    messages.warning(
                        request, f"El empleado '{username}' no existe. No se asignó ninguno.")
            else:
                cliente.empleado_asignado = None

            cliente.save()
            messages.success(
                request, f"La información del cliente {cliente.nombre_comercial} fue actualizada correctamente.")
            return redirect('listado_clientes')
        except IntegrityError:
            messages.error(
                request, f"Ya existe un cliente con CIF/NIF {str(cliente.cif)}")
            return render(request, 'clientes/detail_client.html', {"cliente": cliente})
    return render(request, 'clientes/detail_client.html', {"cliente": cliente})
