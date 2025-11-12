from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Proveedor


@login_required
def supplier_register(request):
    if request.method == 'POST':
        try:
            # Obtener datos formulario
            nombre_empresa = request.POST.get('nombreEmpresa')
            cif = request.POST.get('cif', '').strip().upper()
            contacto_nombre = request.POST.get('nombreContacto')
            telefono_oficina = request.POST.get('telefonoOficina')

            # Corregir el nombre del campo para consistencia
            telefono_segundario = request.POST.get(
                'telefonoSegundario', '').strip() or None

            # Manejar campos opcionales
            email = request.POST.get('email', '').lower().strip() or None
            direccion = request.POST.get('direccionFiscal', '').strip() or None
            ciudad = request.POST.get(
                'ciudadFiscal', '').strip().title() or None
            condiciones_pago = request.POST.get(
                'condicionesPago', '').strip() or None

            # Manejar código postal - puede estar vacío
            codigo_postal_str = request.POST.get(
                'codigoPostalFiscal', '').strip()
            codigo_postal = None
            if codigo_postal_str:
                try:
                    codigo_postal = int(codigo_postal_str)
                except ValueError:
                    error_msg = 'El código postal debe ser un número válido.'

                    # Detectar si es petición AJAX
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_msg
                        })
                    else:
                        messages.error(request, error_msg)
                        return render(request, "proveedores/supplier_form.html")

            # Validar campos obligatorios
            if not all([nombre_empresa, cif, contacto_nombre, telefono_oficina]):
                error_msg = 'Todos los campos obligatorios deben ser completados.'

                # Detectar si es petición AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    return render(request, "proveedores/supplier_form.html")

            # Validar si existe proveedor
            if Proveedor.objects.filter(cif=cif).exists():
                error_msg = f'Ya existe un proveedor con este CIF: {cif}.'

                # Detectar si es petición AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    return render(request, "proveedores/supplier_form.html")

            # Crear proveedor
            nuevo_proveedor = Proveedor.objects.create(
                nombre_empresa=nombre_empresa,
                cif=cif,
                contacto_nombre=contacto_nombre,
                telefono_oficina=telefono_oficina,
                telefono_segundario=telefono_segundario,
                email=email,
                direccion=direccion,
                ciudad=ciudad,
                codigo_postal=codigo_postal,
                condiciones_pago=condiciones_pago,
            )

            success_msg = f'El proveedor {nuevo_proveedor.nombre_empresa} ha sido creado.'

            # Detectar si es petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'proveedor': {
                        'id': nuevo_proveedor.id,
                        'nombre_empresa': nuevo_proveedor.nombre_empresa,
                        'cif': nuevo_proveedor.cif,
                        'contacto_nombre': nuevo_proveedor.contacto_nombre,
                        'telefono_oficina': nuevo_proveedor.telefono_oficina,
                        'email': nuevo_proveedor.email
                    }
                })
            else:
                messages.success(request, success_msg)
                return redirect('listado_proveedor')

        except Exception as e:
            error_msg = 'Error al crear el proveedor. Por favor, verifique los datos ingresados.'

            # Detectar si es petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
            else:
                messages.error(request, error_msg)
                print(
                    f"Error al crear proveedor: {type(e).__name__} - {str(e)}")

    return render(request, "proveedores/supplier_form.html")


@login_required
def list_supplier(request):
    query = request.GET.get('buscarProveedor')
    proveedore = Proveedor.objects.all()

    if query:
        proveedore = proveedore.filter(nombre_empresa__icontains=query)

    return render(request, 'proveedores/list_supplier.html', {"proveedores": proveedore})


@login_required
def details_supplier(request, supplier_id):
    try:
        proveedor = get_object_or_404(Proveedor, id=supplier_id)
    except Proveedor.DoesNotExist:
        messages.error(request, 'El proveedor solicitado no existe.')
        return redirect('listado_proveedor')

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_empresa = request.POST.get('nombreEmpresa', '').strip()
            cif = request.POST.get('cif', '').strip().upper()
            contacto_nombre = request.POST.get('nombreContacto', '').strip()
            telefono_oficina = request.POST.get('telefonoOficina', '').strip()
            telefono_segundario = request.POST.get(
                'telefonoSegundario', '').strip() or None
            email = request.POST.get('email', '').lower().strip() or None
            direccion = request.POST.get('direccionFiscal', '').strip() or None
            ciudad = request.POST.get(
                'ciudadFiscal', '').strip().title() or None
            condiciones_pago = request.POST.get(
                'condicionesPago', '').strip() or None

            # Manejar código postal
            codigo_postal_str = request.POST.get(
                'codigoPostalFiscal', '').strip()
            codigo_postal = None
            if codigo_postal_str:
                try:
                    codigo_postal = int(codigo_postal_str)
                except ValueError:
                    messages.error(
                        request, 'El código postal debe ser un número válido.')
                    context = {'proveedor': proveedor}
                    return render(request, "proveedores/supplier_edit.html", context)

            # Validar campos obligatorios
            if not all([nombre_empresa, cif, contacto_nombre, telefono_oficina]):
                messages.error(
                    request, 'Todos los campos obligatorios deben ser completados.')
                context = {'proveedor': proveedor}
                return render(request, "proveedores/supplier_edit.html", context)

            # Validar si existe otro proveedor con el mismo CIF (excluyendo el actual)
            if Proveedor.objects.filter(cif=cif).exclude(id=supplier_id).exists():
                messages.error(
                    request, f'Ya existe otro proveedor con este CIF: {cif}.')
                context = {'proveedor': proveedor}
                return render(request, "proveedores/supplier_edit.html", context)

            # Actualizar proveedor
            proveedor.nombre_empresa = nombre_empresa
            proveedor.cif = cif
            proveedor.contacto_nombre = contacto_nombre
            proveedor.telefono_oficina = telefono_oficina
            proveedor.telefono_segundario = telefono_segundario
            proveedor.email = email
            proveedor.direccion = direccion
            proveedor.ciudad = ciudad
            proveedor.codigo_postal = codigo_postal
            proveedor.condiciones_pago = condiciones_pago

            proveedor.save()

            messages.success(
                request, f'El proveedor {proveedor.nombre_empresa} ha sido actualizado correctamente.')
            return redirect('listado_proveedor')

        except Exception as e:
            messages.error(
                request, 'Error al actualizar el proveedor. Por favor, verifique los datos ingresados.')
            print(
                f"Error al actualizar proveedor: {type(e).__name__} - {str(e)}")

    # GET request - mostrar formulario con datos actuales
    context = {
        'proveedor': proveedor
    }
    return render(request, "proveedores/supplier_edit.html", context)
